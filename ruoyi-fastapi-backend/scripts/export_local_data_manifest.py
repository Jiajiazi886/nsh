import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pymysql
from dotenv import dotenv_values

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = BACKEND_ROOT / '.env.dev'


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Create a non-secret manifest for a local database export.')
    parser.add_argument('--dump', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--user-files', type=Path, default=BACKEND_ROOT / 'vf_admin')
    parser.add_argument('--env-file', type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument('--source-commit', default='')
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = _parse_args()
    config = dotenv_values(args.env_file)
    connection = pymysql.connect(
        host=config.get('DB_HOST', '127.0.0.1'),
        port=int(config.get('DB_PORT', 3306)),
        user=config.get('DB_USERNAME', 'root'),
        password=config.get('DB_PASSWORD', ''),
        database=config.get('DB_DATABASE', 'ruoyi-fastapi'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY table_name'
            )
            table_names = [row['TABLE_NAME'] for row in cursor.fetchall()]
            table_counts = {}
            for table_name in table_names:
                cursor.execute(f'SELECT COUNT(*) AS row_count FROM `{table_name}`')
                table_counts[table_name] = cursor.fetchone()['row_count']
    finally:
        connection.close()

    user_files = [path for path in args.user_files.rglob('*') if path.is_file()] if args.user_files.exists() else []
    payload = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_commit': args.source_commit,
        'database': {
            'table_count': len(table_counts),
            'table_rows': table_counts,
            'dump_file': args.dump.name,
            'dump_bytes': args.dump.stat().st_size,
            'dump_sha256': _sha256(args.dump),
        },
        'user_files': {
            'file_count': len(user_files),
            'total_bytes': sum(path.stat().st_size for path in user_files),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'wrote data manifest to {args.output}')


if __name__ == '__main__':
    main()

"""Create a restorable logical dump of the single approved development database.

The target and output boundary are deliberately strict: this tool cannot read
or dump the legacy `ruoyi` database, and it refuses paths inside the repo.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pymysql
from dotenv import dotenv_values

TARGET = 'nsh_activity_dev_20260914'
BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target', default=TARGET)
    return parser.parse_args()


def quote(value, connection):
    if value is None:
        return 'NULL'
    if isinstance(value, (bytes, bytearray)):
        escaped = connection.escape(value)
        return "_binary'" + (escaped.decode('ascii') if isinstance(escaped, bytes) else escaped) + "'"
    escaped = connection.escape(str(value))
    return "'" + (escaped.decode('ascii') if isinstance(escaped, bytes) else escaped) + "'"


def main():
    args = parse_args()
    if args.target != TARGET:
        raise SystemExit(f'Only {TARGET} is authorized')
    output = args.output.resolve()
    if output.is_relative_to(REPO_ROOT.resolve()):
        raise SystemExit('Backup output must be outside the repository')
    output.parent.mkdir(parents=True, exist_ok=True)
    config = dotenv_values(BACKEND / '.env.dev')
    connection = pymysql.connect(
        host=config['DB_HOST'], port=int(config['DB_PORT']), user=config['DB_USERNAME'],
        password=config['DB_PASSWORD'], database=TARGET, charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor, read_timeout=60, write_timeout=60,
    )
    table_counts = {}
    try:
        with connection.cursor() as cursor, output.open('w', encoding='utf-8', errors='surrogatepass', newline='\n') as stream:
            cursor.execute('SELECT DATABASE() AS name')
            if cursor.fetchone()['name'] != TARGET:
                raise RuntimeError('Database boundary mismatch')
            stream.write('-- logical backup of nsh_activity_dev_20260914; generated locally\n')
            stream.write('SET FOREIGN_KEY_CHECKS=0;\n')
            cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME", (TARGET,))
            tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
            for table in tables:
                cursor.execute(f'SHOW CREATE TABLE `{table}`')
                create_sql = cursor.fetchone()['Create Table']
                stream.write(f'\nDROP TABLE IF EXISTS `{table}`;\n{create_sql};\n')
                cursor.execute(f'SELECT * FROM `{table}`')
                rows = cursor.fetchall()
                table_counts[table] = len(rows)
                if rows:
                    columns = list(rows[0].keys())
                    column_sql = ', '.join(f'`{column}`' for column in columns)
                    for row in rows:
                        values = ', '.join(quote(row[column], connection) for column in columns)
                        stream.write(f'INSERT INTO `{table}` ({column_sql}) VALUES ({values});\n')
            stream.write('SET FOREIGN_KEY_CHECKS=1;\n')
    finally:
        connection.close()
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    manifest = output.with_suffix(output.suffix + '.manifest.json')
    manifest.write_text(json.dumps({'database': TARGET, 'tableCount': len(table_counts), 'tableRows': table_counts, 'dumpBytes': output.stat().st_size, 'sha256': digest}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'database': TARGET, 'tableCount': len(table_counts), 'dumpBytes': output.stat().st_size, 'sha256': digest, 'manifest': str(manifest)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

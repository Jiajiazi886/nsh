import argparse
import json
from pathlib import Path

import pymysql
from dotenv import dotenv_values

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = BACKEND_ROOT / '.env.dev'
DEFAULT_OUTPUT = BACKEND_ROOT / 'config' / 'project_menu_baseline.json'
MENU_FIELDS = (
    'menu_id',
    'menu_name',
    'parent_id',
    'order_num',
    'path',
    'component',
    'query',
    'route_name',
    'is_frame',
    'is_cache',
    'menu_type',
    'visible',
    'status',
    'perms',
    'icon',
    'remark',
)
BUILTIN_ROLE_IDS = (1, 2, 100)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Export the canonical project menu and role-menu baseline.')
    parser.add_argument('--env-file', type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


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
            cursor.execute(f'SELECT {", ".join(MENU_FIELDS)} FROM sys_menu ORDER BY menu_id')
            menus = cursor.fetchall()
            placeholders = ', '.join(['%s'] * len(BUILTIN_ROLE_IDS))
            cursor.execute(
                f'SELECT role_id, menu_id FROM sys_role_menu '
                f'WHERE role_id IN ({placeholders}) ORDER BY role_id, menu_id',
                BUILTIN_ROLE_IDS,
            )
            role_menu_rows = cursor.fetchall()
    finally:
        connection.close()

    role_menus = {str(role_id): [] for role_id in BUILTIN_ROLE_IDS}
    for row in role_menu_rows:
        role_menus[str(row['role_id'])].append(row['menu_id'])

    payload = {
        'baseline_version': '20260813_local_parity_menu_baseline',
        'menus': menus,
        'role_menus': role_menus,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f'exported {len(menus)} menus and {len(role_menu_rows)} role-menu rows to {args.output}')


if __name__ == '__main__':
    main()

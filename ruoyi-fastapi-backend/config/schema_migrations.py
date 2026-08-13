import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from config.env import DataBaseConfig
from utils.log_util import logger

BASELINE_PATH = Path(__file__).with_name('project_menu_baseline.json')
LEGACY_MENU_IDS = (4, 99, 118, 119, 1061, 1062, 1063, 1064)
BUILTIN_ROLE_IDS = (1, 2, 100)
DEFENSE_CALCULATOR_RENAME_VERSION = '20260813_rename_defense_calculator'
MENU_COLUMNS = (
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


@lru_cache(maxsize=1)
def load_project_menu_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding='utf-8'))


def _migration_table_sql() -> str:
    if DataBaseConfig.db_type == 'postgresql':
        return """
        CREATE TABLE IF NOT EXISTS app_schema_migration (
          version varchar(128) PRIMARY KEY,
          description varchar(255) NOT NULL DEFAULT '',
          applied_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    return """
    CREATE TABLE IF NOT EXISTS app_schema_migration (
      version varchar(128) NOT NULL,
      description varchar(255) NOT NULL DEFAULT '',
      applied_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (version)
    ) ENGINE=InnoDB COMMENT='应用数据库迁移记录'
    """


def _menu_upsert_sql() -> str:
    columns = ', '.join(f'`{column}`' for column in MENU_COLUMNS)
    values = ', '.join(f':{column}' for column in MENU_COLUMNS)
    mutable_columns = [column for column in MENU_COLUMNS if column != 'menu_id']
    if DataBaseConfig.db_type == 'postgresql':
        columns = ', '.join(f'"{column}"' for column in MENU_COLUMNS)
        updates = ', '.join(f'"{column}" = EXCLUDED."{column}"' for column in mutable_columns)
        return f'INSERT INTO sys_menu ({columns}) VALUES ({values}) ON CONFLICT (menu_id) DO UPDATE SET {updates}'
    updates = ', '.join(f'`{column}` = VALUES(`{column}`)' for column in mutable_columns)
    return f'INSERT INTO sys_menu ({columns}) VALUES ({values}) ON DUPLICATE KEY UPDATE {updates}'


async def _apply_local_parity_menu_baseline(conn: AsyncConnection, baseline: dict) -> None:
    legacy_params = {f'legacy_{index}': menu_id for index, menu_id in enumerate(LEGACY_MENU_IDS)}
    legacy_slots = ', '.join(f':legacy_{index}' for index in range(len(LEGACY_MENU_IDS)))
    await conn.execute(text(f'DELETE FROM sys_role_menu WHERE menu_id IN ({legacy_slots})'), legacy_params)
    await conn.execute(text(f'DELETE FROM sys_menu WHERE menu_id IN ({legacy_slots})'), legacy_params)

    await conn.execute(text(_menu_upsert_sql()), baseline['menus'])
    if DataBaseConfig.db_type == 'postgresql':
        await conn.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('sys_menu', 'menu_id'), "
                'GREATEST((SELECT COALESCE(MAX(menu_id), 1) FROM sys_menu), 1), true)'
            )
        )

    role_params = {f'role_{index}': role_id for index, role_id in enumerate(BUILTIN_ROLE_IDS)}
    role_slots = ', '.join(f':role_{index}' for index in range(len(BUILTIN_ROLE_IDS)))
    await conn.execute(text(f'DELETE FROM sys_role_menu WHERE role_id IN ({role_slots})'), role_params)
    role_menu_rows = [
        {'role_id': int(role_id), 'menu_id': menu_id}
        for role_id, menu_ids in baseline['role_menus'].items()
        for menu_id in menu_ids
    ]
    if role_menu_rows:
        await conn.execute(
            text('INSERT INTO sys_role_menu (role_id, menu_id) VALUES (:role_id, :menu_id)'),
            role_menu_rows,
        )


async def run_schema_migrations(conn: AsyncConnection) -> None:
    """Run project data migrations once and keep later administrator permission edits intact."""
    await conn.execute(text(_migration_table_sql()))
    baseline = load_project_menu_baseline()
    version = baseline['baseline_version']
    already_applied = await conn.scalar(
        text('SELECT 1 FROM app_schema_migration WHERE version = :version'),
        {'version': version},
    )
    if not already_applied:
        await _apply_local_parity_menu_baseline(conn, baseline)
        await conn.execute(
            text('INSERT INTO app_schema_migration (version, description) VALUES (:version, :description)'),
            {'version': version, 'description': 'Align menus and built-in role permissions with the project baseline'},
        )
        # MySQL DDL commits implicitly. Record the completed data migration before dropping the obsolete table.
        await conn.execute(text('DROP TABLE IF EXISTS ai_chat_config'))
        logger.info(f'已应用数据库迁移：{version}')

    rename_applied = await conn.scalar(
        text('SELECT 1 FROM app_schema_migration WHERE version = :version'),
        {'version': DEFENSE_CALCULATOR_RENAME_VERSION},
    )
    if not rename_applied:
        await conn.execute(
            text(
                "UPDATE sys_menu SET menu_name = :menu_name, remark = :remark "
                "WHERE menu_id = :menu_id"
            ),
            {'menu_id': 3005, 'menu_name': '坦度计算器', 'remark': '坦度计算器菜单'},
        )
        await conn.execute(
            text('INSERT INTO app_schema_migration (version, description) VALUES (:version, :description)'),
            {
                'version': DEFENSE_CALCULATOR_RENAME_VERSION,
                'description': 'Rename the personal defense calculator menu without resetting role permissions',
            },
        )
        logger.info(f'已应用数据库迁移：{DEFENSE_CALCULATOR_RENAME_VERSION}')

import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from config.env import DataBaseConfig
from utils.log_util import logger

BASELINE_PATH = Path(__file__).with_name('project_menu_baseline.json')
LEGACY_MENU_IDS = (
    4, 99, 118, 119, 1061, 1062, 1063, 1064, 1068, 1069, 1070, 1071, 1072,
    1073, 1074, 1075, 2000, 2001,
)
BUILTIN_ROLE_IDS = (1, 2, 100)
DEFENSE_CALCULATOR_RENAME_VERSION = '20260813_rename_defense_calculator'
SUPER_ADMIN_ROLE_KEY_VERSION = '20260919_super_admin_role_key_cptbtptp'
ACCOUNT_LICENSE_SCHEMA_VERSION = '20260919_account_license_schema'
ACCOUNT_LICENSE_MENU_VERSION = '20260919_account_license_menu'
AUTH_REFRESH_TOKEN_SCHEMA_VERSION = '20260919_auth_refresh_token_schema'
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


def _account_license_schema_sql() -> list[str]:
    if DataBaseConfig.db_type == 'postgresql':
        return [
            """
            CREATE TABLE IF NOT EXISTS system_account_license (
              license_id varchar(64) PRIMARY KEY,
              user_id bigint NOT NULL UNIQUE REFERENCES sys_user(user_id),
              plan_type varchar(16) NOT NULL,
              status varchar(16) NOT NULL DEFAULT 'active',
              valid_from timestamp NOT NULL,
              expires_at timestamp NULL,
              remark varchar(500) NOT NULL DEFAULT '',
              version integer NOT NULL DEFAULT 1,
              create_by varchar(64) NOT NULL DEFAULT 'system',
              create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
              update_by varchar(64) NOT NULL DEFAULT 'system',
              update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            'CREATE INDEX IF NOT EXISTS ix_system_account_license_user ON system_account_license(user_id)',
            """
            CREATE TABLE IF NOT EXISTS system_account_license_audit (
              audit_id varchar(64) PRIMARY KEY,
              batch_id varchar(64) NOT NULL,
              request_id varchar(64) NOT NULL,
              user_id bigint NOT NULL REFERENCES sys_user(user_id),
              operator_user_id bigint NOT NULL REFERENCES sys_user(user_id),
              action varchar(32) NOT NULL,
              previous_state jsonb NULL,
              new_state jsonb NULL,
              remark varchar(500) NOT NULL DEFAULT '',
              created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(request_id, user_id)
            )
            """,
            'CREATE INDEX IF NOT EXISTS ix_system_account_license_audit_batch ON system_account_license_audit(batch_id)',
            'CREATE INDEX IF NOT EXISTS ix_system_account_license_audit_user ON system_account_license_audit(user_id)',
        ]
    return [
        """
        CREATE TABLE IF NOT EXISTS system_account_license (
          license_id varchar(64) NOT NULL,
          user_id bigint NOT NULL,
          plan_type varchar(16) NOT NULL,
          status varchar(16) NOT NULL DEFAULT 'active',
          valid_from datetime NOT NULL,
          expires_at datetime NULL,
          remark varchar(500) NOT NULL DEFAULT '',
          version int NOT NULL DEFAULT 1,
          create_by varchar(64) NOT NULL DEFAULT 'system',
          create_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          update_by varchar(64) NOT NULL DEFAULT 'system',
          update_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (license_id),
          UNIQUE KEY uk_system_account_license_user (user_id),
          KEY ix_system_account_license_user (user_id),
          CONSTRAINT fk_system_account_license_user FOREIGN KEY (user_id) REFERENCES sys_user(user_id)
        ) ENGINE=InnoDB COMMENT='账号授权'
        """,
        """
        CREATE TABLE IF NOT EXISTS system_account_license_audit (
          audit_id varchar(64) NOT NULL,
          batch_id varchar(64) NOT NULL,
          request_id varchar(64) NOT NULL,
          user_id bigint NOT NULL,
          operator_user_id bigint NOT NULL,
          action varchar(32) NOT NULL,
          previous_state json NULL,
          new_state json NULL,
          remark varchar(500) NOT NULL DEFAULT '',
          created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (audit_id),
          UNIQUE KEY uk_system_account_license_audit_request_user (request_id, user_id),
          KEY ix_system_account_license_audit_batch (batch_id),
          KEY ix_system_account_license_audit_user (user_id),
          CONSTRAINT fk_system_account_license_audit_user FOREIGN KEY (user_id) REFERENCES sys_user(user_id),
          CONSTRAINT fk_system_account_license_audit_operator FOREIGN KEY (operator_user_id) REFERENCES sys_user(user_id)
        ) ENGINE=InnoDB COMMENT='账号授权审计'
        """,
    ]


def _auth_refresh_token_schema_sql() -> list[str]:
    if DataBaseConfig.db_type == 'postgresql':
        return [
            """
            CREATE TABLE IF NOT EXISTS system_auth_refresh_token (
              token_id varchar(64) PRIMARY KEY,
              token_hash varchar(64) NOT NULL UNIQUE,
              user_id bigint NOT NULL REFERENCES sys_user(user_id),
              client_type varchar(40) NOT NULL DEFAULT '',
              token_family_id varchar(64) NOT NULL,
              device_id varchar(128) NULL,
              issued_at timestamp NOT NULL,
              expires_at timestamp NOT NULL,
              last_used_at timestamp NULL,
              revoked_at timestamp NULL,
              replaced_by_token_id varchar(64) NULL
            )
            """,
            'CREATE INDEX IF NOT EXISTS ix_system_auth_refresh_token_user ON system_auth_refresh_token(user_id)',
            'CREATE INDEX IF NOT EXISTS ix_system_auth_refresh_token_family ON system_auth_refresh_token(token_family_id)',
            'CREATE INDEX IF NOT EXISTS ix_system_auth_refresh_token_device ON system_auth_refresh_token(device_id)',
        ]
    return [
        """
        CREATE TABLE IF NOT EXISTS system_auth_refresh_token (
          token_id varchar(64) NOT NULL,
          token_hash varchar(64) NOT NULL,
          user_id bigint NOT NULL,
          client_type varchar(40) NOT NULL DEFAULT '',
          token_family_id varchar(64) NOT NULL,
          device_id varchar(128) NULL,
          issued_at datetime NOT NULL,
          expires_at datetime NOT NULL,
          last_used_at datetime NULL,
          revoked_at datetime NULL,
          replaced_by_token_id varchar(64) NULL,
          PRIMARY KEY (token_id),
          UNIQUE KEY uk_system_auth_refresh_token_hash (token_hash),
          KEY ix_system_auth_refresh_token_user (user_id),
          KEY ix_system_auth_refresh_token_family (token_family_id),
          KEY ix_system_auth_refresh_token_device (device_id),
          CONSTRAINT fk_system_auth_refresh_token_user FOREIGN KEY (user_id) REFERENCES sys_user(user_id)
        ) ENGINE=InnoDB COMMENT='持久化刷新令牌'
        """,
    ]


def _license_menu_rows() -> list[dict]:
    base = {
        'query': '', 'route_name': '', 'is_frame': 1, 'is_cache': 0,
        'visible': '0', 'status': '0', 'icon': '#', 'remark': '',
    }
    return [
        base | {
            'menu_id': 3170, 'menu_name': '卡密管理', 'parent_id': 1, 'order_num': 16,
            'path': 'license', 'component': 'system/license/index', 'menu_type': 'C',
            'perms': 'system:license:list', 'icon': 'lock', 'remark': 'RuoYi账号授权管理',
        },
        base | {'menu_id': 3171, 'menu_name': '授权查询', 'parent_id': 3170, 'order_num': 1, 'path': '#', 'component': '', 'menu_type': 'F', 'perms': 'system:license:list'},
        base | {'menu_id': 3172, 'menu_name': '发放授权', 'parent_id': 3170, 'order_num': 2, 'path': '#', 'component': '', 'menu_type': 'F', 'perms': 'system:license:grant'},
        base | {'menu_id': 3173, 'menu_name': '撤销授权', 'parent_id': 3170, 'order_num': 3, 'path': '#', 'component': '', 'menu_type': 'F', 'perms': 'system:license:revoke'},
        base | {'menu_id': 3174, 'menu_name': '修改备注', 'parent_id': 3170, 'order_num': 4, 'path': '#', 'component': '', 'menu_type': 'F', 'perms': 'system:license:remark'},
        base | {'menu_id': 3175, 'menu_name': '授权审计', 'parent_id': 3170, 'order_num': 5, 'path': '#', 'component': '', 'menu_type': 'F', 'perms': 'system:license:audit'},
    ]


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

    role_key_applied = await conn.scalar(
        text('SELECT 1 FROM app_schema_migration WHERE version = :version'),
        {'version': SUPER_ADMIN_ROLE_KEY_VERSION},
    )
    if not role_key_applied:
        duplicate_key = await conn.scalar(
            text(
                'SELECT 1 FROM sys_role '
                'WHERE role_key = :role_key AND role_id <> :role_id LIMIT 1'
            ),
            {'role_key': 'cptbtptp', 'role_id': 1},
        )
        if duplicate_key:
            raise RuntimeError('无法迁移超级管理员权限字符：cptbtptp 已被其他角色占用')
        role_exists = await conn.scalar(
            text('SELECT 1 FROM sys_role WHERE role_id = :role_id LIMIT 1'),
            {'role_id': 1},
        )
        if not role_exists:
            raise RuntimeError('无法迁移超级管理员权限字符：role_id=1 不存在')
        await conn.execute(
            text(
                'UPDATE sys_role SET role_key = :new_key, update_by = :update_by '
                'WHERE role_id = :role_id AND role_key <> :new_key'
            ),
            {'new_key': 'cptbtptp', 'update_by': 'system', 'role_id': 1},
        )
        await conn.execute(
            text('INSERT INTO app_schema_migration (version, description) VALUES (:version, :description)'),
            {
                'version': SUPER_ADMIN_ROLE_KEY_VERSION,
                'description': 'Rename built-in super administrator role key to cptbtptp',
            },
        )
        logger.info(f'已应用数据库迁移：{SUPER_ADMIN_ROLE_KEY_VERSION}')

    license_schema_applied = await conn.scalar(
        text('SELECT 1 FROM app_schema_migration WHERE version = :version'),
        {'version': ACCOUNT_LICENSE_SCHEMA_VERSION},
    )
    if not license_schema_applied:
        for statement in _account_license_schema_sql():
            await conn.execute(text(statement))
        await conn.execute(
            text('INSERT INTO app_schema_migration (version, description) VALUES (:version, :description)'),
            {
                'version': ACCOUNT_LICENSE_SCHEMA_VERSION,
                'description': 'Create account entitlement and audit tables',
            },
        )
        logger.info(f'已应用数据库迁移：{ACCOUNT_LICENSE_SCHEMA_VERSION}')

    license_menu_applied = await conn.scalar(
        text('SELECT 1 FROM app_schema_migration WHERE version = :version'),
        {'version': ACCOUNT_LICENSE_MENU_VERSION},
    )
    if not license_menu_applied:
        license_menus = _license_menu_rows()
        await conn.execute(text(_menu_upsert_sql()), license_menus)
        role_menu_sql = (
            'INSERT INTO sys_role_menu (role_id, menu_id) VALUES (:role_id, :menu_id) '
            'ON CONFLICT (role_id, menu_id) DO NOTHING'
            if DataBaseConfig.db_type == 'postgresql'
            else 'INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (:role_id, :menu_id)'
        )
        await conn.execute(
            text(role_menu_sql),
            [{'role_id': 1, 'menu_id': row['menu_id']} for row in license_menus],
        )
        await conn.execute(
            text('INSERT INTO app_schema_migration (version, description) VALUES (:version, :description)'),
            {
                'version': ACCOUNT_LICENSE_MENU_VERSION,
                'description': 'Add account entitlement management menu and permissions',
            },
        )
        logger.info(f'已应用数据库迁移：{ACCOUNT_LICENSE_MENU_VERSION}')

    refresh_token_applied = await conn.scalar(
        text('SELECT 1 FROM app_schema_migration WHERE version = :version'),
        {'version': AUTH_REFRESH_TOKEN_SCHEMA_VERSION},
    )
    if not refresh_token_applied:
        for statement in _auth_refresh_token_schema_sql():
            await conn.execute(text(statement))
        await conn.execute(
            text('INSERT INTO app_schema_migration (version, description) VALUES (:version, :description)'),
            {
                'version': AUTH_REFRESH_TOKEN_SCHEMA_VERSION,
                'description': 'Create persistent rotating refresh-token storage',
            },
        )
        logger.info(f'已应用数据库迁移：{AUTH_REFRESH_TOKEN_SCHEMA_VERSION}')

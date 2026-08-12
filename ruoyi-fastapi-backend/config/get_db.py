from collections.abc import AsyncGenerator

from sqlalchemy import Connection, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal, Base, async_engine
from config.env import DataBaseConfig
from config.schema_migrations import run_schema_migrations
from utils.log_util import logger

INTERNAL_POWER_ENTRY_TABLE = 'system_internal_power_entry'
SYSTEM_INTERNAL_POWER_PRESET_TABLE = 'system_internal_power_preset'
PERSONAL_INTERNAL_POWER_TABLE = 'personal_internal_power'
SYS_USER_TABLE = 'sys_user'
DAMAGE_FORMULA_VERSION_TABLE = 'system_damage_formula_version'
SYSTEM_INTERNAL_POWER_PANEL_TEMPLATE_TABLE = 'system_internal_power_panel_template'
PERSONAL_INTERNAL_POWER_PANEL_RECOGNITION_HISTORY_TABLE = 'personal_internal_power_panel_recognition_history'
SYSTEM_ROLE_SQL = {
    'mysql': """
    INSERT INTO sys_role (
      role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly,
      status, del_flag, create_by, create_time, update_by, update_time, remark
    ) VALUES
      (1, '超级管理员', 'admin', 1, '1', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置超级管理员角色'),
      (2, '帮会管理', 'common', 2, '2', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置帮会管理角色'),
      (100, '帮会成员', 'user', 0, '2', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置帮会成员角色')
    ON DUPLICATE KEY UPDATE
      role_name = VALUES(role_name), role_key = VALUES(role_key), role_sort = VALUES(role_sort),
      status = '0', del_flag = '0', update_by = 'system', update_time = NOW(), remark = VALUES(remark)
    """,
    'postgresql': """
    INSERT INTO sys_role (
      role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly,
      status, del_flag, create_by, create_time, update_by, update_time, remark
    ) VALUES
      (1, '超级管理员', 'admin', 1, '1', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置超级管理员角色'),
      (2, '帮会管理', 'common', 2, '2', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置帮会管理角色'),
      (100, '帮会成员', 'user', 0, '2', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置帮会成员角色')
    ON CONFLICT (role_id) DO UPDATE SET
      role_name = EXCLUDED.role_name, role_key = EXCLUDED.role_key, role_sort = EXCLUDED.role_sort,
      status = '0', del_flag = '0', update_by = 'system', update_time = NOW(), remark = EXCLUDED.remark
    """,
}
INTERNAL_POWER_ENTRY_LIMIT_COLUMN_SQL = {
    'mysql': {
        'limit_text': (
            "ALTER TABLE system_internal_power_entry "
            "ADD COLUMN limit_text varchar(32) DEFAULT '' COMMENT '固定上限展示值' AFTER conversion_desc"
        ),
        'limit_value': (
            "ALTER TABLE system_internal_power_entry "
            "ADD COLUMN limit_value double DEFAULT NULL COMMENT '固定上限数值' AFTER limit_text"
        ),
        'value_type': (
            "ALTER TABLE system_internal_power_entry "
            "ADD COLUMN value_type varchar(16) NOT NULL DEFAULT 'number' "
            "COMMENT '数值类型（number数值 percent百分比）' AFTER limit_value"
        ),
    },
    'postgresql': {
        'limit_text': "ALTER TABLE system_internal_power_entry ADD COLUMN limit_text varchar(32) DEFAULT ''",
        'limit_value': 'ALTER TABLE system_internal_power_entry ADD COLUMN limit_value double precision DEFAULT NULL',
        'value_type': (
            "ALTER TABLE system_internal_power_entry ADD COLUMN value_type varchar(16) NOT NULL DEFAULT 'number'"
        ),
    },
}

INTERNAL_POWER_LINGYUN_COLUMN_SQL = {
    'mysql': {
        SYSTEM_INTERNAL_POWER_PRESET_TABLE: {
            'lingyun_bonus_percent': (
                "ALTER TABLE system_internal_power_preset "
                "ADD COLUMN lingyun_bonus_percent double NOT NULL DEFAULT 0 COMMENT '灵韵百分比提升' AFTER bonus_percent"
            ),
        },
        PERSONAL_INTERNAL_POWER_TABLE: {
            'lingyun_enabled': (
                "ALTER TABLE personal_internal_power "
                "ADD COLUMN lingyun_enabled char(1) NOT NULL DEFAULT '0' COMMENT '是否启用灵韵（0否 1是）' "
                "AFTER bonus_percent"
            ),
            'lingyun_bonus_percent': (
                "ALTER TABLE personal_internal_power "
                "ADD COLUMN lingyun_bonus_percent double NOT NULL DEFAULT 0 COMMENT '灵韵百分比提升' "
                "AFTER lingyun_enabled"
            ),
        },
    },
    'postgresql': {
        SYSTEM_INTERNAL_POWER_PRESET_TABLE: {
            'lingyun_bonus_percent': (
                'ALTER TABLE system_internal_power_preset ADD COLUMN lingyun_bonus_percent double precision NOT NULL DEFAULT 0'
            ),
        },
        PERSONAL_INTERNAL_POWER_TABLE: {
            'lingyun_enabled': (
                "ALTER TABLE personal_internal_power ADD COLUMN lingyun_enabled char(1) NOT NULL DEFAULT '0'"
            ),
            'lingyun_bonus_percent': (
                'ALTER TABLE personal_internal_power ADD COLUMN lingyun_bonus_percent double precision NOT NULL DEFAULT 0'
            ),
        },
    },
}

SYS_USER_VIP_SPONSOR_COLUMN_SQL = {
    'mysql': {
        'vip_ai_image_recognition_count': (
            "ALTER TABLE sys_user ADD COLUMN vip_ai_image_recognition_count int NOT NULL DEFAULT 0 "
            "COMMENT 'VIP AI识图剩余次数' AFTER ai_image_recognition_count"
        ),
        'sponsor_enabled': (
            "ALTER TABLE sys_user ADD COLUMN sponsor_enabled char(1) NOT NULL DEFAULT '0' "
            "COMMENT '赞助开关（0关闭 1开启）' AFTER vip_ai_image_recognition_count"
        ),
        'sponsored_vip': (
            "ALTER TABLE sys_user ADD COLUMN sponsored_vip char(1) NOT NULL DEFAULT '0' "
            "COMMENT '赞助VIP标识（0非VIP 1VIP）' AFTER sponsor_enabled"
        ),
        'sponsored_by_user_id': (
            "ALTER TABLE sys_user ADD COLUMN sponsored_by_user_id bigint NULL "
            "COMMENT '赞助来源帮会管理用户ID' AFTER sponsored_vip"
        ),
    },
    'postgresql': {
        'vip_ai_image_recognition_count': (
            'ALTER TABLE sys_user ADD COLUMN vip_ai_image_recognition_count integer NOT NULL DEFAULT 0'
        ),
        'sponsor_enabled': "ALTER TABLE sys_user ADD COLUMN sponsor_enabled char(1) NOT NULL DEFAULT '0'",
        'sponsored_vip': "ALTER TABLE sys_user ADD COLUMN sponsored_vip char(1) NOT NULL DEFAULT '0'",
        'sponsored_by_user_id': 'ALTER TABLE sys_user ADD COLUMN sponsored_by_user_id bigint NULL',
    },
}

DEFAULT_AI_RECOGNITION_CONFIG_SQL = {
    'mysql': """
    INSERT INTO sys_config (
      config_name, config_key, config_value, config_type,
      create_by, create_time, update_by, update_time, remark
    )
    SELECT '用户管理-新用户默认普通AI识图次数', 'sys.user.defaultAiImageRecognitionCount', '0', 'Y',
           'system', NOW(), 'system', NOW(), '后台新增、注册和导入新增用户时默认发放的普通AI识图次数'
    FROM DUAL
    WHERE NOT EXISTS (
      SELECT 1 FROM sys_config WHERE config_key = 'sys.user.defaultAiImageRecognitionCount'
    )
    """,
    'postgresql': """
    INSERT INTO sys_config (
      config_name, config_key, config_value, config_type,
      create_by, create_time, update_by, update_time, remark
    )
    SELECT '用户管理-新用户默认普通AI识图次数', 'sys.user.defaultAiImageRecognitionCount', '0', 'Y',
           'system', NOW(), 'system', NOW(), '后台新增、注册和导入新增用户时默认发放的普通AI识图次数'
    WHERE NOT EXISTS (
      SELECT 1 FROM sys_config WHERE config_key = 'sys.user.defaultAiImageRecognitionCount'
    )
    """,
}

DAMAGE_FORMULA_VERSION_COLUMN_SQL = {
    'mysql': {
        'formula_package_json': (
            "ALTER TABLE system_damage_formula_version "
            "MODIFY COLUMN formula_package_json LONGTEXT NOT NULL COMMENT '公式包JSON'"
        ),
    },
    'postgresql': {},
}

INTERNAL_POWER_ENTRY_LIMIT_BACKFILL_SQL = """
UPDATE system_internal_power_entry
SET
  limit_text = CASE entry_name
    WHEN '攻击' THEN '33'
    WHEN '力量/气海' THEN '10'
    WHEN '赛年伤害/治疗提高' THEN '1.7%'
    WHEN '最小攻击' THEN '36'
    WHEN '最大攻击' THEN '36'
    WHEN '流派克制' THEN '1.2%'
    WHEN '破防' THEN '33'
    WHEN '会心' THEN '66'
    WHEN '耐力' THEN '10'
    WHEN '根骨' THEN '10'
    WHEN '身法' THEN '10'
    WHEN '内功防御' THEN '36'
    WHEN '首领抵御' THEN '1.2%'
    WHEN '流派抵御' THEN '1.2%'
    WHEN '抗会心' THEN '66'
    WHEN '防御' THEN '33'
    WHEN '气血上限' THEN '991'
    WHEN '首领克制' THEN '1.2%'
    WHEN '抗内功会心' THEN '72'
    WHEN '抗外功会心' THEN '72'
    WHEN '外功防御' THEN '36'
    ELSE limit_text
  END,
  limit_value = CASE entry_name
    WHEN '攻击' THEN 33
    WHEN '力量/气海' THEN 10
    WHEN '赛年伤害/治疗提高' THEN 1.7
    WHEN '最小攻击' THEN 36
    WHEN '最大攻击' THEN 36
    WHEN '流派克制' THEN 1.2
    WHEN '破防' THEN 33
    WHEN '会心' THEN 66
    WHEN '耐力' THEN 10
    WHEN '根骨' THEN 10
    WHEN '身法' THEN 10
    WHEN '内功防御' THEN 36
    WHEN '首领抵御' THEN 1.2
    WHEN '流派抵御' THEN 1.2
    WHEN '抗会心' THEN 66
    WHEN '防御' THEN 33
    WHEN '气血上限' THEN 991
    WHEN '首领克制' THEN 1.2
    WHEN '抗内功会心' THEN 72
    WHEN '抗外功会心' THEN 72
    WHEN '外功防御' THEN 36
    ELSE limit_value
  END,
  value_type = CASE entry_name
    WHEN '赛年伤害/治疗提高' THEN 'percent'
    WHEN '流派克制' THEN 'percent'
    WHEN '首领抵御' THEN 'percent'
    WHEN '流派抵御' THEN 'percent'
    WHEN '首领克制' THEN 'percent'
    ELSE value_type
  END,
  update_time = NOW()
WHERE (limit_value IS NULL OR limit_text IS NULL OR limit_text = '')
  AND entry_name IN (
    '攻击', '力量/气海', '赛年伤害/治疗提高', '最小攻击', '最大攻击', '流派克制',
    '破防', '会心', '耐力', '根骨', '身法', '内功防御', '首领抵御', '流派抵御',
    '抗会心', '防御', '气血上限', '首领克制', '抗内功会心', '抗外功会心', '外功防御'
  )
"""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接

    :return:
    """
    async with AsyncSessionLocal() as current_db:
        yield current_db


def _get_table_columns(sync_conn: Connection, table_name: str) -> set[str]:
    inspector = inspect(sync_conn)
    if not inspector.has_table(table_name):
        return set()
    return {column['name'] for column in inspector.get_columns(table_name)}


def _get_table_column_info(sync_conn: Connection, table_name: str, column_name: str) -> dict | None:
    inspector = inspect(sync_conn)
    if not inspector.has_table(table_name):
        return None
    for column in inspector.get_columns(table_name):
        if column['name'] == column_name:
            return column
    return None


async def ensure_internal_power_entry_limit_columns() -> None:
    """
    补齐系统内功词条上限字段。

    Base.metadata.create_all 只会创建缺失表，不会给已有表追加字段；这里用于兼容已部署库升级。
    """
    async with async_engine.begin() as conn:
        existing_columns = await conn.run_sync(_get_table_columns, INTERNAL_POWER_ENTRY_TABLE)
        if not existing_columns:
            return

        ddl_map = INTERNAL_POWER_ENTRY_LIMIT_COLUMN_SQL.get(DataBaseConfig.db_type)
        if not ddl_map:
            return

        for column_name, ddl in ddl_map.items():
            if column_name not in existing_columns:
                await conn.execute(text(ddl))
                logger.info(f'已补齐{INTERNAL_POWER_ENTRY_TABLE}.{column_name}字段')

        await conn.execute(text(INTERNAL_POWER_ENTRY_LIMIT_BACKFILL_SQL))


async def ensure_system_roles() -> None:
    """补齐并保护项目内置的三种系统角色，不改写管理员配置的菜单权限。"""
    sql = SYSTEM_ROLE_SQL.get(DataBaseConfig.db_type)
    if not sql:
        return
    async with async_engine.begin() as conn:
        await conn.execute(text(sql))
        if DataBaseConfig.db_type == 'postgresql':
            await conn.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('sys_role', 'role_id'), "
                    "GREATEST((SELECT COALESCE(MAX(role_id), 100) FROM sys_role), 100), true)"
                )
            )


async def ensure_internal_power_lingyun_columns() -> None:
    """
    补齐内功灵韵字段，兼容已部署库升级。
    """
    ddl_by_table = INTERNAL_POWER_LINGYUN_COLUMN_SQL.get(DataBaseConfig.db_type)
    if not ddl_by_table:
        return

    async with async_engine.begin() as conn:
        for table_name, ddl_map in ddl_by_table.items():
            existing_columns = await conn.run_sync(_get_table_columns, table_name)
            if not existing_columns:
                continue
            for column_name, ddl in ddl_map.items():
                if column_name not in existing_columns:
                    await conn.execute(text(ddl))
                    logger.info(f'已补齐{table_name}.{column_name}字段')


async def ensure_sys_user_vip_sponsor_columns() -> None:
    """
    补齐VIP识图次数与赞助字段，兼容已部署库升级。
    """
    ddl_map = SYS_USER_VIP_SPONSOR_COLUMN_SQL.get(DataBaseConfig.db_type)
    if not ddl_map:
        return

    async with async_engine.begin() as conn:
        existing_columns = await conn.run_sync(_get_table_columns, SYS_USER_TABLE)
        if not existing_columns:
            return
        for column_name, ddl in ddl_map.items():
            if column_name not in existing_columns:
                await conn.execute(text(ddl))
                logger.info(f'已补齐{SYS_USER_TABLE}.{column_name}字段')


async def ensure_default_ai_recognition_config() -> None:
    """
    补齐新用户默认普通AI识图次数配置，兼容已部署库升级。
    """
    sql = DEFAULT_AI_RECOGNITION_CONFIG_SQL.get(DataBaseConfig.db_type)
    if not sql:
        return

    async with async_engine.begin() as conn:
        await conn.execute(text(sql))


async def ensure_damage_formula_version_schema() -> None:
    """
    补齐公式版本表字段容量，兼容已部署库升级。

    完整公式包包含工作簿数据，MySQL TEXT 容量不够；Base.metadata.create_all 不会修改已有列。
    """
    ddl_map = DAMAGE_FORMULA_VERSION_COLUMN_SQL.get(DataBaseConfig.db_type)
    if ddl_map is None:
        return

    async with async_engine.begin() as conn:
        column_info = await conn.run_sync(
            _get_table_column_info,
            DAMAGE_FORMULA_VERSION_TABLE,
            'formula_package_json',
        )
        if not column_info:
            return
        if DataBaseConfig.db_type == 'mysql':
            column_type = str(column_info.get('type', '')).lower()
            if column_type != 'longtext':
                await conn.execute(text(ddl_map['formula_package_json']))
                logger.info(f'已升级{DAMAGE_FORMULA_VERSION_TABLE}.formula_package_json字段为LONGTEXT')


async def init_create_table() -> None:
    """
    应用启动时初始化数据库连接

    :return:
    """
    logger.info('🔎 初始化数据库连接...')
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_system_roles()
    async with async_engine.begin() as conn:
        await run_schema_migrations(conn)
    await ensure_internal_power_entry_limit_columns()
    await ensure_internal_power_lingyun_columns()
    await ensure_sys_user_vip_sponsor_columns()
    await ensure_default_ai_recognition_config()
    await ensure_damage_formula_version_schema()
    logger.info('✅️ 数据库连接成功')


async def close_async_engine() -> None:
    """
    应用关闭时释放数据库连接池

    :return:
    """
    await async_engine.dispose()

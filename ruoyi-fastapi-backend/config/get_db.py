from collections.abc import AsyncGenerator

from sqlalchemy import Connection, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal, Base, async_engine
from config.env import DataBaseConfig
from utils.log_util import logger

INTERNAL_POWER_ENTRY_TABLE = 'system_internal_power_entry'
SYSTEM_INTERNAL_POWER_PRESET_TABLE = 'system_internal_power_preset'
PERSONAL_INTERNAL_POWER_TABLE = 'personal_internal_power'
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


async def init_create_table() -> None:
    """
    应用启动时初始化数据库连接

    :return:
    """
    logger.info('🔎 初始化数据库连接...')
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_internal_power_entry_limit_columns()
    await ensure_internal_power_lingyun_columns()
    logger.info('✅️ 数据库连接成功')


async def close_async_engine() -> None:
    """
    应用关闭时释放数据库连接池

    :return:
    """
    await async_engine.dispose()

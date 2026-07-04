from collections.abc import AsyncGenerator

from sqlalchemy import Connection, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal, Base, async_engine
from config.env import DataBaseConfig
from utils.log_util import logger

INTERNAL_POWER_ENTRY_TABLE = 'system_internal_power_entry'
SYSTEM_INTERNAL_POWER_PRESET_TABLE = 'system_internal_power_preset'
PERSONAL_INTERNAL_POWER_TABLE = 'personal_internal_power'
SYS_USER_TABLE = 'sys_user'
DAMAGE_FORMULA_VERSION_TABLE = 'system_damage_formula_version'
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

SYS_USER_VIP_SPONSOR_PERMISSION_SQL = [
    """
    INSERT INTO sys_menu (
      menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache,
      menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark
    )
    SELECT 3130, 'VIP授权修改', menu_id, 8, '#', '', '', '', 1, 0, 'F', '0', '0',
           'system:user:vip:edit', '#', 'admin', NOW(), '', NULL, ''
    FROM sys_menu
    WHERE perms = 'system:user:list'
      AND NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'system:user:vip:edit')
    LIMIT 1
    """,
    """
    INSERT INTO sys_menu (
      menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache,
      menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark
    )
    SELECT 3131, '赞助状态修改', menu_id, 9, '#', '', '', '', 1, 0, 'F', '0', '0',
           'system:user:sponsor:edit', '#', 'admin', NOW(), '', NULL, ''
    FROM sys_menu
    WHERE perms = 'system:user:list'
      AND NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'system:user:sponsor:edit')
    LIMIT 1
    """,
    """
    INSERT INTO sys_menu (
      menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache,
      menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark
    )
    SELECT 3132, 'AI识图次数修改', menu_id, 10, '#', '', '', '', 1, 0, 'F', '0', '0',
           'system:user:ai:edit', '#', 'admin', NOW(), '', NULL, ''
    FROM sys_menu
    WHERE perms = 'system:user:list'
      AND NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'system:user:ai:edit')
    LIMIT 1
    """,
]

INTERNAL_POWER_PANEL_SETTING_MENU_SQL = [
    """
    INSERT INTO sys_menu (
      menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
      is_frame, is_cache, menu_type, visible, status, perms, icon,
      create_by, create_time, update_by, update_time, remark
    ) VALUES (
      3115, '面板设置', 3000, 7, 'internal-power-panel', 'personal/internalPowerPanel/index', '',
      'PersonalInternalPowerPanel', 1, 0, 'C', '0', '0', 'personal:internal-power-panel:list',
      'chart', 'admin', NOW(), '', NULL, '个人内功PVP收益面板设置菜单'
    )
    ON DUPLICATE KEY UPDATE
      menu_name = VALUES(menu_name),
      parent_id = VALUES(parent_id),
      order_num = VALUES(order_num),
      path = VALUES(path),
      component = VALUES(component),
      route_name = VALUES(route_name),
      menu_type = VALUES(menu_type),
      visible = VALUES(visible),
      status = VALUES(status),
      perms = VALUES(perms),
      icon = VALUES(icon),
      update_by = 'admin',
      update_time = NOW(),
      remark = VALUES(remark)
    """,
    """
    INSERT INTO sys_menu (
      menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
      is_frame, is_cache, menu_type, visible, status, perms, icon,
      create_by, create_time, update_by, update_time, remark
    ) VALUES (
      3116, '面板设置保存', 3115, 1, '#', '', '', '', 1, 0, 'F', '0', '0',
      'personal:internal-power-panel:edit', '#', 'admin', NOW(), '', NULL, ''
    )
    ON DUPLICATE KEY UPDATE
      menu_name = VALUES(menu_name),
      parent_id = VALUES(parent_id),
      perms = VALUES(perms),
      update_by = 'admin',
      update_time = NOW(),
      remark = VALUES(remark)
    """,
    """
    INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
      (1, 3115), (1, 3116),
      (2, 3115), (2, 3116)
    """,
]

FORMULA_DESIGN_MENU_SQL = [
    """
    INSERT INTO sys_menu (
      menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
      is_frame, is_cache, menu_type, visible, status, perms, icon,
      create_by, create_time, update_by, update_time, remark
    ) VALUES (
      3140, '公式设计', 1, 13, 'formulaDesign', 'system/formulaDesign/index', '',
      'SystemFormulaDesign', 1, 0, 'C', '0', '0', 'system:formula-design:list',
      'edit', 'admin', NOW(), '', NULL, '系统内功PVP收益公式设计菜单'
    )
    ON DUPLICATE KEY UPDATE
      menu_name = VALUES(menu_name),
      parent_id = VALUES(parent_id),
      order_num = VALUES(order_num),
      path = VALUES(path),
      component = VALUES(component),
      route_name = VALUES(route_name),
      menu_type = VALUES(menu_type),
      visible = VALUES(visible),
      status = VALUES(status),
      perms = VALUES(perms),
      icon = VALUES(icon),
      update_by = 'admin',
      update_time = NOW(),
      remark = VALUES(remark)
    """,
    """
    INSERT INTO sys_menu (
      menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
      is_frame, is_cache, menu_type, visible, status, perms, icon,
      create_by, create_time, update_by, update_time, remark
    ) VALUES
      (3141, '公式版本查询', 3140, 1, '#', '', '', '', 1, 0, 'F', '0', '0',
       'system:formula-design:query', '#', 'admin', NOW(), '', NULL, ''),
      (3142, '公式版本新增', 3140, 2, '#', '', '', '', 1, 0, 'F', '0', '0',
       'system:formula-design:add', '#', 'admin', NOW(), '', NULL, ''),
      (3143, '公式版本修改', 3140, 3, '#', '', '', '', 1, 0, 'F', '0', '0',
       'system:formula-design:edit', '#', 'admin', NOW(), '', NULL, ''),
      (3144, '公式版本发布', 3140, 4, '#', '', '', '', 1, 0, 'F', '0', '0',
       'system:formula-design:publish', '#', 'admin', NOW(), '', NULL, '')
    ON DUPLICATE KEY UPDATE
      menu_name = VALUES(menu_name),
      parent_id = VALUES(parent_id),
      perms = VALUES(perms),
      update_by = 'admin',
      update_time = NOW(),
      remark = VALUES(remark)
    """,
    """
    INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
      (1, 3140), (1, 3141), (1, 3142), (1, 3143), (1, 3144)
    """,
]

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


async def ensure_sys_user_vip_sponsor_permission_menus() -> None:
    """
    补齐用户管理下的VIP、赞助和AI识图次数细分权限按钮。
    """
    async with async_engine.begin() as conn:
        for sql in SYS_USER_VIP_SPONSOR_PERMISSION_SQL:
            await conn.execute(text(sql))


async def ensure_internal_power_panel_setting_menu() -> None:
    """
    补齐个人内功PVP收益面板设置菜单，并迁移旧词条换算菜单入口。
    """
    async with async_engine.begin() as conn:
        for sql in INTERNAL_POWER_PANEL_SETTING_MENU_SQL:
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


async def ensure_formula_design_menu() -> None:
    """
    补齐系统管理下的公式设计菜单。
    """
    async with async_engine.begin() as conn:
        for sql in FORMULA_DESIGN_MENU_SQL:
            await conn.execute(text(sql))


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
    await ensure_sys_user_vip_sponsor_columns()
    await ensure_sys_user_vip_sponsor_permission_menus()
    await ensure_internal_power_panel_setting_menu()
    await ensure_damage_formula_version_schema()
    await ensure_formula_design_menu()
    logger.info('✅️ 数据库连接成功')


async def close_async_engine() -> None:
    """
    应用关闭时释放数据库连接池

    :return:
    """
    await async_engine.dispose()

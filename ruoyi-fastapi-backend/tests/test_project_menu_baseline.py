from pathlib import Path

from config.schema_migrations import LEGACY_MENU_IDS, load_project_menu_baseline

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MYSQL_INSTALL_SQL = BACKEND_ROOT / 'sql' / 'ruoyi-fastapi.sql'
POSTGRES_INSTALL_SQL = BACKEND_ROOT / 'sql' / 'ruoyi-fastapi-pg.sql'
STARTUP_DB_MODULE = BACKEND_ROOT / 'config' / 'get_db.py'
ACTIVITY_MENU_SQL = BACKEND_ROOT / 'sql' / '20260914_activity_information_menus.sql'
EXPECTED_ROLE_MENU_COUNTS = {'1': 148, '2': 31, '100': 11}


def test_project_menu_baseline_has_only_expected_top_level_menus() -> None:
    baseline = load_project_menu_baseline()
    top_level = [menu for menu in baseline['menus'] if menu['parent_id'] == 0]

    assert [menu['menu_name'] for menu in top_level] == ['系统管理', '系统监控', '系统工具', '帮会管理', '个人管理']
    assert not {menu['menu_id'] for menu in baseline['menus']} & set(LEGACY_MENU_IDS)
    assert not {'AI 管理', '模型管理', 'AI 对话', '若依官网'} & {menu['menu_name'] for menu in baseline['menus']}


def test_project_menu_baseline_contains_current_business_features() -> None:
    baseline = load_project_menu_baseline()
    names = {menu['menu_name'] for menu in baseline['menus']}
    permissions = {menu['perms'] for menu in baseline['menus']}

    assert {'帮会管理', '个人管理', 'AIKey管理', '数据库管理', '内功管理', '坦度计算器'} <= names
    assert '防守计算器' not in names
    assert {'system:aikey:edit', 'personal:defense-calculator:list'} <= permissions
    license_menus = {menu['menu_id']: menu for menu in baseline['menus'] if 3170 <= menu['menu_id'] <= 3175}
    assert set(license_menus) == {3170, 3171, 3172, 3173, 3174, 3175}
    assert license_menus[3170]['parent_id'] == 1
    assert license_menus[3170]['component'] == 'system/license/index'
    assert {menu['perms'] for menu in license_menus.values()} >= {
        'system:license:list', 'system:license:grant', 'system:license:revoke',
        'system:license:remark', 'system:license:audit',
    }
    assert set(license_menus) <= set(baseline['role_menus']['1'])
    assert not set(license_menus) & set(baseline['role_menus']['2'])
    assert not set(license_menus) & set(baseline['role_menus']['100'])


def test_legacy_battle_management_branch_is_removed() -> None:
    baseline = load_project_menu_baseline()
    names = {menu['menu_name'] for menu in baseline['menus']}
    permissions = {menu['perms'] for menu in baseline['menus']}

    assert not {'约战管理', '历史数据管理', '约战报名', '数据导入'} & names
    assert not {'guild:battle:list', 'guild:battle:import', 'guild:battle:query', 'guild:battle:remove'} & permissions


def test_schedule_is_standalone_and_obsolete_group_review_menus_are_removed() -> None:
    baseline = load_project_menu_baseline()
    menus = baseline['menus']
    names = {menu['menu_name'] for menu in menus}
    schedule = next(menu for menu in menus if menu['menu_name'] == '约战排表')

    assert schedule['parent_id'] == 1065
    assert not {'分团管理', '审核管理', '成员审核', '约战审核'} & names
    for menu_ids in baseline['role_menus'].values():
        assert not {1068, 1073, 1074, 1075} & set(menu_ids)


def test_manual_activity_menu_migration_matches_current_personal_public_rules() -> None:
    sql = ACTIVITY_MENU_SQL.read_text(encoding='utf-8')

    assert 'GuildFindBattles' not in sql
    assert "'找约战',47000" not in sql
    assert "'找约战',47004" in sql
    assert sql.count("'历史约战'") == 2
    assert "'历史战报'" not in sql
    assert 'DELETE FROM sys_menu WHERE menu_id=47002' in sql


def test_builtin_roles_have_a_one_time_default_menu_snapshot() -> None:
    role_menus = load_project_menu_baseline()['role_menus']

    assert set(role_menus) == {'1', '2', '100'}
    assert {role_id: len(menu_ids) for role_id, menu_ids in role_menus.items()} == EXPECTED_ROLE_MENU_COUNTS


def test_install_sql_matches_project_menu_baseline() -> None:
    for path in (MYSQL_INSTALL_SQL, POSTGRES_INSTALL_SQL):
        sql = path.read_text(encoding='utf-8')
        assert "'帮会管理'" in sql
        assert "'个人管理'" in sql
        assert "'AIKey管理'" in sql
        assert "'坦度计算器'" in sql
        assert "'AI 管理'" not in sql
        assert "'模型管理'" not in sql
        assert "'AI 对话'" not in sql
        assert "'若依官网'" not in sql
        assert 'ai_chat_config' not in sql

    postgres_sql = POSTGRES_INSTALL_SQL.read_text(encoding='utf-8')
    assert "setval(pg_get_serial_sequence('sys_menu', 'menu_id')" in postgres_sql


def test_startup_uses_versioned_menu_migration_only() -> None:
    source = STARTUP_DB_MODULE.read_text(encoding='utf-8')
    init_body = source.split('async def init_create_table()', maxsplit=1)[1]

    assert 'await run_schema_migrations(conn)' in init_body
    assert 'await ensure_sys_user_vip_sponsor_permission_menus()' not in init_body
    assert 'await ensure_personal_defense_calculator_menu()' not in init_body
    assert 'await ensure_internal_power_panel_setting_menu()' not in init_body
    assert 'await ensure_formula_design_menu()' not in init_body
    assert 'await ensure_internal_power_panel_template_menu()' not in init_body

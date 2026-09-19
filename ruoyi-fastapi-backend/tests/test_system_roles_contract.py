from pathlib import Path

from config.get_db import SYSTEM_ROLE_SQL
from config.schema_migrations import _account_license_schema_sql, _auth_refresh_token_schema_sql
from module_integration.license import SystemAccountLicense, SystemAccountLicenseAudit
from module_integration.refresh_tokens import SystemAuthRefreshToken


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MYSQL_INSTALL_SQL = BACKEND_ROOT / 'sql' / 'ruoyi-fastapi.sql'
POSTGRES_INSTALL_SQL = BACKEND_ROOT / 'sql' / 'ruoyi-fastapi-pg.sql'
SQL_DIR = BACKEND_ROOT / 'sql'


def test_startup_contains_three_builtin_system_roles() -> None:
    for database_type in ('mysql', 'postgresql'):
        sql = SYSTEM_ROLE_SQL[database_type]
        assert "'超级管理员', 'cptbtptp'" in sql
        assert "'帮会管理', 'common'" in sql
        assert "'帮会成员', 'user'" in sql


def test_fresh_install_scripts_contain_three_builtin_system_roles() -> None:
    for path in (MYSQL_INSTALL_SQL, POSTGRES_INSTALL_SQL):
        sql = path.read_text(encoding='utf-8')
        assert (
            "'1', '超级管理员',  'cptbtptp'" in sql
            or "(1, '超级管理员',  'cptbtptp'" in sql
        )
        assert "'帮会管理'," in sql and "'common'" in sql
        assert "'帮会成员'," in sql and "'user'" in sql


def test_fresh_install_scripts_keep_the_canonical_super_admin_username() -> None:
    for path in (MYSQL_INSTALL_SQL, POSTGRES_INSTALL_SQL):
        sql = path.read_text(encoding='utf-8')
        assert "'cptbtptp369'" in sql
        assert "insert into sys_user values(1" in sql


def test_fresh_install_scripts_include_account_entitlement_schema() -> None:
    for path in (MYSQL_INSTALL_SQL, POSTGRES_INSTALL_SQL):
        sql = path.read_text(encoding='utf-8').lower()
        assert 'create table if not exists system_account_license' in sql
        assert 'create table if not exists system_account_license_audit' in sql
        assert sql.count('references sys_user(user_id)') >= 4


def test_sql_scripts_do_not_authorize_super_admin_by_legacy_role_key() -> None:
    forbidden_fragments = (
        "role_key = 'admin'",
        "role_key <> 'admin'",
        "role_key IN ('admin'",
        "(1, '超级管理员', 'admin'",
    )
    violations: list[str] = []
    for path in SQL_DIR.glob('*.sql'):
        sql = path.read_text(encoding='utf-8')
        for fragment in forbidden_fragments:
            if fragment in sql:
                violations.append(f'{path.name}: {fragment}')

    assert violations == []


def test_account_entitlement_schema_keeps_user_referential_integrity() -> None:
    orm_foreign_keys = {
        str(fk.target_fullname)
        for table in (SystemAccountLicense.__table__, SystemAccountLicenseAudit.__table__, SystemAuthRefreshToken.__table__)
        for fk in table.foreign_keys
    }
    assert {'sys_user.user_id'} <= orm_foreign_keys
    for path in (
        SQL_DIR / '20260919_account_license_mysql.sql',
        SQL_DIR / '20260919_account_license_postgresql.sql',
    ):
        sql = path.read_text(encoding='utf-8').lower()
        assert sql.count('references sys_user(user_id)') == 4
    runtime_sql = '\n'.join(_account_license_schema_sql() + _auth_refresh_token_schema_sql()).lower()
    assert runtime_sql.count('references sys_user(user_id)') == 4

from pathlib import Path

from config.get_db import SYSTEM_ROLE_SQL


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MYSQL_INSTALL_SQL = BACKEND_ROOT / 'sql' / 'ruoyi-fastapi.sql'
POSTGRES_INSTALL_SQL = BACKEND_ROOT / 'sql' / 'ruoyi-fastapi-pg.sql'


def test_startup_contains_three_builtin_system_roles() -> None:
    for database_type in ('mysql', 'postgresql'):
        sql = SYSTEM_ROLE_SQL[database_type]
        assert "'超级管理员', 'admin'" in sql
        assert "'帮会管理', 'common'" in sql
        assert "'帮会成员', 'user'" in sql


def test_fresh_install_scripts_contain_three_builtin_system_roles() -> None:
    for path in (MYSQL_INSTALL_SQL, POSTGRES_INSTALL_SQL):
        sql = path.read_text(encoding='utf-8')
        assert "'超级管理员',  'admin'" in sql
        assert "'帮会管理'," in sql and "'common'" in sql
        assert "'帮会成员'," in sql and "'user'" in sql

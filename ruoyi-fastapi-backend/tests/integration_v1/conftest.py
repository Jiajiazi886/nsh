import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest

from .helpers import FakeDB, FakeRedis, make_request


def pytest_configure(config):
    if os.environ.get('NSH_INTEGRATION_TEST') != '1' or os.environ.get('DB_DATABASE') != 'nsh_integration_test':
        raise pytest.UsageError('Use tools/run_integration_tests.py; this suite must never load real database settings')


@pytest.fixture
def auth_state(monkeypatch):
    from common.enums import RedisInitKeyConfig
    from config.env import AppConfig, JwtConfig
    from module_admin.dao.user_dao import UserDao
    from module_admin.entity.do.role_do import SysRole
    from module_admin.entity.do.user_do import SysUser

    user = SysUser(user_id=23, user_name='member23', status='0', del_flag='0', is_vip='0', pwd_update_date=None)
    role = SysRole(role_id=100, role_key='user')
    redis = FakeRedis()
    queries = []
    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    async def query_user(db, user_id):
        queries.append(user_id)
        return {
            'user_basic_info': user,
            'user_role_info': [role],
            'user_menu_info': [],
            'user_post_info': [],
            'user_dept_info': None,
        }

    def token(payload=None, *, secret=None, algorithm='HS256', session='session-a'):
        claims = {'user_id': '23', 'session_id': session, 'exp': expires}
        if payload is not None:
            claims = payload
        return jwt.encode(claims, secret if secret is not None else JwtConfig.jwt_secret_key, algorithm=algorithm)

    def activate(encoded, session='session-a'):
        redis.values[f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session}'] = encoded

    monkeypatch.setattr(AppConfig, 'app_same_time_login', True)
    monkeypatch.setattr(UserDao, 'get_user_by_id', query_user)
    encoded = token()
    activate(encoded)
    return SimpleNamespace(
        user=user,
        redis=redis,
        queries=queries,
        token=token,
        activate=activate,
        request=make_request(redis),
        db=FakeDB(),
        prefix=RedisInitKeyConfig.ACCESS_TOKEN.key,
    )

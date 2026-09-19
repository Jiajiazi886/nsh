import inspect
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request

from exceptions.exception import LoginException
from module_admin.controller.login_controller import login
from module_admin.service.login_service import CustomOAuth2PasswordRequestForm, LoginService
from module_admin.service.user_service import UserService


class FakeRedis:
    async def get(self, _key):
        return None

    async def set(self, *_args, **_kwargs):
        return True

    async def delete(self, *_args, **_kwargs):
        return 0


class FakeDatabase:
    def __init__(self, scalar_value):
        self.scalar_value = scalar_value
        self.statement = None

    async def scalar(self, statement):
        self.statement = statement
        return self.scalar_value


def make_request() -> Request:
    app = FastAPI()
    app.state.redis = FakeRedis()
    return Request(
        {
            'type': 'http',
            'method': 'POST',
            'path': '/login',
            'query_string': b'',
            'headers': [],
            'app': app,
            'client': ('127.0.0.1', 12345),
        }
    )


def make_form(client_type: str) -> CustomOAuth2PasswordRequestForm:
    return CustomOAuth2PasswordRequestForm(
        grant_type='password',
        username='member23',
        password='synthetic-only',
        scope='',
        client_id=None,
        client_secret=None,
        code='',
        uuid='',
        login_info=None,
        client_type=client_type,
    )


@pytest.mark.asyncio
async def test_license_admin_login_rejects_non_super_admin_before_token_issue(monkeypatch) -> None:
    user = SimpleNamespace(user_id=23, user_name='member23')
    db = FakeDatabase(None)
    token_issued = False

    async def authenticate(*_args, **_kwargs):
        return user, None

    async def create_token(*_args, **_kwargs):
        nonlocal token_issued
        token_issued = True
        return 'must-not-be-issued'

    monkeypatch.setattr(LoginService, 'authenticate_user', authenticate)
    monkeypatch.setattr(LoginService, 'create_access_token', create_token)

    raw_login = inspect.unwrap(login)
    with pytest.raises(LoginException) as exc_info:
        await raw_login(make_request(), make_form('license-admin'), db)

    assert '只有超级管理员' in exc_info.value.message
    assert token_issued is False
    assert db.statement is not None
    params = db.statement.compile().params
    assert 1 in params.values()
    assert 'cptbtptp' in params.values()


@pytest.mark.asyncio
async def test_regular_client_login_does_not_use_license_admin_role_gate(monkeypatch) -> None:
    user = SimpleNamespace(user_id=23, user_name='member23')
    db = FakeDatabase(None)

    async def authenticate(*_args, **_kwargs):
        return user, None

    async def create_token(*_args, **_kwargs):
        return 'regular-access-token'

    async def edit_user(*_args, **_kwargs):
        return None

    monkeypatch.setattr(LoginService, 'authenticate_user', authenticate)
    monkeypatch.setattr(LoginService, 'create_access_token', create_token)
    monkeypatch.setattr(UserService, 'edit_user_services', edit_user)

    raw_login = inspect.unwrap(login)
    response = await raw_login(make_request(), make_form('web'), db)

    assert response.status_code == 200
    assert db.statement is None

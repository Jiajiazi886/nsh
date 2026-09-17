import inspect

import pytest
from starlette.responses import JSONResponse

from common.enums import RedisInitKeyConfig
from exceptions.exception import ServiceException
from module_admin.controller import login_controller as legacy
from module_admin.service.login_service import LoginService
from module_admin.service.user_service import UserService
from utils.response_util import ResponseUtil

from .test_v1_contract import call, v1_app


def enabled(auth_state, captcha=False):
    prefix = RedisInitKeyConfig.SYS_CONFIG.key
    auth_state.redis.values[f'{prefix}:sys.account.registerUser'] = 'true'
    auth_state.redis.values[f'{prefix}:sys.account.captchaEnabled'] = 'true' if captcha else 'false'


@pytest.mark.asyncio
async def test_register_delegates_to_existing_decorated_entry(v1_app, auth_state, monkeypatch):
    enabled(auth_state)
    calls = []
    async def register(request, user_register, query_db):
        calls.append(user_register)
        assert query_db is auth_state.db
        return ResponseUtil.success(dict_content={})
    monkeypatch.setattr(legacy, 'register_user', register)
    response = await call(v1_app, 'POST', '/api/v1/auth/register', json={
        'userName': 'new_player', 'password': 'Test123!', 'confirmPassword': 'Test123!',
        'code': '1234', 'uuid': 'captcha-a'})
    assert response.status_code == 200
    assert response.json()['data'] == {'registered': True, 'userName': 'new_player'}
    assert calls[0].username == 'new_player'
    assert calls[0].confirm_password == 'Test123!'
    assert calls[0].code == '1234' and calls[0].uuid == 'captcha-a'
    assert 'Test123!' not in response.text
    assert 'accessToken' not in response.text


@pytest.mark.asyncio
async def test_closed_registration_cannot_be_bypassed(v1_app, monkeypatch):
    async def forbidden(**kwargs):
        pytest.fail('closed registration must not call the writer')
    monkeypatch.setattr(legacy, 'register_user', forbidden)
    response = await call(v1_app, 'POST', '/api/v1/auth/register', json={
        'userName': 'new_player', 'password': 'Test123!', 'confirmPassword': 'Test123!'})
    assert response.status_code == 403
    assert response.json()['errorKey'] == 'REGISTRATION_DISABLED'


@pytest.mark.asyncio
@pytest.mark.parametrize('change', [
    {'confirmPassword': 'Different123!'}, {'userName': ' '}, {'userName': 'x' * 21},
    {'password': '1234', 'confirmPassword': '1234'},
    {'password': 'bad<pass', 'confirmPassword': 'bad<pass'},
    {'roleIds': [1]}, {'userId': '1'}, {'captchaEnabled': False},
])
async def test_register_validation_never_echoes_credentials(v1_app, auth_state, monkeypatch, change):
    enabled(auth_state)
    async def forbidden(**kwargs):
        pytest.fail('invalid registration must not call the writer')
    monkeypatch.setattr(legacy, 'register_user', forbidden)
    payload = {'userName': 'new_player', 'password': 'Private123!', 'confirmPassword': 'Private123!', **change}
    response = await call(v1_app, 'POST', '/api/v1/auth/register', json=payload)
    assert response.status_code == 422
    assert payload['password'] not in response.text
    assert payload['confirmPassword'] not in response.text


@pytest.mark.asyncio
async def test_register_rate_limit_response_is_normalized(v1_app, auth_state, monkeypatch):
    enabled(auth_state)
    async def limited(**kwargs):
        return JSONResponse({'code': 429, 'msg': 'private limit details'})
    monkeypatch.setattr(legacy, 'register_user', limited)
    response = await call(v1_app, 'POST', '/api/v1/auth/register', json={
        'userName': 'new_player', 'password': 'Test123!', 'confirmPassword': 'Test123!'})
    assert response.status_code == 429
    assert response.json()['errorKey'] == 'RATE_LIMITED'
    assert 'private' not in response.text


@pytest.mark.asyncio
async def test_register_preserves_duplicate_account_error(v1_app, auth_state, monkeypatch):
    enabled(auth_state)
    async def duplicate(**kwargs):
        raise ServiceException(message='新增用户new_player失败，登录账号已存在')
    monkeypatch.setattr(legacy, 'register_user', duplicate)
    response = await call(v1_app, 'POST', '/api/v1/auth/register', json={
        'userName': 'new_player', 'password': 'Test123!', 'confirmPassword': 'Test123!'})
    assert response.status_code == 409
    assert response.json()['errorKey'] == 'ACCOUNT_EXISTS'


@pytest.mark.asyncio
async def test_real_register_service_checks_captcha_and_default_role(v1_app, auth_state, monkeypatch):
    enabled(auth_state, captcha=True)
    prefix = RedisInitKeyConfig.CAPTCHA_CODES.key
    auth_state.redis.values[f'{prefix}:captcha-a'] = '1234'
    writes = []
    async def writer(db, model):
        writes.append(model)
        return ResponseUtil.success(dict_content={})
    monkeypatch.setattr(UserService, 'add_user_services', writer)
    async def entry(request, user_register, query_db):
        return await LoginService.register_user_services(request, query_db, user_register)
    monkeypatch.setattr(legacy, 'register_user', entry)
    payload = {'userName': 'new_player', 'password': 'Test123!', 'confirmPassword': 'Test123!',
               'uuid': 'captcha-a', 'code': 'bad'}
    response = await call(v1_app, 'POST', '/api/v1/auth/register', json=payload)
    assert response.status_code == 422 and not writes
    payload['code'] = '1234'
    response = await call(v1_app, 'POST', '/api/v1/auth/register', json=payload)
    assert response.status_code == 200
    assert writes[0].role_ids == [100]
    assert writes[0].password != payload['password']
    assert writes[0].create_by == 'register'
    from module_integration.controller.api_v1_controller import register
    source = inspect.getsource(register)
    assert 'legacy_auth.register_user(' in source and '__wrapped__' not in source


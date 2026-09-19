import httpx
import pytest
from fastapi import FastAPI

from config.get_db import get_db
from exceptions.handle import handle_exception
from module_integration.controller.api_v1_controller import api_v1_controller


@pytest.fixture
def v1_app(auth_state):
    app = FastAPI()
    app.state.redis = auth_state.redis
    handle_exception(app)
    app.include_router(api_v1_controller)

    async def db():
        yield auth_state.db

    app.dependency_overrides[get_db] = db
    return app


async def call(app, method, path, **kwargs):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
        return await client.request(method, path, **kwargs)


@pytest.mark.asyncio
async def test_capabilities_only_advertises_available_features(v1_app):
    response = await call(v1_app, 'GET', '/api/v1/capabilities')
    payload = response.json()
    assert response.status_code == payload['code'] == 200
    assert payload['requestId'] == response.headers['X-Request-ID']
    assert payload['data']['wechatLogin'] is False
    assert payload['data']['botTransport'] is False
    assert 'password' not in response.text.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize('authorization', [None, 'Bearer broken.token.value', 'Basic invalid'])
async def test_v1_auth_uses_real_http_401(v1_app, authorization):
    response = await call(
        v1_app, 'GET', '/api/v1/auth/me', headers={'Authorization': authorization} if authorization else {}
    )
    assert response.status_code == 401
    assert response.json()['code'] == 401 and response.json()['errorKey'] == 'AUTH_REQUIRED'
    assert response.headers['WWW-Authenticate'] == 'Bearer'


@pytest.mark.asyncio
async def test_me_returns_allowlisted_fields_and_string_id(v1_app, auth_state):
    response = await call(v1_app, 'GET', '/api/v1/auth/me', headers={'Authorization': f'Bearer {auth_state.token()}'})
    data = response.json()['data']
    assert response.status_code == 200 and data['userId'] == '23'
    assert set(data) == {'userId', 'userName', 'nickName', 'roles', 'permissions'}
    assert 'password' not in response.text and 'member_user_id' not in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_v1_real_business_permissions_have_http_403(v1_app, auth_state, monkeypatch, kind):
    from exceptions.exception import PermissionException
    from module_guild.service.battle_registration_service import BattleRegistrationService

    async def fail(*args, **kwargs):
        raise PermissionException(message='不能申请他人', data={'errorKey': 'MEMBER_NOT_OWNER'})

    monkeypatch.setattr(
        BattleRegistrationService, f'submit_public_{"leave" if kind == "leave" else "registration"}_service', fail
    )
    response = await call(
        v1_app,
        'POST',
        f'/api/v1/invitations/invite-a/{kind}',
        json={'memberId': '9'},
        headers={'Authorization': f'Bearer {auth_state.token()}'},
    )
    assert response.status_code == 403 and response.json()['errorKey'] == 'MEMBER_NOT_OWNER'


@pytest.mark.asyncio
@pytest.mark.parametrize('member_id', ['0', '-1', '9223372036854775808', '9.0', 9, True])
async def test_v1_member_ids_are_bounded_decimal_strings(v1_app, auth_state, member_id):
    response = await call(
        v1_app,
        'POST',
        '/api/v1/invitations/invite-a/leave',
        json={'memberId': member_id, 'password': 'do-not-echo'},
        headers={'Authorization': f'Bearer {auth_state.token()}'},
    )
    assert response.status_code == 422 and response.json()['errorKey'] == 'VALIDATION_FAILED'
    assert 'do-not-echo' not in response.text


@pytest.mark.asyncio
async def test_unexpected_error_is_sanitized(v1_app, auth_state, monkeypatch):
    from module_guild.service.battle_registration_service import BattleRegistrationService

    async def fail(*args, **kwargs):
        raise RuntimeError('SQL password private host E:/private')

    monkeypatch.setattr(BattleRegistrationService, 'submit_public_leave_service', fail)
    response = await call(
        v1_app,
        'POST',
        '/api/v1/invitations/invite-a/leave',
        json={'memberId': '9'},
        headers={'Authorization': f'Bearer {auth_state.token()}'},
    )
    assert response.status_code == 500 and response.json()['errorKey'] == 'INTERNAL_ERROR'
    assert 'SQL' not in response.text and 'private' not in response.text


@pytest.mark.asyncio
async def test_wechat_login_is_explicitly_unavailable(v1_app):
    response = await call(v1_app, 'POST', '/api/v1/auth/wechat/login', json={'code': 'unverified'})
    assert response.status_code == 503 and response.json()['errorKey'] == 'CAPABILITY_DISABLED'


@pytest.mark.asyncio
async def test_logout_revokes_only_current_session(v1_app, auth_state):
    second = auth_state.token(session='session-b')
    auth_state.activate(second, session='session-b')
    response = await call(
        v1_app, 'POST', '/api/v1/auth/logout', headers={'Authorization': f'Bearer {auth_state.token()}'}
    )
    assert response.status_code == 200
    again = await call(v1_app, 'GET', '/api/v1/auth/me', headers={'Authorization': f'Bearer {auth_state.token()}'})
    assert again.status_code == 401
    other = await call(v1_app, 'GET', '/api/v1/auth/me', headers={'Authorization': f'Bearer {second}'})
    assert other.status_code == 200


@pytest.mark.asyncio
async def test_json_login_reuses_existing_decorated_entry(v1_app, monkeypatch):
    from module_admin.controller import login_controller as legacy
    from utils.response_util import ResponseUtil

    calls = []

    async def login(request, form_data, query_db):
        calls.append((form_data.username, form_data.password, form_data.code, form_data.uuid))
        return ResponseUtil.success(dict_content={'token': 'synthetic.test.token'})

    monkeypatch.setattr(legacy, 'login', login)
    response = await call(
        v1_app,
        'POST',
        '/api/v1/auth/login',
        json={'userName': 'member23', 'password': 'synthetic-only', 'code': '1234', 'uuid': 'captcha-test'},
    )
    assert response.status_code == 200 and response.json()['data']['accessToken'] == 'synthetic.test.token'
    assert response.json()['data']['tokenType'] == 'Bearer'
    assert calls == [('member23', 'synthetic-only', '1234', 'captcha-test')]


@pytest.mark.asyncio
async def test_license_admin_login_skips_image_captcha_but_keeps_client_marker(v1_app, monkeypatch):
    from module_admin.controller import login_controller as legacy
    from utils.response_util import ResponseUtil

    seen = {}

    async def login(request, form_data, query_db):
        seen['client_type'] = form_data.client_type
        seen['code'] = form_data.code
        seen['uuid'] = form_data.uuid
        return ResponseUtil.success(dict_content={'token': 'synthetic.test.token'})

    monkeypatch.setattr(legacy, 'login', login)
    response = await call(
        v1_app,
        'POST',
        '/api/v1/auth/login',
        json={'userName': 'admin', 'password': 'synthetic-only', 'clientType': 'license-admin'},
    )
    assert response.status_code == 200
    assert seen == {'client_type': 'license-admin', 'code': '', 'uuid': ''}


@pytest.mark.asyncio
@pytest.mark.parametrize('legacy_code, expected', [(601, 401), (500, 500), (429, 429)])
async def test_legacy_login_failures_are_normalized_and_sanitized(v1_app, monkeypatch, legacy_code, expected):
    from module_admin.controller import login_controller as legacy
    from starlette.responses import JSONResponse

    async def login(**kwargs):
        return JSONResponse({'code': legacy_code, 'msg': 'SQL private password'})

    monkeypatch.setattr(legacy, 'login', login)
    response = await call(
        v1_app, 'POST', '/api/v1/auth/login', json={'userName': 'member23', 'password': 'synthetic-only'}
    )
    assert response.status_code == expected
    assert 'SQL' not in response.text and 'private' not in response.text


@pytest.mark.asyncio
async def test_login_validation_never_echoes_password(v1_app):
    response = await call(
        v1_app, 'POST', '/api/v1/auth/login', json={'userName': '', 'password': 'never-echo-password'}
    )
    assert response.status_code == 422 and 'never-echo-password' not in response.text


@pytest.mark.asyncio
async def test_public_auth_config_and_captcha_reuse_legacy_services(v1_app, monkeypatch):
    from module_admin.controller import captcha_controller as legacy_captcha
    from utils.response_util import ResponseUtil

    calls = []

    async def captcha(request):
        calls.append(True)
        return ResponseUtil.success(
            dict_content={
                'captchaEnabled': True,
                'registerEnabled': False,
                'img': 'synthetic-base64',
                'uuid': 'captcha-test',
            }
        )

    monkeypatch.setattr(legacy_captcha, 'get_captcha_image', captcha)
    config = await call(v1_app, 'GET', '/api/v1/auth/config')
    response = await call(v1_app, 'GET', '/api/v1/auth/captcha')
    assert config.status_code == 200 and config.json()['data']['wechatLogin'] is False
    assert response.status_code == 200 and response.json()['data']['uuid'] == 'captcha-test'
    assert calls == [True]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'path, method, expected', [('/api/v1/not-present', 'GET', 404), ('/api/v1/auth/me', 'DELETE', 405)]
)
async def test_unmatched_v1_requests_keep_the_contract(v1_app, path, method, expected):
    response = await call(v1_app, method, path)
    assert response.status_code == expected and response.json()['code'] == expected
    assert response.json()['requestId'] == response.headers['X-Request-ID']
    assert response.json()['success'] is False


@pytest.mark.asyncio
async def test_openapi_defines_auth_and_string_member_ids(v1_app):
    schema = v1_app.openapi()
    assert schema['paths']['/api/v1/auth/me']['get'].get('security')
    assert schema['paths']['/api/v1/invitations/{invite_code}/leave']['post'].get('security')
    assert not schema['paths']['/api/v1/capabilities']['get'].get('security')
    assert schema['components']['schemas']['MemberChoice']['properties']['memberId']['type'] == 'string'
    operation = schema['paths']['/api/v1/invitations/{invite_code}/leave']['post']
    assert {'401', '403', '404', '409', '422', '500'} <= set(operation['responses'])
    operation_ids = [item['operationId'] for methods in schema['paths'].values() for item in methods.values()]
    assert len(operation_ids) == len(set(operation_ids))


@pytest.mark.asyncio
async def test_missing_invitation_returns_http_404(v1_app, auth_state):
    response = await call(
        v1_app,
        'POST',
        '/api/v1/invitations/not-present/leave',
        json={'memberId': '9'},
        headers={'Authorization': f'Bearer {auth_state.token()}'},
    )
    assert response.status_code == 404 and response.json()['errorKey'] == 'INVITE_NOT_FOUND'


@pytest.mark.asyncio
@pytest.mark.parametrize('allowed', [True, False])
async def test_actual_login_decorators_and_session_issuance_are_exercised(v1_app, auth_state, monkeypatch, allowed):
    from common.annotation.cache_annotation import ApiCacheManager
    from common.annotation.log_annotation import Log
    from common.annotation.rate_limit_annotation import ApiRateLimit
    from module_admin.service import login_service as login_module
    from module_admin.service.log_service import LogQueueService
    from module_admin.service.user_service import UserService
    from utils.access_token_util import decode_access_token
    from utils.pwd_util import PwdUtil
    from config.env import JwtConfig

    counts = {'rate': 0, 'password': 0, 'audit': 0, 'cache': 0, 'user': 0}

    async def limit(self, redis, request):
        counts['rate'] += 1
        return {'allowed': allowed, 'current': 1, 'remaining': 1, 'reset_after_seconds': 30, 'reset_at': 2000000000}

    async def query(db, name):
        assert name == 'member23'
        return auth_state.user, None

    def password(plain, encoded):
        counts['password'] += 1
        assert plain == 'synthetic-only'
        return True

    async def location(*args):
        return 'isolated'

    async def audit(request, model, path):
        counts['audit'] += 1
        assert model.user_name == 'member23'

    async def cache(*args):
        counts['cache'] += 1

    async def edit(*args):
        counts['user'] += 1

    monkeypatch.setattr(ApiRateLimit, '_acquire_rate_limit', limit)
    monkeypatch.setattr(login_module, 'login_by_account', query)
    monkeypatch.setattr(PwdUtil, 'verify_password', password)
    monkeypatch.setattr(Log, '_get_oper_location', location)
    monkeypatch.setattr(LogQueueService, 'enqueue_login_log', audit)
    monkeypatch.setattr(ApiCacheManager, 'clear_namespaces', cache)
    monkeypatch.setattr(UserService, 'edit_user_services', edit)
    response = await call(
        v1_app, 'POST', '/api/v1/auth/login', json={'userName': 'member23', 'password': 'synthetic-only'}
    )
    assert counts['rate'] == 1
    if allowed:
        assert response.status_code == 200
        assert counts == {'rate': 1, 'password': 1, 'audit': 1, 'cache': 1, 'user': 1}
        token = response.json()['data']['accessToken']
        claims = decode_access_token(token, JwtConfig.jwt_secret_key, JwtConfig.jwt_algorithm)
        assert claims.user_id == 23
        assert auth_state.redis.values[f'{auth_state.prefix}:{claims.session_id}'] == token
    else:
        assert response.status_code == 429
        assert counts == {'rate': 1, 'password': 0, 'audit': 0, 'cache': 0, 'user': 0}

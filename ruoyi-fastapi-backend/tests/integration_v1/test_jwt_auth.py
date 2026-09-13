from datetime import datetime, timedelta, timezone

import pytest

from common.aspect.pre_auth import PreAuth
from exceptions.exception import AuthException
from module_admin.service.login_service import LoginService

from .helpers import make_request


@pytest.mark.asyncio
async def test_valid_existing_session_is_accepted(auth_state):
    user = await LoginService.get_current_user(auth_state.request, auth_state.token(), auth_state.db)
    assert user.user.user_id == 23
    assert user.roles == ['user']


@pytest.mark.asyncio
@pytest.mark.parametrize('header', ['Bearer', 'Bearer ', 'Bearer  token', 'Basic token', '', None])
async def test_malformed_tokens_are_auth_errors_not_server_errors(auth_state, header):
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, header, auth_state.db)
    assert auth_state.queries == []


@pytest.mark.asyncio
@pytest.mark.parametrize('missing', ['exp', 'user_id', 'session_id'])
async def test_required_claims_are_validated_before_database_access(auth_state, missing):
    claims = {'user_id': '23', 'session_id': 'session-a', 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}
    claims.pop(missing)
    encoded = auth_state.token(claims)
    auth_state.activate(encoded)
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, encoded, auth_state.db)
    assert auth_state.queries == []


@pytest.mark.asyncio
@pytest.mark.parametrize('user_id', ['not-number', '0', '-1', True, 1.5, '', None, '9223372036854775808'])
async def test_invalid_user_ids_do_not_escape_as_value_errors(auth_state, user_id):
    claims = {'user_id': user_id, 'session_id': 'session-a', 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, auth_state.token(claims), auth_state.db)
    assert auth_state.queries == []


@pytest.mark.asyncio
@pytest.mark.parametrize('session_id', ['', None, 23, 'unsafe:redis:key', ' space ', 'x' * 129])
async def test_invalid_session_claims_are_rejected(auth_state, session_id):
    claims = {'user_id': '23', 'session_id': session_id, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, auth_state.token(claims), auth_state.db)
    assert auth_state.queries == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'kwargs', [{'secret': 'incorrect-test-key-never-use-in-production-12345'}, {'algorithm': 'HS384'}]
)
async def test_wrong_signature_or_algorithm_is_rejected(auth_state, kwargs):
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, auth_state.token(**kwargs), auth_state.db)
    assert auth_state.queries == []


@pytest.mark.asyncio
async def test_expired_jwt_does_not_query_database(auth_state):
    encoded = auth_state.token(
        {'user_id': '23', 'session_id': 'session-a', 'exp': datetime.now(timezone.utc) - timedelta(seconds=1)}
    )
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, encoded, auth_state.db)
    assert auth_state.queries == []


@pytest.mark.asyncio
@pytest.mark.parametrize('field,value', [('status', '1'), ('del_flag', '2')])
async def test_disabled_or_deleted_accounts_cannot_keep_using_valid_tokens(auth_state, field, value):
    setattr(auth_state.user, field, value)
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, auth_state.token(), auth_state.db)
    assert not any(call[0] == 'set' for call in auth_state.redis.calls)


@pytest.mark.asyncio
async def test_revoked_session_is_rejected(auth_state):
    auth_state.redis.values.clear()
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, auth_state.token(), auth_state.db)


@pytest.mark.asyncio
async def test_authorization_header_requires_bearer_scheme(auth_state):
    request = make_request(auth_state.redis, auth_state.token())
    with pytest.raises(AuthException):
        await PreAuth()(request, auth_state.db)
    assert auth_state.queries == []


@pytest.mark.asyncio
async def test_bearer_scheme_is_case_insensitive(auth_state):
    request = make_request(auth_state.redis, f'bearer {auth_state.token()}')
    result = await PreAuth()(request, auth_state.db)
    assert result.user.user_id == 23


@pytest.mark.asyncio
async def test_logout_one_session_does_not_revoke_another(auth_state):
    first = auth_state.token(session='session-a')
    second = auth_state.token(session='session-b')
    auth_state.activate(first, 'session-a')
    auth_state.activate(second, 'session-b')
    await LoginService.logout_services(auth_state.request, 'session-a')
    with pytest.raises(AuthException):
        await LoginService.get_current_user(auth_state.request, first, auth_state.db)
    result = await LoginService.get_current_user(auth_state.request, second, auth_state.db)
    assert result.user.user_id == 23

import hashlib
import hmac
from types import SimpleNamespace

import pytest

from module_integration.bot_auth import SigningKey, verify_service_request
from module_integration.contract import ApiProblem

SECRET = b'synthetic-bot-test-key-never-use-in-production'
NOW = 1800000000
BODY = b'{"messageId":"synthetic-only","subject":"channel-subject"}'


def headers(*, timestamp=NOW, nonce='nonce_test_1234567890', body=BODY, path='/internal/bot/v1/events', method='POST'):
    material = '\n'.join((method, path, str(timestamp), nonce, hashlib.sha256(body).hexdigest())).encode()
    return {
        'X-Bot-Key-Id': 'bridge-test',
        'X-Bot-Timestamp': str(timestamp),
        'X-Bot-Nonce': nonce,
        'X-Bot-Signature': hmac.new(SECRET, material, hashlib.sha256).hexdigest(),
    }


class Nonces:
    def __init__(self):
        self.entries = {}

    async def set(self, key, value, *, nx, ex):
        assert nx is True and ex >= 601
        if key in self.entries:
            return None
        self.entries[key] = value
        return True


@pytest.fixture
def context():
    return SimpleNamespace(keys={'bridge-test': SigningKey(SECRET, 'mock', 'app-test', 'bot-test')}, nonces=Nonces())


async def verify(context, values=None, body=BODY, path='/internal/bot/v1/events', method='POST'):
    return await verify_service_request(
        values or headers(), method, path, body, keys=context.keys, nonce_store=context.nonces, now=NOW
    )


@pytest.mark.asyncio
async def test_valid_service_identity_is_not_a_user_identity(context):
    identity = await verify(context)
    assert (identity.channel, identity.app_id, identity.bot_account) == ('mock', 'app-test', 'bot-test')
    assert not hasattr(identity, 'user_id')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'field,value',
    [
        ('X-Bot-Key-Id', 'unknown'),
        ('X-Bot-Signature', '0' * 64),
        ('X-Bot-Timestamp', str(NOW - 301)),
        ('X-Bot-Timestamp', str(NOW + 301)),
        ('X-Bot-Timestamp', '01800000000'),
        ('X-Bot-Nonce', 'short'),
    ],
)
async def test_invalid_signature_metadata_is_rejected_before_replay_write(context, field, value):
    values = headers()
    values[field] = value
    with pytest.raises(ApiProblem) as error:
        await verify(context, values)
    assert error.value.status == 401 and context.nonces.entries == {}


@pytest.mark.asyncio
@pytest.mark.parametrize('change', ['body', 'path', 'method'])
async def test_signature_covers_all_request_material(context, change):
    kwargs = (
        {'body': b'changed'}
        if change == 'body'
        else {'path': '/internal/bot/v1/queries'}
        if change == 'path'
        else {'method': 'GET'}
    )
    with pytest.raises(ApiProblem) as error:
        await verify(context, **kwargs)
    assert error.value.status == 401


@pytest.mark.asyncio
async def test_nonce_is_claimed_atomically_and_replay_is_rejected(context):
    await verify(context)
    with pytest.raises(ApiProblem) as error:
        await verify(context)
    assert error.value.status == 409 and error.value.key == 'BOT_REPLAY_REJECTED'


@pytest.mark.asyncio
async def test_replay_store_failure_is_fail_closed(context):
    async def failure(*args, **kwargs):
        raise RuntimeError('private-redis-password')

    context.nonces.set = failure
    with pytest.raises(ApiProblem) as error:
        await verify(context)
    assert error.value.status == 503 and 'private' not in error.value.message


@pytest.mark.asyncio
async def test_oversized_body_is_rejected(context):
    with pytest.raises(ApiProblem) as error:
        await verify(context, body=b'x' * (64 * 1024 + 1))
    assert error.value.status == 413 and context.nonces.entries == {}


@pytest.mark.asyncio
@pytest.mark.parametrize('path', ['/internal/bot/v1/events?userId=1', '/internal/bot/v1/%65vents', '/api/v1/auth/me'])
async def test_only_unambiguous_internal_paths_can_be_signed(context, path):
    with pytest.raises(ApiProblem) as error:
        await verify(context, headers(path=path), path=path)
    assert error.value.status == 401


def test_weak_signing_keys_are_rejected():
    with pytest.raises(ValueError):
        SigningKey(b'weak', 'mock', 'app-test', 'bot-test')


def test_signing_key_representation_does_not_disclose_secret():
    assert SECRET.decode() not in repr(SigningKey(SECRET, 'mock', 'app-test', 'bot-test'))

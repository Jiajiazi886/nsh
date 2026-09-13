"""Authentication for our internal bridge, NOT a WeChat/iLink wire protocol.

Service identity is intentionally not a system user identity. A verified,
durably bound channel subject is still required for private business queries.
"""

import hashlib
import hmac
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from module_integration.contract import ApiProblem

MAX_BODY = 64 * 1024
WINDOW_SECONDS = 300
MIN_SIGNING_KEY_BYTES = 32
_PATHS = frozenset({'/internal/bot/v1/events', '/internal/bot/v1/queries', '/internal/bot/v1/deliveries'})


@dataclass(frozen=True)
class SigningKey:
    secret: bytes = field(repr=False)
    channel: str
    app_id: str
    bot_account: str

    def __post_init__(self) -> None:
        if not isinstance(self.secret, bytes) or len(self.secret) < MIN_SIGNING_KEY_BYTES:
            raise ValueError('Signing key requires at least 32 bytes')
        if not all(
            isinstance(value, str) and 0 < len(value) <= 128 for value in (self.channel, self.app_id, self.bot_account)
        ):
            raise ValueError('Signing key must have an explicit channel/app/bot scope')


@dataclass(frozen=True)
class ServiceIdentity:
    key_id: str
    channel: str
    app_id: str
    bot_account: str


class NonceStore(Protocol):
    async def set(self, key: str, value: str, *, nx: bool, ex: int) -> bool | None: ...


def _unauthorized() -> ApiProblem:
    return ApiProblem(401, 'BOT_AUTH_FAILED', '机器人服务身份验证失败')


async def verify_service_request(
    headers: Mapping[str, str],
    method: str,
    path: str,
    body: bytes,
    *,
    keys: Mapping[str, SigningKey],
    nonce_store: NonceStore,
    now: float | None = None,
) -> ServiceIdentity:
    if not isinstance(body, bytes):
        raise _unauthorized()
    if len(body) > MAX_BODY:
        raise ApiProblem(413, 'BODY_TOO_LARGE', '机器人请求超过大小限制')
    if path not in _PATHS or method not in {'POST', 'GET'}:
        raise _unauthorized()
    values = {}
    for name, value in headers.items():
        normalized = name.lower()
        if normalized in values:
            raise _unauthorized()
        values[normalized] = value
    key_id = values.get('x-bot-key-id', '')
    timestamp = values.get('x-bot-timestamp', '')
    nonce = values.get('x-bot-nonce', '')
    signature = values.get('x-bot-signature', '')
    if not all(isinstance(value, str) for value in (key_id, timestamp, nonce, signature)):
        raise _unauthorized()
    if (
        not re.fullmatch(r'[1-9][0-9]{8,11}', timestamp)
        or not re.fullmatch(r'[A-Za-z0-9_-]{16,128}', nonce)
        or not re.fullmatch(r'[0-9a-f]{64}', signature)
    ):
        raise _unauthorized()
    clock = time.time() if now is None else now
    if abs(clock - int(timestamp)) > WINDOW_SECONDS:
        raise _unauthorized()
    key = keys.get(key_id)
    if not isinstance(key, SigningKey):
        raise _unauthorized()
    material = '\n'.join((method, path, timestamp, nonce, hashlib.sha256(body).hexdigest())).encode('utf-8')
    expected = hmac.new(key.secret, material, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise _unauthorized()
    digest = hashlib.sha256(f'{key_id}:{nonce}'.encode()).hexdigest()
    try:
        # A future timestamp can remain valid for another full window. Retain
        # the nonce for BOTH windows, not merely 300 seconds from first use.
        claimed = await nonce_store.set(f'integration:bot:nonce:{digest}', '1', nx=True, ex=2 * WINDOW_SECONDS + 1)
    except Exception:
        raise ApiProblem(503, 'BOT_AUTH_UNAVAILABLE', '机器人身份服务暂时不可用') from None
    if not claimed:
        raise ApiProblem(409, 'BOT_REPLAY_REJECTED', '重复机器人请求已拒绝')
    return ServiceIdentity(key_id, key.channel, key.app_id, key.bot_account)

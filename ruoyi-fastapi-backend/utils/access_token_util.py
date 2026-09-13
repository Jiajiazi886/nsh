"""Strict JWT parsing shared by legacy and versioned API authentication."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from exceptions.exception import AuthException

_JWT = re.compile(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')
_SESSION = re.compile(r'[A-Za-z0-9_-]{1,128}')
_USER_ID = re.compile(r'[1-9][0-9]*')
_MAX_ID = (1 << 63) - 1
_MAX_TOKEN_BYTES = 16384


def _invalid_token() -> AuthException:
    return AuthException(data='', message='登录令牌无效或已过期，请重新登录')


def bearer_access_token(value: str | None) -> str:
    """Only Authorization headers with an explicit Bearer scheme are accepted."""
    if not isinstance(value, str) or len(value) > _MAX_TOKEN_BYTES:
        raise _invalid_token()
    scheme, separator, token = value.partition(' ')
    if scheme.lower() != 'bearer' or separator != ' ' or not _JWT.fullmatch(token):
        raise _invalid_token()
    return token


@dataclass(frozen=True)
class ValidatedAccessToken:
    token: str
    user_id: int
    session_id: str
    payload: dict[str, Any]


def decode_access_token(value: str | None, key: str, algorithm: str) -> ValidatedAccessToken:
    """Accept OAuth2's already-extracted token, or a strictly formed Bearer header."""
    if not isinstance(value, str) or len(value) > _MAX_TOKEN_BYTES:
        raise _invalid_token()
    token = value if _JWT.fullmatch(value) else bearer_access_token(value)
    try:
        payload = jwt.decode(token, key, algorithms=[algorithm], options={'require': ['exp', 'user_id', 'session_id']})
        user_id = payload['user_id']
        if isinstance(user_id, bool) or not isinstance(user_id, (int, str)) or not _USER_ID.fullmatch(str(user_id)):
            raise ValueError('Invalid account identifier')
        user_id = int(user_id)
        if user_id > _MAX_ID:
            raise ValueError('Account identifier out of range')
        session_id = payload['session_id']
        if not isinstance(session_id, str) or not _SESSION.fullmatch(session_id):
            raise ValueError('Invalid session identifier')
        expires = payload['exp']
        if isinstance(expires, bool) or not isinstance(expires, (int, float)):
            raise ValueError('Invalid expiration')
    except (InvalidTokenError, TypeError, ValueError, OverflowError) as exc:
        raise _invalid_token() from exc
    return ValidatedAccessToken(token=token, user_id=user_id, session_id=session_id, payload=payload)

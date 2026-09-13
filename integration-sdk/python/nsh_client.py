"""Dependency-free v1 account client. Not a bot service-authentication client."""

import json
import re
from collections.abc import Callable
from email.message import Message
from typing import Any, BinaryIO
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

Transport = Callable[[str, str, dict[str, str], dict[str, Any] | None], tuple[int, dict[str, Any]]]
HTTP_OK = 200
HTTP_SUCCESS_LIMIT = 300
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_MEMBER_ID = 2**63 - 1


class ApiError(Exception):
    def __init__(self, message: str, status: int, error_key: str, request_id: str | None = None) -> None:
        super().__init__(message)
        self.status, self.error_key, self.request_id = status, error_key, request_id


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, request: Request, file: BinaryIO, code: int, message: str, headers: Message, new_url: str
    ) -> None:
        return None


def urllib_transport(
    method: str, url: str, headers: dict[str, str], data: dict[str, Any] | None
) -> tuple[int, dict[str, Any]]:
    payload = None if data is None else json.dumps(data, ensure_ascii=False).encode('utf-8')
    request = Request(url, method=method, headers=headers, data=payload)
    opener = build_opener(_NoRedirect())
    try:
        response = opener.open(request, timeout=15)
    except HTTPError as exc:
        response = exc
    with response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ApiError('响应超过大小限制', response.code, 'INVALID_RESPONSE')
        try:
            body = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ApiError('服务器返回了无法识别的响应', response.code, 'INVALID_RESPONSE') from None
        return response.code, body


class ApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        token_provider: Callable[[], str | None] | None = None,
        transport: Transport | None = None,
    ) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in {'https', 'http'}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or re.search(r'/api/v1/?$', parsed.path)
        ):
            raise ValueError('base_url must be an absolute API root without credentials/query/version prefix')
        self._root = base_url.rstrip('/') + '/api/v1'
        self._token_provider = token_provider or (lambda: None)
        self._transport = transport or urllib_transport

    def _request(
        self, method: str, path: str, data: dict[str, Any] | None = None, *, authenticated: bool = True
    ) -> Any:
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if authenticated:
            token = self._token_provider()
            if token:
                headers['Authorization'] = f'Bearer {token}'
        try:
            status, body = self._transport(method, self._root + path, headers, data)
        except ApiError:
            raise
        except Exception:
            raise ApiError('网络请求失败', 0, 'NETWORK_ERROR') from None
        if not isinstance(body, dict) or type(body.get('code')) is not int or type(body.get('success')) is not bool:
            raise ApiError('服务器返回了无法识别的响应', status, 'INVALID_RESPONSE')
        if not HTTP_OK <= status < HTTP_SUCCESS_LIMIT or body['success'] is not True or body['code'] != HTTP_OK:
            raise ApiError(
                body.get('msg') or '请求失败', status, body.get('errorKey') or 'API_ERROR', body.get('requestId')
            )
        return body.get('data')

    def capabilities(self) -> Any:
        return self._request('GET', '/capabilities', authenticated=False)

    def auth_config(self) -> Any:
        return self._request('GET', '/auth/config', authenticated=False)

    def captcha(self) -> Any:
        return self._request('GET', '/auth/captcha', authenticated=False)

    def login(self, user_name: str, password: str, *, code: str = '', uuid: str = '') -> Any:
        return self._request(
            'POST',
            '/auth/login',
            {'userName': user_name, 'password': password, 'code': code, 'uuid': uuid},
            authenticated=False,
        )

    def me(self) -> Any:
        return self._request('GET', '/auth/me')

    def logout(self) -> Any:
        return self._request('POST', '/auth/logout')

    def _choice(self, invite_code: str, member_id: str, kind: str, fields: dict[str, Any]) -> Any:
        if (
            not isinstance(member_id, str)
            or not re.fullmatch(r'[1-9][0-9]{0,18}', member_id)
            or int(member_id) > MAX_MEMBER_ID
        ):
            raise ValueError('member_id must be a bounded positive decimal string')
        if not isinstance(invite_code, str) or not invite_code:
            raise ValueError('invite_code must be a non-empty string')
        return self._request(
            'POST', f'/invitations/{quote(invite_code, safe="")}/{kind}', {'memberId': member_id, **fields}
        )

    def leave(self, invite_code: str, member_id: str, *, remark: str = '') -> Any:
        return self._choice(invite_code, member_id, 'leave', {'remark': remark})

    def signup(
        self, invite_code: str, member_id: str, *, player_class: str = '', secondary_class: str = '', remark: str = ''
    ) -> Any:
        return self._choice(
            invite_code,
            member_id,
            'signup',
            {'playerClass': player_class, 'secondaryClass': secondary_class, 'remark': remark},
        )

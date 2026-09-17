"""v1-only contract: never rewrites the legacy response envelope."""

import re
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator
from pydantic.alias_generators import to_camel
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from exceptions.exception import AuthException, LoginException, PermissionException, ServiceException
from utils.log_util import logger


class ApiProblem(Exception):
    def __init__(self, status: int, key: str, message: str) -> None:
        self.status, self.key, self.message = status, key, message


def request_id(request: Request) -> str:
    if not getattr(request.state, 'integration_request_id', None):
        # Generate locally; never trust arbitrary client headers in logs/responses.
        request.state.integration_request_id = f'req_{uuid.uuid4().hex}'
    return request.state.integration_request_id


def api_response(
    request: Request, data: Any = None, *, status: int = 200, message: str = '操作成功', key: str | None = None
) -> JSONResponse:
    rid = request_id(request)
    body = {'code': status, 'msg': message, 'success': status < 400, 'requestId': rid, 'data': data}
    if key:
        body['errorKey'] = key
    headers = {'X-Request-ID': rid, 'Cache-Control': 'no-store'}
    if status == 401:
        headers['WWW-Authenticate'] = 'Bearer'
    return JSONResponse(status_code=status, content=body, headers=headers)


class IntegrationRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def handle(request: Request) -> Response:
            request_id(request)
            try:
                return await original(request)
            except ApiProblem as exc:
                return api_response(request, status=exc.status, key=exc.key, message=exc.message)
            except (AuthException, LoginException):
                return api_response(request, status=401, key='AUTH_REQUIRED', message='请重新登录')
            except PermissionException as exc:
                data = exc.data if isinstance(exc.data, dict) else {}
                key = data.get('errorKey', 'FORBIDDEN')
                return api_response(request, status=403, key=key, message=exc.message or '无权操作')
            except ServiceException as exc:
                data = exc.data if isinstance(exc.data, dict) else {}
                key = data.get('errorKey', 'BUSINESS_RULE_FAILED')
                code = (
                    404
                    if key == 'INVITE_NOT_FOUND'
                    else 409
                    if key in {'REGISTRATION_EXISTS', 'INVITE_INACTIVE'}
                    else 422
                )
                return api_response(request, status=code, key=key, message=exc.message or '操作不符合业务规则')
            except RequestValidationError:
                # Do not echo input: validation errors can contain tokens/passwords.
                return api_response(request, status=422, key='VALIDATION_FAILED', message='请求参数格式不正确')
            except HTTPException as exc:
                keys = {401: 'AUTH_REQUIRED', 403: 'FORBIDDEN', 404: 'NOT_FOUND', 429: 'RATE_LIMITED'}
                return api_response(
                    request, status=exc.status_code, key=keys.get(exc.status_code, 'HTTP_ERROR'), message='请求未能完成'
                )
            except Exception as exc:
                logger.error(f'v1 request failed requestId={request_id(request)} type={type(exc).__name__}')
                return api_response(request, status=500, key='INTERNAL_ERROR', message='服务暂时无法完成请求')

        return handle


class ApiEnvelope(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)
    code: int
    msg: str
    success: bool
    request_id: str
    data: Any = None
    error_key: str | None = None


class MemberChoice(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, alias_generator=to_camel)
    member_id: str = Field(description='本人已绑定的成员 ID；十进制字符串', max_length=19)
    remark: str = Field(default='', max_length=500)

    @field_validator('member_id')
    @classmethod
    def validate_member_id(cls, value: str) -> str:
        if not re.fullmatch(r'[1-9][0-9]{0,18}', value) or int(value) > 2**63 - 1:
            raise ValueError('Invalid member ID')
        return value


class SignupChoice(MemberChoice):
    player_class: str = Field(default='', max_length=50)
    secondary_class: str = Field(default='', max_length=50)


class AccountLogin(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, alias_generator=to_camel)
    user_name: str = Field(min_length=1, max_length=50)
    password: SecretStr = Field(min_length=1, max_length=256)
    code: str = Field(default='', max_length=32)
    uuid: str = Field(default='', max_length=128)


class AccountRegister(AccountLogin):
    user_name: str = Field(min_length=2, max_length=20)
    password: SecretStr = Field(min_length=5, max_length=20)
    confirm_password: SecretStr = Field(min_length=5, max_length=20)

    @field_validator('user_name')
    @classmethod
    def valid_name(cls, value: str) -> str:
        if not value.strip() or any(char in value for char in '<>'):
            raise ValueError('Invalid account name')
        return value

    @model_validator(mode='after')
    def valid_passwords(self) -> 'AccountRegister':
        password = self.password.get_secret_value()
        if password != self.confirm_password.get_secret_value():
            raise ValueError('Passwords do not match')
        if any(char in password for char in '<>"\'|\\'):
            raise ValueError('Invalid password')
        return self

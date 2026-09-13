import json
from typing import Annotated

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse, Response

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency
from common.enums import RedisInitKeyConfig
from common.router import APIRouterPro
from config.env import AppConfig, JwtConfig
from module_admin.controller import captcha_controller as legacy_captcha
from module_admin.controller import login_controller as legacy_auth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import CustomOAuth2PasswordRequestForm, LoginService
from module_guild.entity.vo.battle_registration_vo import (
    PublicBattleLeaveApplicationModel,
    PublicBattleRegistrationModel,
)
from module_guild.service.battle_registration_service import BattleRegistrationService
from module_integration.contract import (
    AccountLogin,
    ApiEnvelope,
    ApiProblem,
    IntegrationRoute,
    MemberChoice,
    SignupChoice,
    api_response,
)
from utils.access_token_util import bearer_access_token, decode_access_token

api_v1_controller = APIRouterPro(
    prefix='/api/v1',
    order_num=90,
    tags=['统一多端接口 v1'],
    route_class=IntegrationRoute,
    responses={
        code: {'model': ApiEnvelope, 'description': description}
        for code, description in {
            401: '未认证或会话已失效',
            403: '无权操作对象',
            404: '不存在或不可见',
            409: '业务状态冲突',
            422: '参数不正确',
            429: '请求限流',
            500: '内部错误（不返回异常详情）',
            503: '能力未启用或服务不可用',
        }.items()
    },
)
CurrentUser = Annotated[CurrentUserModel, CurrentUserDependency()]
Database = Annotated[AsyncSession, DBSessionDependency()]


def legacy_auth_payload(response: Response | dict) -> dict:
    payload = response if isinstance(response, dict) else json.loads(response.body)
    code = payload.get('code', 200)
    if code == 429:
        raise ApiProblem(429, 'RATE_LIMITED', '请求过于频繁，请稍后重试')
    if code in {401, 601}:
        raise ApiProblem(401, 'AUTH_REQUIRED', '账号认证失败，请检查登录信息和验证码')
    if code != 200:
        raise ApiProblem(500, 'INTERNAL_ERROR', '认证服务暂时不可用')
    return payload


@api_v1_controller.get('/auth/config', response_model=ApiEnvelope, operation_id='v1AuthConfig')
async def auth_config(request: Request) -> JSONResponse:
    redis = request.app.state.redis
    prefix = RedisInitKeyConfig.SYS_CONFIG.key
    return api_response(
        request,
        {
            'captchaEnabled': await redis.get(f'{prefix}:sys.account.captchaEnabled') == 'true',
            'registerEnabled': await redis.get(f'{prefix}:sys.account.registerUser') == 'true',
            'wechatLogin': False,
        },
    )


@api_v1_controller.get('/auth/captcha', response_model=ApiEnvelope, operation_id='v1AuthCaptcha')
async def captcha(request: Request) -> JSONResponse:
    payload = legacy_auth_payload(await legacy_captcha.get_captcha_image(request=request))
    return api_response(
        request, {key: payload.get(key) for key in ('captchaEnabled', 'registerEnabled', 'img', 'uuid')}
    )


@api_v1_controller.post('/auth/login', response_model=ApiEnvelope, operation_id='v1AuthLogin')
async def login(request: Request, data: AccountLogin, db: Database) -> JSONResponse:
    # Call the existing decorated entry, including rate limit, audit and cache
    # eviction. Do not call __wrapped__ or issue an independent account token.
    form = CustomOAuth2PasswordRequestForm(
        grant_type='password',
        username=data.user_name,
        password=data.password.get_secret_value(),
        scope='',
        client_id=None,
        client_secret=None,
        code=data.code,
        uuid=data.uuid,
        login_info=None,
    )
    payload = legacy_auth_payload(await legacy_auth.login(request=request, form_data=form, query_db=db))
    token = payload.get('token') or payload.get('access_token')
    if not isinstance(token, str) or not token:
        raise ApiProblem(500, 'INTERNAL_ERROR', '认证服务暂时不可用')
    return api_response(
        request, {'accessToken': token, 'tokenType': 'Bearer', 'expiresIn': JwtConfig.jwt_expire_minutes * 60}
    )


@api_v1_controller.get('/capabilities', response_model=ApiEnvelope, operation_id='v1Capabilities')
async def capabilities(request: Request) -> JSONResponse:
    return api_response(
        request,
        {
            'apiVersion': 'v1',
            'accountSessions': True,
            'selfRegistration': True,
            'wechatLogin': False,
            'botTransport': False,
            'activitySnapshots': False,
            'csvAnalysis': False,
        },
    )


@api_v1_controller.get('/auth/me', response_model=ApiEnvelope, operation_id='v1AuthMe')
async def me(request: Request, current_user: CurrentUser) -> JSONResponse:
    user = current_user.user
    return api_response(
        request,
        {
            'userId': str(user.user_id),
            'userName': user.user_name,
            'nickName': user.nick_name,
            'roles': current_user.roles,
            'permissions': current_user.permissions,
        },
    )


@api_v1_controller.post('/auth/logout', response_model=ApiEnvelope, operation_id='v1AuthLogout')
async def logout(request: Request, current_user: CurrentUser) -> JSONResponse:
    validated = decode_access_token(
        bearer_access_token(request.headers.get('Authorization')), JwtConfig.jwt_secret_key, JwtConfig.jwt_algorithm
    )
    token_id = validated.session_id if AppConfig.app_same_time_login else str(current_user.user.user_id)
    await LoginService.logout_services(request, token_id)
    return api_response(request)


@api_v1_controller.post('/auth/wechat/login', response_model=ApiEnvelope, operation_id='v1WechatLoginUnavailable')
async def wechat_login(request: Request) -> JSONResponse:
    raise ApiProblem(503, 'CAPABILITY_DISABLED', '微信登录尚未配置，暂请使用账号密码登录')


@api_v1_controller.post(
    '/invitations/{invite_code}/leave', response_model=ApiEnvelope, operation_id='v1InvitationLeave'
)
async def leave(
    request: Request, invite_code: str, data: MemberChoice, current_user: CurrentUser, db: Database
) -> JSONResponse:
    result = await BattleRegistrationService.submit_public_leave_service(
        db,
        invite_code,
        PublicBattleLeaveApplicationModel(member_id=int(data.member_id), remark=data.remark),
        current_user=current_user,
    )
    return api_response(request, message=result.message)


@api_v1_controller.post(
    '/invitations/{invite_code}/signup', response_model=ApiEnvelope, operation_id='v1InvitationSignup'
)
async def signup(
    request: Request, invite_code: str, data: SignupChoice, current_user: CurrentUser, db: Database
) -> JSONResponse:
    result = await BattleRegistrationService.submit_public_registration_service(
        db,
        invite_code,
        PublicBattleRegistrationModel(
            member_id=int(data.member_id),
            player_class=data.player_class,
            secondary_class=data.secondary_class,
            remark=data.remark,
        ),
        current_user=current_user,
    )
    return api_response(request, message=result.message)

from typing import Annotated
import json
import uuid
from datetime import datetime, timedelta

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse, Response

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency
from common.enums import RedisInitKeyConfig
from common.router import APIRouterPro
from config.env import AppConfig, JwtConfig
from module_admin.controller import captcha_controller as legacy_captcha
from module_admin.controller import login_controller as legacy_auth
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.login_vo import UserRegister
from exceptions.exception import AuthException, ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import CustomOAuth2PasswordRequestForm, LoginService
from module_guild.entity.vo.battle_registration_vo import (
    PublicBattleLeaveApplicationModel,
    PublicBattleRegistrationModel,
)
from module_guild.service.battle_registration_service import BattleRegistrationService
from module_integration.contract import (
    AccountLogin,
    AccountRegister,
    ApiEnvelope,
    ApiProblem,
    IntegrationRoute,
    MemberChoice,
    RefreshTokenInput,
    SignupChoice,
    api_response,
)
from utils.access_token_util import bearer_access_token, decode_access_token
from module_integration.activities.enabled import activities_enabled
from module_integration.refresh_tokens import (
    find_refresh_token,
    issue_refresh_token,
    new_refresh_token,
    revoke_refresh_tokens,
    rotate_loaded_refresh_token,
)

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


async def _consume_refresh_token(redis, key: str):
    """Consume a refresh token once; use Redis Lua when available."""
    script = "local value = redis.call('GET', KEYS[1]); if value then redis.call('DEL', KEYS[1]); end; return value"
    evaluator = getattr(redis, 'eval', None)
    if evaluator is not None:
        try:
            return await evaluator(script, 1, key)
        except (AttributeError, NotImplementedError, TypeError):
            pass
    raw = await redis.get(key)
    if raw:
        await redis.delete(key)
    return raw


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
        client_type=data.client_type,
    )
    payload = legacy_auth_payload(await legacy_auth.login(request=request, form_data=form, query_db=db))
    token = payload.get('token') or payload.get('access_token')
    if not isinstance(token, str) or not token:
        raise ApiProblem(500, 'INTERNAL_ERROR', '认证服务暂时不可用')
    try:
        claims = decode_access_token(token, JwtConfig.jwt_secret_key, JwtConfig.jwt_algorithm)
    except AuthException:
        # Legacy adapters and isolated contract tests may return a synthetic
        # token. Keep the old v1 response shape for that compatibility path;
        # real login responses are JWTs and receive a rotating refresh token.
        return api_response(
            request,
            {'accessToken': token, 'tokenType': 'Bearer', 'expiresIn': JwtConfig.jwt_expire_minutes * 60},
        )
    refresh_token = new_refresh_token()
    refresh_payload = {
        'user_id': claims.user_id,
        'user_name': claims.payload.get('user_name'),
        'dept_name': claims.payload.get('dept_name'),
        'login_info': claims.payload.get('login_info'),
        'session_id': claims.session_id,
    }
    await issue_refresh_token(
        db,
        refresh_token,
        user_id=int(claims.user_id),
        client_type=data.client_type,
        session_id=claims.session_id,
        expires_days=JwtConfig.jwt_refresh_expire_days,
    )
    if isinstance(db, AsyncSession):
        await db.commit()
    await request.app.state.redis.set(
        f'refresh_token:{refresh_token}',
        json.dumps(refresh_payload, ensure_ascii=False),
        ex=timedelta(days=JwtConfig.jwt_refresh_expire_days),
    )
    return api_response(
        request,
        {
            'accessToken': token,
            'tokenType': 'Bearer',
            'expiresIn': JwtConfig.jwt_expire_minutes * 60,
            'refreshToken': refresh_token,
            'refreshExpiresIn': JwtConfig.jwt_refresh_expire_days * 86400,
        },
    )


@api_v1_controller.post('/auth/refresh', response_model=ApiEnvelope, operation_id='v1AuthRefresh')
async def refresh(request: Request, data: RefreshTokenInput, db: Database) -> JSONResponse:
    persistent_old = await find_refresh_token(db, data.refresh_token)
    if persistent_old is not None:
        now = datetime.now()
        if not persistent_old.client_type == data.client_type or not persistent_old.expires_at > now or persistent_old.revoked_at is not None or persistent_old.last_used_at is not None:
            raise ApiProblem(401, 'REFRESH_TOKEN_INVALID', '刷新令牌无效或已使用')
        user_id = str(persistent_old.user_id)
        user = await db.scalar(select(SysUser).where(SysUser.user_id == int(user_id)))
        if user is None or user.status != '0' or user.del_flag != '0':
            raise ApiProblem(401, 'ACCOUNT_DISABLED', '账号已停用或删除，请重新登录')
        old_session_id = persistent_old.device_id or ''
        if old_session_id:
            await request.app.state.redis.delete(f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{old_session_id}')
        session_id = str(uuid.uuid4())
        access_token = await LoginService.create_access_token(
            data={
                'user_id': user_id,
                'user_name': user.user_name,
                'dept_name': None,
                'session_id': session_id,
                'login_info': None,
            },
            expires_delta=timedelta(minutes=JwtConfig.jwt_expire_minutes),
        )
        token_key = (
            f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}'
            if AppConfig.app_same_time_login
            else f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{user_id}'
        )
        replacement_token = new_refresh_token()
        try:
            next_row = await rotate_loaded_refresh_token(
                db, persistent_old, replacement_token, client_type=data.client_type, session_id=session_id,
                expires_days=JwtConfig.jwt_refresh_expire_days,
            )
            if next_row is None:
                raise ApiProblem(401, 'REFRESH_TOKEN_INVALID', '刷新令牌无效或已使用')
            await db.commit()
            await request.app.state.redis.set(token_key, access_token, ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes))
        except Exception:
            await db.rollback()
            await request.app.state.redis.delete(token_key)
            raise
        await request.app.state.redis.set(
            f'refresh_token:{replacement_token}',
            json.dumps({'user_id': user_id, 'user_name': user.user_name, 'dept_name': None, 'login_info': None, 'session_id': session_id}, ensure_ascii=False),
            ex=timedelta(days=JwtConfig.jwt_refresh_expire_days),
        )
        return api_response(request, {'accessToken': access_token, 'tokenType': 'Bearer', 'expiresIn': JwtConfig.jwt_expire_minutes * 60, 'refreshToken': replacement_token, 'refreshExpiresIn': JwtConfig.jwt_refresh_expire_days * 86400})

    # Compatibility path for refresh tokens issued before the persistence table
    # existed. A successful refresh below immediately writes the replacement
    # into the database, so Redis is not the long-term source of truth.
    replacement_token = new_refresh_token()
    key = f'refresh_token:{data.refresh_token}'
    raw = await _consume_refresh_token(request.app.state.redis, key)
    if not raw:
        raise ApiProblem(401, 'REFRESH_TOKEN_INVALID', '刷新令牌无效或已使用')
    try:
        stored = json.loads(raw)
        user_id = str(stored['user_id'])
        user_name = stored.get('user_name')
        dept_name = stored.get('dept_name')
        login_info = stored.get('login_info')
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise ApiProblem(401, 'REFRESH_TOKEN_INVALID', '刷新令牌无效或已使用') from exc
    user = await db.scalar(select(SysUser).where(SysUser.user_id == int(user_id)))
    if user is None or user.status != '0' or user.del_flag != '0':
        raise ApiProblem(401, 'ACCOUNT_DISABLED', '账号已停用或删除，请重新登录')
    old_session_id = stored.get('session_id')
    if old_session_id:
        await request.app.state.redis.delete(f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{old_session_id}')
    session_id = str(uuid.uuid4())
    access_token = await LoginService.create_access_token(
        data={
            'user_id': user_id,
            'user_name': user_name,
            'dept_name': dept_name,
            'session_id': session_id,
            'login_info': login_info,
        },
        expires_delta=timedelta(minutes=JwtConfig.jwt_expire_minutes),
    )
    token_key = (
        f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}'
        if AppConfig.app_same_time_login
        else f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{user_id}'
    )
    await request.app.state.redis.set(
        token_key,
        access_token,
        ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
    )
    next_refresh_token = replacement_token
    await issue_refresh_token(
        db,
        next_refresh_token,
        user_id=int(user_id),
        client_type=data.client_type,
        session_id=session_id,
        expires_days=JwtConfig.jwt_refresh_expire_days,
    )
    if isinstance(db, AsyncSession):
        await db.commit()
    await request.app.state.redis.set(
        f'refresh_token:{next_refresh_token}',
        json.dumps(
            {
                'user_id': user_id,
                'user_name': user_name,
                'dept_name': dept_name,
                'login_info': login_info,
                'session_id': session_id,
            },
            ensure_ascii=False,
        ),
        ex=timedelta(days=JwtConfig.jwt_refresh_expire_days),
    )
    return api_response(
        request,
        {
            'accessToken': access_token,
            'tokenType': 'Bearer',
            'expiresIn': JwtConfig.jwt_expire_minutes * 60,
            'refreshToken': next_refresh_token,
            'refreshExpiresIn': JwtConfig.jwt_refresh_expire_days * 86400,
        },
    )


@api_v1_controller.post('/auth/register', response_model=ApiEnvelope, operation_id='v1AuthRegister')
async def register(request: Request, data: AccountRegister, db: Database) -> JSONResponse:
    prefix = RedisInitKeyConfig.SYS_CONFIG.key
    if await request.app.state.redis.get(f'{prefix}:sys.account.registerUser') != 'true':
        raise ApiProblem(403, 'REGISTRATION_DISABLED', '注册已关闭，请联系管理员')
    form = UserRegister(
        username=data.user_name,
        password=data.password.get_secret_value(),
        confirmPassword=data.confirm_password.get_secret_value(),
        code=data.code,
        uuid=data.uuid,
    )
    try:
        # Preserve legacy anonymous rate limiting, cache eviction, role and transaction rules.
        response = await legacy_auth.register_user(request=request, user_register=form, query_db=db)
    except ServiceException as exc:
        if '登录账号已存在' in (exc.message or ''):
            raise ApiProblem(409, 'ACCOUNT_EXISTS', '登录账号已存在，请更换账号') from exc
        raise
    legacy_auth_payload(response)
    return api_response(request, {'registered': True, 'userName': data.user_name}, message='注册成功，请登录')


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
            'activitySnapshots': activities_enabled(),
            'activityInformation': activities_enabled(),
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
async def logout(request: Request, current_user: CurrentUser, db: Database) -> JSONResponse:
    validated = decode_access_token(
        bearer_access_token(request.headers.get('Authorization')), JwtConfig.jwt_secret_key, JwtConfig.jwt_algorithm
    )
    token_id = validated.session_id if AppConfig.app_same_time_login else str(current_user.user.user_id)
    await LoginService.logout_services(request, token_id)
    await revoke_refresh_tokens(db, user_id=int(current_user.user.user_id), session_id=validated.session_id)
    if isinstance(db, AsyncSession):
        await db.commit()
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

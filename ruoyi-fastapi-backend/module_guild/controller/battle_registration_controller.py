from typing import Annotated

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_guild.entity.vo.battle_registration_vo import (
    BattleInviteCreateModel,
    BattleRegistrationReviewModel,
    PublicBattleJoinApplicationModel,
    PublicBattleRegistrationModel,
)
from module_guild.service.battle_registration_service import BattleRegistrationService
from utils.log_util import logger
from utils.response_util import ResponseUtil

battle_registration_controller = APIRouterPro(
    prefix='/guild/battle-registration',
    order_num=26,
    tags=['帮会管理-约战报名审核'],
    dependencies=[PreAuthDependency()],
)

public_battle_registration_controller = APIRouterPro(
    prefix='/public/battle',
    order_num=27,
    tags=['公开约战报名'],
)


@battle_registration_controller.post(
    '/invite',
    summary='创建约战临时链接',
    dependencies=[UserInterfaceAuthDependency('guild:review:battle:list')],
)
async def create_invite(
    data: BattleInviteCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.create_invite_service(query_db, current_user, data)
        return ResponseUtil.success(data=result, msg='创建成功')
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'创建约战临时链接失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@battle_registration_controller.get(
    '/invite/list',
    summary='查看约战临时链接',
    dependencies=[UserInterfaceAuthDependency('guild:review:battle:list')],
)
async def list_invites(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.list_invites_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'查看约战临时链接失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@battle_registration_controller.get(
    '/list',
    summary='查看约战报名审核列表',
    dependencies=[UserInterfaceAuthDependency('guild:review:battle:list')],
)
async def list_registrations(
    status: str | None = None,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.list_registrations_service(query_db, current_user, status)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'查看约战报名审核列表失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@battle_registration_controller.get(
    '/approved-schedule-list',
    summary='排表读取已通过约战报名',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:list')],
)
async def list_approved_schedule_registrations(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.list_registrations_service(query_db, current_user, '1')
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'排表读取已通过约战报名失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@battle_registration_controller.post('/approve', summary='通过约战报名')
async def approve_registration(
    data: BattleRegistrationReviewModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.approve_registration_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'通过约战报名失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@battle_registration_controller.post('/reject', summary='拒绝约战报名')
async def reject_registration(
    data: BattleRegistrationReviewModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.reject_registration_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'拒绝约战报名失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@public_battle_registration_controller.get('/{invite_code}', summary='查看公开约战链接')
async def get_public_invite(
    invite_code: str,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.get_public_invite_service(query_db, invite_code)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'查看公开约战链接失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@public_battle_registration_controller.get('/{invite_code}/members', summary='公开搜索帮会成员')
async def search_public_members(
    invite_code: str,
    keyword: str = '',
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.search_public_members_service(query_db, invite_code, keyword)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'公开搜索帮会成员失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@public_battle_registration_controller.get('/{invite_code}/professions', summary='公开获取职业选项')
async def get_public_professions(
    invite_code: str,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.get_public_profession_options_service(query_db, invite_code)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'公开获取职业选项失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@public_battle_registration_controller.post('/{invite_code}/signup', summary='公开提交约战报名')
async def submit_public_registration(
    invite_code: str,
    data: PublicBattleRegistrationModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.submit_public_registration_service(query_db, invite_code, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'公开提交约战报名失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@public_battle_registration_controller.post('/{invite_code}/join', summary='公开提交入会申请')
async def submit_public_join(
    invite_code: str,
    data: PublicBattleJoinApplicationModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    try:
        result = await BattleRegistrationService.submit_public_join_service(query_db, invite_code, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'公开提交入会申请失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')

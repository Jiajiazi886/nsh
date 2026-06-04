from typing import Annotated

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from exceptions.exception import ServiceException
from module_guild.entity.vo.member_vo import (
    MemberBatchDeleteModel,
    MemberCreateModel,
    MemberEditModel,
    MemberImportModel,
    MemberProfileEditModel,
)
from module_guild.service.member_service import MemberService
from utils.log_util import logger
from utils.response_util import ResponseUtil

member_controller = APIRouterPro(
    prefix='/guild/member', order_num=21, tags=['帮会管理-成员管理'], dependencies=[PreAuthDependency()]
)

@member_controller.get('/list', summary='获取成员列表', dependencies=[UserInterfaceAuthDependency('guild:member:list')])
async def get_member_list(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await MemberService.query_member_list_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'获取成员列表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@member_controller.post('', summary='添加帮会成员', dependencies=[UserInterfaceAuthDependency('guild:member:add')])
async def create_member(
    data: MemberCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await MemberService.create_member_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'添加成员失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@member_controller.get(
    '/my-profile',
    summary='查看当前登录用户自己的帮会成员资料',
    dependencies=[UserInterfaceAuthDependency('personal:profile:edit')],
)
async def get_my_member_profile(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await MemberService.get_my_profile_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'查看个人帮会资料失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@member_controller.put(
    '/my-profile',
    summary='修改当前登录用户自己的帮会成员资料',
    dependencies=[UserInterfaceAuthDependency('personal:profile:edit')],
)
async def update_my_member_profile(
    data: MemberProfileEditModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await MemberService.update_my_profile_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'修改个人帮会资料失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@member_controller.put('/{member_id}', summary='编辑成员信息', dependencies=[UserInterfaceAuthDependency('guild:member:edit')])
async def edit_member(
    member_id: int,
    data: MemberEditModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        data.member_id = member_id
        result = await MemberService.edit_member_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'编辑成员失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@member_controller.post(
    '/batch-delete', summary='批量删除成员', dependencies=[UserInterfaceAuthDependency('guild:member:remove')]
)
async def batch_delete_members(
    data: MemberBatchDeleteModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await MemberService.batch_delete_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'批量删除成员失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@member_controller.post(
    '/import-from-battle', summary='从历史数据导入成员', dependencies=[UserInterfaceAuthDependency('guild:member:import')]
)
async def import_from_battle(
    data: MemberImportModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await MemberService.import_from_battle_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'导入成员失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@member_controller.get(
    '/battle-list', summary='获取可导入的战斗列表', dependencies=[UserInterfaceAuthDependency('guild:member:import')]
)
async def get_battle_list(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await MemberService.get_battle_list_for_import_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'获取战斗列表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@member_controller.get(
    '/battle-guilds/{battle_id}',
    summary='获取战斗中帮会名列表',
    dependencies=[UserInterfaceAuthDependency('guild:member:import')],
)
async def get_battle_guilds(
    battle_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await MemberService.get_guild_names_for_battle_service(query_db, current_user, battle_id)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'获取帮会名列表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

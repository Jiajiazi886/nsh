from typing import Annotated

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_guild.entity.vo.join_application_vo import JoinApplicationCreateModel, JoinApplicationReviewModel
from module_guild.service.join_application_service import JoinApplicationService
from utils.log_util import logger
from utils.response_util import ResponseUtil

join_application_controller = APIRouterPro(
    prefix='/guild/join', order_num=22, tags=['帮会管理-入会申请'], dependencies=[PreAuthDependency()]
)


@join_application_controller.get('/search', summary='搜索帮会', dependencies=[UserInterfaceAuthDependency('personal:join:list')])
async def search_guilds(
    keyword: str = '',
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    try:
        result = await JoinApplicationService.search_guilds_service(query_db, keyword)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'搜索帮会失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@join_application_controller.post('/apply', summary='提交入会申请', dependencies=[UserInterfaceAuthDependency('personal:join:list')])
async def submit_application(
    data: JoinApplicationCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await JoinApplicationService.submit_application_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'提交入会申请失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@join_application_controller.get(
    '/my-status', summary='查看我的申请与当前归属', dependencies=[UserInterfaceAuthDependency('personal:join:list')]
)
async def get_my_status(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await JoinApplicationService.get_my_status_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'查询我的入会状态失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@join_application_controller.post('/quit', summary='主动退会', dependencies=[UserInterfaceAuthDependency('personal:join:quit')])
async def quit_guild(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await JoinApplicationService.quit_guild_service(query_db, current_user)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'主动退会失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@join_application_controller.get(
    '/pending', summary='查看待审核列表', dependencies=[UserInterfaceAuthDependency('guild:review:member:list')]
)
async def list_pending_applications(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await JoinApplicationService.list_pending_applications_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'查询待审核列表失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@join_application_controller.post(
    '/approve', summary='同意入会申请', dependencies=[UserInterfaceAuthDependency('guild:review:member:approve')]
)
async def approve_application(
    data: JoinApplicationReviewModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await JoinApplicationService.approve_application_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'同意入会申请失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')


@join_application_controller.post(
    '/reject', summary='拒绝入会申请', dependencies=[UserInterfaceAuthDependency('guild:review:member:reject')]
)
async def reject_application(
    data: JoinApplicationReviewModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[CurrentUserModel | None, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await JoinApplicationService.reject_application_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'拒绝入会申请失败: {e!s}')
        return ResponseUtil.error(msg=f'{e!s}')

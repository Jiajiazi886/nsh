from typing import Annotated

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from exceptions.exception import ServiceException
from module_guild.entity.vo.schedule_vo import (
    ScheduleAssignmentModel,
    ScheduleHistoryRenameModel,
    ScheduleSnapshotModel,
    ScheduleSquadCreateModel,
    ScheduleTeamCreateModel,
    ScheduleWorkbookModel,
)
from module_guild.service.schedule_service import ScheduleService
from utils.log_util import logger
from utils.response_util import ResponseUtil

schedule_controller = APIRouterPro(
    prefix='/guild/schedule', order_num=25, tags=['帮会管理-约战排表'], dependencies=[PreAuthDependency()]
)


@schedule_controller.get(
    '/current',
    summary='获取当前约战排表',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:list')],
)
async def get_current_schedule(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.get_current_schedule_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'获取约战排表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.get(
    '/history',
    summary='查询约战排表历史',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:history')],
)
async def list_schedule_history(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.list_history_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'查询约战排表历史失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.put(
    '/history/{schedule_id}/name',
    summary='修改历史约战排表名称',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:history')],
)
async def rename_schedule_history(
    schedule_id: int,
    data: ScheduleHistoryRenameModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.rename_history_service(query_db, current_user, schedule_id, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'修改历史约战排表名称失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.delete(
    '/history/{schedule_id}',
    summary='删除历史约战排表',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:history')],
)
async def delete_schedule_history(
    schedule_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.delete_history_service(query_db, current_user, schedule_id)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除历史约战排表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.get(
    '/current/workbook',
    summary='获取当前约战排表自由表格',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:list')],
)
async def get_current_schedule_workbook(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.get_current_workbook_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'获取约战排表自由表格失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.put(
    '/current/workbook',
    summary='保存当前约战排表自由表格',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:edit')],
)
async def save_current_schedule_workbook(
    data: ScheduleWorkbookModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.save_current_workbook_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'保存约战排表自由表格失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.get(
    '/{schedule_id}',
    summary='获取约战排表详情',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:query')],
)
async def get_schedule_detail(
    schedule_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.get_schedule_detail_service(query_db, current_user, schedule_id)
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取约战排表详情失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.post(
    '/team',
    summary='创建排表团队',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:team:add')],
)
async def create_schedule_team(
    data: ScheduleTeamCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.create_team_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'创建排表团队失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.delete(
    '/team/{team_id}',
    summary='删除排表团队',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:team:remove')],
)
async def delete_schedule_team(
    team_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.delete_team_service(query_db, current_user, team_id)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除排表团队失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.post(
    '/team/{team_id}/squad',
    summary='创建排表小队',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:squad:add')],
)
async def create_schedule_squad(
    team_id: int,
    data: ScheduleSquadCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.create_squad_service(query_db, current_user, team_id, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'创建排表小队失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.delete(
    '/team/{team_id}/squad/{squad_id}',
    summary='删除排表小队',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:squad:remove')],
)
async def delete_schedule_squad(
    team_id: int,
    squad_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.delete_squad_service(query_db, current_user, team_id, squad_id)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除排表小队失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.put(
    '/assignment',
    summary='保存成员排表位置',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:edit')],
)
async def assign_schedule_member(
    data: ScheduleAssignmentModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.assign_member_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'保存成员排表位置失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.delete(
    '/assignment/{member_id}',
    summary='移出成员排表',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:edit')],
)
async def clear_schedule_member(
    member_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.clear_assignment_service(query_db, current_user, member_id)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'移出成员排表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.post(
    '/snapshot',
    summary='保存约战排表历史',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:snapshot')],
)
async def create_schedule_snapshot(
    data: ScheduleSnapshotModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.create_snapshot_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'保存约战排表历史失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@schedule_controller.post(
    '/history/{schedule_id}/apply',
    summary='应用历史约战排表',
    dependencies=[UserInterfaceAuthDependency('guild:schedule:apply')],
)
async def apply_schedule_history(
    schedule_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ScheduleService.apply_history_service(query_db, current_user, schedule_id)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'应用历史约战排表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

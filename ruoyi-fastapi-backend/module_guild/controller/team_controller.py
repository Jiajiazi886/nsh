from typing import Annotated
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from exceptions.exception import ServiceException
from module_guild.entity.vo.team_vo import TeamCreateModel
from module_guild.service.team_service import TeamService
from utils.log_util import logger
from utils.response_util import ResponseUtil

team_controller = APIRouterPro(
    prefix='/guild/team', order_num=24, tags=['帮会管理-团队管理'], dependencies=[PreAuthDependency()]
)

@team_controller.get('/list', summary='获取团队列表')
async def list_teams(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await TeamService.list_teams_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'获取团队列表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@team_controller.post('/create', summary='创建团队', dependencies=[UserInterfaceAuthDependency('guild:team:edit')])
async def create_team(
    data: TeamCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await TeamService.create_team_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'创建团队失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@team_controller.delete('/{team_id}', summary='删除团队')
async def delete_team(
    team_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await TeamService.delete_team_service(query_db, current_user, team_id)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除团队失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))
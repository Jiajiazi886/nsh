from typing import Annotated

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from exceptions.exception import ServiceException
from module_guild.service.analysis_service import AnalysisService
from utils.log_util import logger
from utils.response_util import ResponseUtil

analysis_controller = APIRouterPro(
    prefix='/guild/analysis',
    order_num=26,
    tags=['帮会管理-数据分析'],
    dependencies=[PreAuthDependency()],
)


@analysis_controller.get(
    '/schedule-battle',
    summary='分析历史排表与约战数据',
    description='选择一份已导入约战数据，并可选一份历史排表进行匹配分析',
    dependencies=[UserInterfaceAuthDependency('guild:battle:list')],
)
async def analyze_schedule_battle(
    battle_id: int,
    schedule_id: int | None = None,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await AnalysisService.query_schedule_battle_analysis_service(
            query_db,
            current_user,
            battle_id,
            schedule_id,
        )
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'分析约战数据失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

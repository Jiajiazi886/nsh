from typing import Annotated

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_guild.service.dashboard_service import DashboardService
from utils.log_util import logger
from utils.response_util import ResponseUtil

dashboard_controller = APIRouterPro(
    prefix='/guild/dashboard', order_num=20, tags=['帮会管理-首页聚合'], dependencies=[PreAuthDependency()]
)


@dashboard_controller.get('/summary', summary='获取帮会首页真实数据聚合')
async def get_dashboard_summary(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await DashboardService.get_summary_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'获取帮会首页数据失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

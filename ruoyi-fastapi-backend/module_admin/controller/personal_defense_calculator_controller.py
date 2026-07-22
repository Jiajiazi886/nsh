from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel
from module_admin.entity.vo.pvp_attack_panel_vo import PvpAttackPanelModel
from module_admin.service.pvp_attack_panel_service import PvpAttackPanelService
from utils.response_util import ResponseUtil


personal_defense_calculator_controller = APIRouterPro(
    prefix='/personal/defense-calculator',
    order_num=92,
    tags=['个人管理-防守计算器'],
    dependencies=[PreAuthDependency()],
)


@personal_defense_calculator_controller.get(
    '/attack-panels',
    response_model=DataResponseModel[list[PvpAttackPanelModel]],
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
async def get_enabled_pvp_attack_panels(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await PvpAttackPanelService.get_enabled_services(query_db))

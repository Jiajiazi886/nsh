from typing import Annotated

from fastapi import Path, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import RoleInterfaceAuthDependency, UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, ResponseBaseModel
from module_admin.entity.vo.pvp_defense_profession_bonus_vo import ProfessionBonusModel, ProfessionBonusUpdateModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.pvp_defense_profession_bonus_service import PvpDefenseProfessionBonusService
from utils.response_util import ResponseUtil


pvp_defense_profession_bonus_controller = APIRouterPro(
    prefix='/system/pvp-defense-profession-bonus',
    order_num=11,
    tags=['系统管理-职业加成设置'],
    dependencies=[PreAuthDependency()],
)


@pvp_defense_profession_bonus_controller.get(
    '/list',
    response_model=DataResponseModel[list[ProfessionBonusModel]],
    dependencies=[
        UserInterfaceAuthDependency('system:pvp-defense-profession-bonus:list'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
async def list_profession_bonuses(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await PvpDefenseProfessionBonusService.list_services(query_db))


@pvp_defense_profession_bonus_controller.put(
    '/{profession_id}',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:pvp-defense-profession-bonus:edit'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@Log(title='职业加成设置', business_type=BusinessType.UPDATE)
async def update_profession_bonus(
    request: Request,
    profession_id: Annotated[int, Path(description='职业ID')],
    payload: ProfessionBonusUpdateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PvpDefenseProfessionBonusService.update_services(
        query_db, profession_id, payload, current_user.user.user_name
    )
    return ResponseUtil.success(msg=result.message)

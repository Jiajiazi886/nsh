from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import RoleInterfaceAuthDependency, UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.pvp_attack_panel_vo import (
    PvpAttackPanelModel,
    PvpAttackPanelQueryModel,
    PvpAttackPanelStatusModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.pvp_attack_panel_service import PvpAttackPanelService
from utils.response_util import ResponseUtil


pvp_attack_panel_controller = APIRouterPro(
    prefix='/system/pvp-attack-panel',
    order_num=10,
    tags=['系统管理-进攻方面板设置'],
    dependencies=[PreAuthDependency()],
)


@pvp_attack_panel_controller.get(
    '/list',
    response_model=PageResponseModel[PvpAttackPanelModel],
    dependencies=[UserInterfaceAuthDependency('system:pvp-attack-panel:list'), RoleInterfaceAuthDependency('admin')],
)
async def get_pvp_attack_panel_list(
    request: Request,
    query: Annotated[PvpAttackPanelQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(model_content=await PvpAttackPanelService.get_list_services(query_db, query))


@pvp_attack_panel_controller.get(
    '/{panel_id}',
    response_model=DataResponseModel[PvpAttackPanelModel],
    dependencies=[UserInterfaceAuthDependency('system:pvp-attack-panel:query'), RoleInterfaceAuthDependency('admin')],
)
async def get_pvp_attack_panel_detail(
    request: Request,
    panel_id: Annotated[int, Path(description='面板主键')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await PvpAttackPanelService.get_detail_services(query_db, panel_id))


@pvp_attack_panel_controller.post(
    '',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:pvp-attack-panel:add'), RoleInterfaceAuthDependency('admin')],
)
@ValidateFields(validate_model='add_pvp_attack_panel')
@Log(title='进攻方面板设置', business_type=BusinessType.INSERT)
async def add_pvp_attack_panel(
    request: Request,
    payload: PvpAttackPanelModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PvpAttackPanelService.add_services(query_db, payload, current_user.user.user_name)
    return ResponseUtil.success(msg=result.message, data=result.result)


@pvp_attack_panel_controller.put(
    '',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:pvp-attack-panel:edit'), RoleInterfaceAuthDependency('admin')],
)
@ValidateFields(validate_model='edit_pvp_attack_panel')
@Log(title='进攻方面板设置', business_type=BusinessType.UPDATE)
async def edit_pvp_attack_panel(
    request: Request,
    payload: PvpAttackPanelModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PvpAttackPanelService.edit_services(query_db, payload, current_user.user.user_name)
    return ResponseUtil.success(msg=result.message)

@pvp_attack_panel_controller.post(
    '/{panel_id}/status',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:pvp-attack-panel:edit'), RoleInterfaceAuthDependency('admin')],
)
@Log(title='进攻方面板状态', business_type=BusinessType.UPDATE)
async def change_pvp_attack_panel_status(
    request: Request,
    panel_id: Annotated[int, Path(description='面板主键')],
    payload: PvpAttackPanelStatusModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PvpAttackPanelService.change_status_services(
        query_db, panel_id, payload.status, current_user.user.user_name
    )
    return ResponseUtil.success(msg=result.message)


@pvp_attack_panel_controller.delete(
    '/{panel_ids}',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:pvp-attack-panel:remove'), RoleInterfaceAuthDependency('admin')],
)
@Log(title='进攻方面板设置', business_type=BusinessType.DELETE)
async def delete_pvp_attack_panel(
    request: Request,
    panel_ids: Annotated[str, Path(description='面板主键，多个逗号分隔')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await PvpAttackPanelService.delete_services(query_db, panel_ids)
    return ResponseUtil.success(msg=result.message)

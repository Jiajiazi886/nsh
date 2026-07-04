from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DynamicResponseModel
from module_admin.entity.vo.internal_power_panel_setting_vo import InternalPowerPanelSettingModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_panel_setting_service import InternalPowerPanelSettingService
from utils.log_util import logger
from utils.response_util import ResponseUtil

internal_power_panel_setting_controller = APIRouterPro(
    prefix='/personal/internal-power-panel-setting',
    order_num=92,
    tags=['个人管理-内功面板设置'],
    dependencies=[PreAuthDependency()],
)


@internal_power_panel_setting_controller.get(
    '',
    summary='获取当前用户内功PVP收益面板设置接口',
    description='用于获取当前登录用户的受击方面板和攻击方无内功基础面板',
    response_model=DynamicResponseModel[InternalPowerPanelSettingModel],
)
async def get_personal_internal_power_panel_setting(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerPanelSettingService.get_setting_services(query_db, current_user)
    logger.info('获取内功PVP收益面板设置成功')
    return ResponseUtil.success(model_content=result)


@internal_power_panel_setting_controller.put(
    '',
    summary='保存当前用户内功PVP收益面板设置接口',
    description='用于保存当前登录用户的受击方面板和攻击方无内功基础面板',
    response_model=DynamicResponseModel[InternalPowerPanelSettingModel],
)
@Log(title='个人内功PVP收益面板设置', business_type=BusinessType.UPDATE)
async def save_personal_internal_power_panel_setting(
    request: Request,
    payload: InternalPowerPanelSettingModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerPanelSettingService.save_setting_services(query_db, current_user, payload)
    logger.info('保存内功PVP收益面板设置成功')
    return ResponseUtil.success(model_content=result, msg='保存成功')

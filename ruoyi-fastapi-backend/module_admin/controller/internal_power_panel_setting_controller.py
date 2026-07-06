from typing import Annotated

from fastapi import File, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, DynamicResponseModel, ResponseBaseModel
from module_admin.entity.vo.internal_power_panel_setting_vo import (
    InternalPowerPanelSettingModel,
    InternalPowerPanelTemplateModel,
    PanelRecognitionHistoryListModel,
    PanelRecognitionResultModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_panel_recognition_service import InternalPowerPanelRecognitionService
from module_admin.service.internal_power_panel_setting_service import InternalPowerPanelSettingService
from module_admin.service.internal_power_panel_template_service import InternalPowerPanelTemplateService
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


@internal_power_panel_setting_controller.post(
    '/recognize-image',
    summary='识别玩家面板图片接口',
    description='上传单张玩家面板图片并调用Mimo识别为面板JSON',
    response_model=DataResponseModel[PanelRecognitionResultModel],
)
@Log(title='个人玩家面板识别', business_type=BusinessType.INSERT)
async def recognize_personal_internal_power_panel_image(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    file: Annotated[UploadFile, File(description='玩家面板图片')],
) -> Response:
    result = await InternalPowerPanelRecognitionService.recognize_image_services(query_db, current_user, file)
    logger.info('玩家面板图片识别完成')
    return ResponseUtil.success(data=result, msg='识别成功' if result.success else '识别失败')


@internal_power_panel_setting_controller.get(
    '/recognition-history',
    summary='获取玩家面板识别历史接口',
    description='普通用户最多返回5条，VIP和管理员最多返回10条',
    response_model=DynamicResponseModel[PanelRecognitionHistoryListModel],
)
async def get_personal_internal_power_panel_recognition_history(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerPanelRecognitionService.get_history_services(query_db, current_user)
    logger.info('获取玩家面板识别历史成功')
    return ResponseUtil.success(model_content=result)


@internal_power_panel_setting_controller.delete(
    '/recognition-history',
    summary='清空玩家面板识别历史接口',
    description='清空当前用户的玩家面板识别历史',
    response_model=ResponseBaseModel,
)
@Log(title='个人玩家面板识别历史', business_type=BusinessType.DELETE)
async def clear_personal_internal_power_panel_recognition_history(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerPanelRecognitionService.clear_history_services(query_db, current_user)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@internal_power_panel_setting_controller.get(
    '/templates',
    summary='获取启用面板模板接口',
    description='用于个人面板设置页一键套用系统模板',
    response_model=DataResponseModel[list[InternalPowerPanelTemplateModel]],
)
async def get_personal_internal_power_panel_templates(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerPanelTemplateService.get_enabled_templates_services(query_db)
    logger.info('获取启用面板模板成功')
    return ResponseUtil.success(data=result)

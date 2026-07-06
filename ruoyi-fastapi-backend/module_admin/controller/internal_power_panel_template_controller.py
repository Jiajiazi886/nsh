from datetime import datetime
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
from module_admin.entity.vo.internal_power_panel_setting_vo import (
    InternalPowerPanelTemplateModel,
    InternalPowerPanelTemplateQueryModel,
    InternalPowerPanelTemplateStatusModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_panel_template_service import InternalPowerPanelTemplateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

internal_power_panel_template_controller = APIRouterPro(
    prefix='/system/internal-power-panel-template',
    order_num=10,
    tags=['系统管理-面板模板设置'],
    dependencies=[PreAuthDependency()],
)


@internal_power_panel_template_controller.get(
    '/list',
    summary='获取面板模板分页列表接口',
    description='用于获取面板模板分页列表',
    response_model=PageResponseModel[InternalPowerPanelTemplateModel],
    dependencies=[UserInterfaceAuthDependency('system:internal-power-panel-template:list')],
)
async def get_system_internal_power_panel_template_list(
    request: Request,
    query: Annotated[InternalPowerPanelTemplateQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerPanelTemplateService.get_template_list_services(query_db, query, is_page=True)
    logger.info('获取面板模板列表成功')
    return ResponseUtil.success(model_content=result)


@internal_power_panel_template_controller.post(
    '',
    summary='新增面板模板接口',
    description='用于新增攻击方和受击方整套面板模板',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:internal-power-panel-template:add'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@ValidateFields(validate_model='add_template')
@Log(title='面板模板设置', business_type=BusinessType.INSERT)
async def add_system_internal_power_panel_template(
    request: Request,
    add_template: InternalPowerPanelTemplateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_template.create_time = datetime.now()
    add_template.update_time = datetime.now()
    operator = current_user.user.user_name if current_user.user else ''
    result = await InternalPowerPanelTemplateService.add_template_services(query_db, add_template, operator)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message, data=result.result)


@internal_power_panel_template_controller.put(
    '',
    summary='编辑面板模板接口',
    description='用于编辑攻击方和受击方整套面板模板',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:internal-power-panel-template:edit'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@ValidateFields(validate_model='edit_template')
@Log(title='面板模板设置', business_type=BusinessType.UPDATE)
async def edit_system_internal_power_panel_template(
    request: Request,
    edit_template: InternalPowerPanelTemplateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_template.update_time = datetime.now()
    operator = current_user.user.user_name if current_user.user else ''
    result = await InternalPowerPanelTemplateService.edit_template_services(query_db, edit_template, operator)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@internal_power_panel_template_controller.post(
    '/{template_id}/status',
    summary='修改面板模板状态接口',
    description='用于启用或停用面板模板',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:internal-power-panel-template:status'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@Log(title='面板模板状态', business_type=BusinessType.UPDATE)
async def change_system_internal_power_panel_template_status(
    request: Request,
    template_id: Annotated[int, Path(description='模板ID')],
    payload: InternalPowerPanelTemplateStatusModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    payload.template_id = template_id
    operator = current_user.user.user_name if current_user.user else ''
    result = await InternalPowerPanelTemplateService.change_status_services(query_db, payload, operator)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@internal_power_panel_template_controller.delete(
    '/{template_ids}',
    summary='删除面板模板接口',
    description='用于删除面板模板',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:internal-power-panel-template:remove'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@Log(title='面板模板设置', business_type=BusinessType.DELETE)
async def delete_system_internal_power_panel_template(
    request: Request,
    template_ids: Annotated[str, Path(description='需要删除的模板ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerPanelTemplateService.delete_template_services(query_db, template_ids)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@internal_power_panel_template_controller.get(
    '/{template_id}',
    summary='获取面板模板详情接口',
    description='用于获取指定面板模板详情',
    response_model=DataResponseModel[InternalPowerPanelTemplateModel],
    dependencies=[UserInterfaceAuthDependency('system:internal-power-panel-template:query')],
)
async def query_detail_system_internal_power_panel_template(
    request: Request,
    template_id: Annotated[int, Path(description='模板ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerPanelTemplateService.template_detail_services(query_db, template_id)
    logger.info(f'获取template_id为{template_id}的面板模板成功')
    return ResponseUtil.success(data=result)

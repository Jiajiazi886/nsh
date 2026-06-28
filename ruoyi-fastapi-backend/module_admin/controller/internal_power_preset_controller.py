from datetime import datetime
from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.internal_power_preset_vo import (
    DeleteInternalPowerPresetModel,
    InternalPowerPresetModel,
    InternalPowerPresetQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_preset_service import InternalPowerPresetService
from utils.log_util import logger
from utils.response_util import ResponseUtil

internal_power_preset_controller = APIRouterPro(
    prefix='/system/internal-power-preset',
    order_num=10,
    tags=['系统管理-内功信息管理'],
    dependencies=[PreAuthDependency()],
)


@internal_power_preset_controller.get(
    '/list',
    summary='获取内功预设分页列表接口',
    description='用于获取内功预设分页列表',
    response_model=PageResponseModel[InternalPowerPresetModel],
    dependencies=[UserInterfaceAuthDependency('system:internal-power:list')],
)
async def get_system_internal_power_preset_list(
    request: Request,
    preset_page_query: Annotated[InternalPowerPresetQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerPresetService.get_preset_list_services(query_db, preset_page_query, is_page=True)
    logger.info('获取内功预设列表成功')

    return ResponseUtil.success(model_content=result)


@internal_power_preset_controller.post(
    '',
    summary='新增内功预设接口',
    description='用于新增内功预设',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:internal-power:add')],
)
@ValidateFields(validate_model='add_preset')
@Log(title='内功信息管理', business_type=BusinessType.INSERT)
async def add_system_internal_power_preset(
    request: Request,
    add_preset: InternalPowerPresetModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_preset.create_time = datetime.now()
    add_preset.update_time = datetime.now()
    result = await InternalPowerPresetService.add_preset_services(query_db, add_preset)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@internal_power_preset_controller.put(
    '',
    summary='编辑内功预设接口',
    description='用于编辑内功预设',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:internal-power:edit')],
)
@ValidateFields(validate_model='edit_preset')
@Log(title='内功信息管理', business_type=BusinessType.UPDATE)
async def edit_system_internal_power_preset(
    request: Request,
    edit_preset: InternalPowerPresetModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_preset.update_time = datetime.now()
    result = await InternalPowerPresetService.edit_preset_services(query_db, edit_preset)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@internal_power_preset_controller.delete(
    '/{preset_ids}',
    summary='删除内功预设接口',
    description='用于删除内功预设',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:internal-power:remove')],
)
@Log(title='内功信息管理', business_type=BusinessType.DELETE)
async def delete_system_internal_power_preset(
    request: Request,
    preset_ids: Annotated[str, Path(description='需要删除的预设ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_preset = DeleteInternalPowerPresetModel(presetIds=preset_ids)
    result = await InternalPowerPresetService.delete_preset_services(query_db, delete_preset)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@internal_power_preset_controller.get(
    '/{preset_id}',
    summary='获取内功预设详情接口',
    description='用于获取指定内功预设详情',
    response_model=DataResponseModel[InternalPowerPresetModel],
    dependencies=[UserInterfaceAuthDependency('system:internal-power:query')],
)
async def query_detail_system_internal_power_preset(
    request: Request,
    preset_id: Annotated[int, Path(description='预设ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerPresetService.preset_detail_services(query_db, preset_id)
    logger.info(f'获取preset_id为{preset_id}的内功预设成功')

    return ResponseUtil.success(data=result)

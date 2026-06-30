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
from module_admin.entity.vo.internal_power_entry_vo import (
    DeleteInternalPowerEntryModel,
    InternalPowerEntryConfigModel,
    InternalPowerEntryQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_entry_service import InternalPowerEntryService
from utils.log_util import logger
from utils.response_util import ResponseUtil

internal_power_entry_controller = APIRouterPro(
    prefix='/system/internal-power-entry',
    order_num=10,
    tags=['系统管理-内功词条管理'],
    dependencies=[PreAuthDependency()],
)


@internal_power_entry_controller.get(
    '/list',
    summary='获取内功词条分页列表接口',
    description='用于获取内功词条分页列表',
    response_model=PageResponseModel[InternalPowerEntryConfigModel],
    dependencies=[UserInterfaceAuthDependency('system:internal-power-entry:list')],
)
async def get_system_internal_power_entry_list(
    request: Request,
    entry_page_query: Annotated[InternalPowerEntryQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerEntryService.get_entry_list_services(query_db, entry_page_query, is_page=True)
    logger.info('获取内功词条列表成功')

    return ResponseUtil.success(model_content=result)


@internal_power_entry_controller.post(
    '',
    summary='新增内功词条接口',
    description='用于新增内功词条',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:internal-power-entry:add'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@ValidateFields(validate_model='add_entry')
@Log(title='内功词条管理', business_type=BusinessType.INSERT)
async def add_system_internal_power_entry(
    request: Request,
    add_entry: InternalPowerEntryConfigModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_entry.create_time = datetime.now()
    add_entry.update_time = datetime.now()
    result = await InternalPowerEntryService.add_entry_services(query_db, add_entry)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@internal_power_entry_controller.put(
    '',
    summary='编辑内功词条接口',
    description='用于编辑内功词条',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:internal-power-entry:edit'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@ValidateFields(validate_model='edit_entry')
@Log(title='内功词条管理', business_type=BusinessType.UPDATE)
async def edit_system_internal_power_entry(
    request: Request,
    edit_entry: InternalPowerEntryConfigModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_entry.update_time = datetime.now()
    result = await InternalPowerEntryService.edit_entry_services(query_db, edit_entry)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@internal_power_entry_controller.delete(
    '/{entry_ids}',
    summary='删除内功词条接口',
    description='用于删除内功词条',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:internal-power-entry:remove'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@Log(title='内功词条管理', business_type=BusinessType.DELETE)
async def delete_system_internal_power_entry(
    request: Request,
    entry_ids: Annotated[str, Path(description='需要删除的词条ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_entry = DeleteInternalPowerEntryModel(entryIds=entry_ids)
    result = await InternalPowerEntryService.delete_entry_services(query_db, delete_entry)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@internal_power_entry_controller.get(
    '/{entry_id}',
    summary='获取内功词条详情接口',
    description='用于获取指定内功词条详情',
    response_model=DataResponseModel[InternalPowerEntryConfigModel],
    dependencies=[UserInterfaceAuthDependency('system:internal-power-entry:query')],
)
async def query_detail_system_internal_power_entry(
    request: Request,
    entry_id: Annotated[int, Path(description='词条ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerEntryService.entry_detail_services(query_db, entry_id)
    logger.info(f'获取entry_id为{entry_id}的内功词条成功')

    return ResponseUtil.success(data=result)

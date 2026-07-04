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
from module_admin.entity.vo.damage_formula_version_vo import (
    FORMULA_SCOPE_INTERNAL_POWER_PVP,
    DamageFormulaVersionModel,
    DamageFormulaVersionQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.damage_formula_version_service import DamageFormulaVersionService
from utils.log_util import logger
from utils.response_util import ResponseUtil

damage_formula_version_controller = APIRouterPro(
    prefix='/system/formula-design',
    order_num=10,
    tags=['系统管理-公式设计'],
    dependencies=[PreAuthDependency()],
)


@damage_formula_version_controller.get(
    '/active',
    summary='获取当前发布公式版本接口',
    description='用于获取当前内功PVP伤害收益公式版本',
    response_model=DataResponseModel[DamageFormulaVersionModel],
)
async def get_active_formula_version(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    scope: Annotated[str, Query(description='公式作用域')] = FORMULA_SCOPE_INTERNAL_POWER_PVP,
) -> Response:
    result = await DamageFormulaVersionService.get_active_version_services(query_db, scope)
    logger.info('获取当前发布公式版本成功')

    return ResponseUtil.success(data=result)


@damage_formula_version_controller.get(
    '/list',
    summary='获取公式版本分页列表接口',
    description='用于获取公式版本分页列表',
    response_model=PageResponseModel[DamageFormulaVersionModel],
    dependencies=[UserInterfaceAuthDependency('system:formula-design:list')],
)
async def get_formula_version_list(
    request: Request,
    query: Annotated[DamageFormulaVersionQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await DamageFormulaVersionService.get_version_list_services(query_db, query, is_page=True)
    logger.info('获取公式版本列表成功')

    return ResponseUtil.success(model_content=result)


@damage_formula_version_controller.post(
    '',
    summary='新增公式版本接口',
    description='用于新增公式草稿版本',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:formula-design:add'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@ValidateFields(validate_model='add_version')
@Log(title='公式设计', business_type=BusinessType.INSERT)
async def add_formula_version(
    request: Request,
    add_version: DamageFormulaVersionModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_version.create_time = datetime.now()
    add_version.update_time = datetime.now()
    operator = current_user.user.user_name if current_user.user else ''
    result = await DamageFormulaVersionService.add_version_services(query_db, add_version, operator)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message, data=result.result)


@damage_formula_version_controller.put(
    '',
    summary='编辑公式版本接口',
    description='用于编辑公式草稿版本',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:formula-design:edit'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@ValidateFields(validate_model='edit_version')
@Log(title='公式设计', business_type=BusinessType.UPDATE)
async def edit_formula_version(
    request: Request,
    edit_version: DamageFormulaVersionModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_version.update_time = datetime.now()
    operator = current_user.user.user_name if current_user.user else ''
    result = await DamageFormulaVersionService.edit_version_services(query_db, edit_version, operator)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@damage_formula_version_controller.post(
    '/{version_id}/copy',
    summary='复制公式版本接口',
    description='用于复制公式版本为草稿',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:formula-design:add'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@Log(title='公式设计', business_type=BusinessType.INSERT)
async def copy_formula_version(
    request: Request,
    version_id: Annotated[int, Path(description='公式版本ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    operator = current_user.user.user_name if current_user.user else ''
    result = await DamageFormulaVersionService.copy_version_services(query_db, version_id, operator)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message, data=result.result)


@damage_formula_version_controller.post(
    '/{version_id}/publish',
    summary='发布公式版本接口',
    description='用于发布公式版本并归档旧版本',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:formula-design:publish'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@Log(title='公式设计', business_type=BusinessType.UPDATE)
async def publish_formula_version(
    request: Request,
    version_id: Annotated[int, Path(description='公式版本ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    operator = current_user.user.user_name if current_user.user else ''
    result = await DamageFormulaVersionService.publish_version_services(query_db, version_id, operator)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@damage_formula_version_controller.post(
    '/{version_id}/rollback',
    summary='回滚公式版本接口',
    description='用于复制历史版本并发布为当前版本',
    response_model=ResponseBaseModel,
    dependencies=[
        UserInterfaceAuthDependency('system:formula-design:publish'),
        RoleInterfaceAuthDependency('admin'),
    ],
)
@Log(title='公式设计', business_type=BusinessType.UPDATE)
async def rollback_formula_version(
    request: Request,
    version_id: Annotated[int, Path(description='公式版本ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    operator = current_user.user.user_name if current_user.user else ''
    result = await DamageFormulaVersionService.rollback_version_services(query_db, version_id, operator)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message, data=result.result)


@damage_formula_version_controller.get(
    '/{version_id}',
    summary='获取公式版本详情接口',
    description='用于获取指定公式版本详情',
    response_model=DataResponseModel[DamageFormulaVersionModel],
    dependencies=[UserInterfaceAuthDependency('system:formula-design:query')],
)
async def query_detail_formula_version(
    request: Request,
    version_id: Annotated[int, Path(description='公式版本ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await DamageFormulaVersionService.version_detail_services(query_db, version_id)
    logger.info(f'获取version_id为{version_id}的公式版本成功')

    return ResponseUtil.success(data=result)

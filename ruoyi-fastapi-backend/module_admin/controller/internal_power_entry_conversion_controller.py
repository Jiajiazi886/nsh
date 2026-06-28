from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DynamicResponseModel
from module_admin.entity.vo.internal_power_entry_conversion_vo import (
    InternalPowerEntryConversionModel,
    InternalPowerEntryConversionSaveModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_entry_conversion_service import InternalPowerEntryConversionService
from utils.log_util import logger
from utils.response_util import ResponseUtil

internal_power_entry_conversion_controller = APIRouterPro(
    prefix='/personal/internal-power-entry-conversion',
    order_num=91,
    tags=['个人管理-内功词条换算'],
    dependencies=[PreAuthDependency()],
)


@internal_power_entry_conversion_controller.get(
    '',
    summary='获取当前用户内功词条换算接口',
    description='用于获取当前登录用户的内功词条换算配置',
    response_model=DynamicResponseModel[InternalPowerEntryConversionModel],
)
async def get_personal_internal_power_entry_conversion(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerEntryConversionService.get_conversion_services(query_db, current_user)
    logger.info('获取内功词条换算成功')

    return ResponseUtil.success(model_content=result)


@internal_power_entry_conversion_controller.put(
    '',
    summary='保存当前用户内功词条换算接口',
    description='用于保存当前登录用户的内功词条换算配置',
    response_model=DynamicResponseModel[InternalPowerEntryConversionModel],
)
@Log(title='个人内功词条换算', business_type=BusinessType.UPDATE)
async def save_personal_internal_power_entry_conversion(
    request: Request,
    payload: InternalPowerEntryConversionSaveModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerEntryConversionService.save_conversion_services(query_db, current_user, payload)
    logger.info('保存内功词条换算成功')

    return ResponseUtil.success(model_content=result, msg='保存成功')

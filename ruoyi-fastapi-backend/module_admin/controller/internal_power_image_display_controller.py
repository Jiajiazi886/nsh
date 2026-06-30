from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, ResponseBaseModel
from module_admin.entity.vo.internal_power_image_display_vo import (
    InternalPowerImageDisplaySaveModel,
    InternalPowerImageDisplayStatusModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_image_display_service import InternalPowerImageDisplayService
from utils.log_util import logger
from utils.response_util import ResponseUtil

internal_power_image_display_controller = APIRouterPro(
    prefix='/system/internal-power-image-display',
    order_num=11,
    tags=['系统管理-图片显示管理'],
    dependencies=[PreAuthDependency()],
)


@internal_power_image_display_controller.get(
    '/status',
    summary='获取内功图片显示开关',
    description='用于所有登录用户读取当前是否允许显示内功图片',
    response_model=DataResponseModel[InternalPowerImageDisplayStatusModel],
)
async def get_internal_power_image_display_status(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await InternalPowerImageDisplayService.get_status_services(query_db, request.app.state.redis)
    logger.info('获取内功图片显示开关成功')

    return ResponseUtil.success(data=result)


@internal_power_image_display_controller.put(
    '/status',
    summary='保存内功图片显示开关',
    description='用于管理员全局开启或关闭网页内功图片显示',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:internal-power-image-display:edit')],
)
@Log(title='图片显示管理', business_type=BusinessType.UPDATE)
async def save_internal_power_image_display_status(
    request: Request,
    save_data: InternalPowerImageDisplaySaveModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerImageDisplayService.save_status_services(
        query_db,
        request.app.state.redis,
        save_data.enabled,
        current_user.user.user_name,
    )
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)

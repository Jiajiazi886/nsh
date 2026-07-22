from typing import Annotated

from fastapi import Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log, RequestLogFieldRoot
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, ResponseBaseModel
from module_admin.entity.vo.ai_key_vo import InternalPowerAiKeyModel, InternalPowerAiKeyUpdateModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.ai_key_service import AiKeyService
from utils.log_util import logger
from utils.response_util import ResponseUtil

ai_key_controller = APIRouterPro(
    prefix='/system/ai-key',
    order_num=10,
    tags=['系统管理-AIKey管理'],
    dependencies=[PreAuthDependency()],
)


@ai_key_controller.get(
    '/internal-power',
    summary='获取内功图片识别 API Key 配置状态',
    response_model=DataResponseModel[InternalPowerAiKeyModel],
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
async def get_internal_power_key(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await AiKeyService.get_internal_power_key_services(query_db, current_user)
    return ResponseUtil.success(data=result)


@ai_key_controller.put(
    '/internal-power',
    summary='更新内功图片识别 API Key',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
@ValidateFields(validate_model='edit_ai_key')
@Log(
    title='内功识别 API Key',
    business_type=BusinessType.UPDATE,
    request_log_mode='exclude',
    request_exclude_fields=(RequestLogFieldRoot.JSON_BODY.field('api_key'),),
)
async def update_internal_power_key(
    request: Request,
    payload: InternalPowerAiKeyUpdateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await AiKeyService.update_internal_power_key_services(query_db, payload, current_user)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)

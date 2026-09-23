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
from module_admin.entity.vo.ai_key_vo import (
    AiConnectionModel,
    AiConnectionProbeModel,
    AiConnectionSaveModel,
    AiConnectionTestModel,
    AiModelsResultModel,
    AiTestResultModel,
    InternalPowerAiKeyModel,
    InternalPowerAiKeyUpdateModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.ai_connection_client import AiConnectionClientService
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
    '/connections',
    summary='获取 AI 连接工作台列表',
    response_model=DataResponseModel[list[AiConnectionModel]],
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
async def list_ai_connections(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await AiKeyService.list_connections_services(query_db, current_user)
    return ResponseUtil.success(data=result)


@ai_key_controller.post(
    '/connections',
    summary='创建 AI 连接',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
@Log(
    title='AI连接工作台',
    business_type=BusinessType.INSERT,
    request_log_mode='exclude',
    request_exclude_fields=(RequestLogFieldRoot.JSON_BODY.field('api_key'),),
)
async def create_ai_connection(
    request: Request,
    payload: AiConnectionSaveModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await AiKeyService.create_connection_services(query_db, payload, current_user)
    return ResponseUtil.success(msg=result.message)


@ai_key_controller.post(
    '/connections/discover-models',
    summary='读取上游模型列表',
    response_model=DataResponseModel[AiModelsResultModel],
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
@Log(
    title='AI连接模型发现',
    business_type=BusinessType.OTHER,
    request_log_mode='exclude',
    request_exclude_fields=(RequestLogFieldRoot.JSON_BODY.field('api_key'),),
)
async def discover_ai_models(
    request: Request,
    payload: AiConnectionProbeModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    AiKeyService.ensure_admin(current_user)
    runtime = await AiKeyService.resolve_probe_connection(query_db, payload)
    models = await AiConnectionClientService.list_models(runtime)
    return ResponseUtil.success(data=AiModelsResultModel(models=models))


@ai_key_controller.post(
    '/connections/test-chat',
    summary='使用选定连接进行真实多轮测试',
    response_model=DataResponseModel[AiTestResultModel],
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
@Log(
    title='AI连接对话测试',
    business_type=BusinessType.OTHER,
    request_log_mode='exclude',
    request_exclude_fields=(
        RequestLogFieldRoot.JSON_BODY.field('api_key'),
        RequestLogFieldRoot.JSON_BODY.field('messages'),
    ),
)
async def test_ai_connection(
    request: Request,
    payload: AiConnectionTestModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    AiKeyService.ensure_admin(current_user)
    runtime = await AiKeyService.resolve_probe_connection(
        query_db,
        payload,
        protocol=payload.protocol,
        model=payload.model,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
    )
    text = await AiConnectionClientService.chat(runtime, payload.messages)
    return ResponseUtil.success(data=AiTestResultModel(text=text))


@ai_key_controller.put(
    '/connections/{connection_id}',
    summary='保存 AI 连接',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
@Log(
    title='AI连接工作台',
    business_type=BusinessType.UPDATE,
    request_log_mode='exclude',
    request_exclude_fields=(RequestLogFieldRoot.JSON_BODY.field('api_key'),),
)
async def update_ai_connection(
    request: Request,
    connection_id: int,
    payload: AiConnectionSaveModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await AiKeyService.update_connection_services(query_db, connection_id, payload, current_user)
    return ResponseUtil.success(msg=result.message)


@ai_key_controller.put(
    '/connections/{connection_id}/activate',
    summary='切换全系统当前 AI 连接',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
@Log(title='AI连接切换', business_type=BusinessType.UPDATE)
async def activate_ai_connection(
    request: Request,
    connection_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await AiKeyService.activate_connection_services(query_db, connection_id, current_user)
    return ResponseUtil.success(msg=result.message)


@ai_key_controller.delete(
    '/connections/{connection_id}',
    summary='删除备选 AI 连接',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
@Log(title='AI连接工作台', business_type=BusinessType.DELETE)
async def delete_ai_connection(
    request: Request,
    connection_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await AiKeyService.delete_connection_services(query_db, connection_id, current_user)
    return ResponseUtil.success(msg=result.message)


@ai_key_controller.get(
    '/internal-power',
    summary='获取项目AI图片识别 API Key 配置状态',
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
    summary='更新项目AI图片识别 API Key',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:aikey:edit')],
)
@ValidateFields(validate_model='edit_ai_key')
@Log(
    title='AI图片识别 API Key',
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

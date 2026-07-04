from typing import Annotated

from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DynamicResponseModel, ResponseBaseModel
from module_admin.entity.vo.internal_power_vo import (
    InternalPowerImportModel,
    InternalPowerListModel,
    InternalPowerModel,
    InternalPowerRecognitionHistoryListModel,
    InternalPowerRecognitionSavedModel,
    InternalPowerRecognizeResultModel,
)
from module_admin.entity.vo.internal_power_entry_vo import InternalPowerEntryListModel
from module_admin.entity.vo.internal_power_preset_vo import InternalPowerPresetListModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_entry_service import InternalPowerEntryService
from module_admin.service.internal_power_preset_service import InternalPowerPresetService
from module_admin.service.internal_power_service import InternalPowerService
from utils.log_util import logger
from utils.response_util import ResponseUtil

internal_power_controller = APIRouterPro(
    prefix='/personal/internal-power',
    order_num=90,
    tags=['个人管理-内功管理'],
    dependencies=[PreAuthDependency()],
)


@internal_power_controller.get(
    '/list',
    summary='获取当前用户内功列表接口',
    description='用于获取当前登录用户的内功列表和额度信息',
    response_model=DynamicResponseModel[InternalPowerListModel],
)
async def get_personal_internal_power_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerService.get_list_services(query_db, current_user)
    logger.info('获取内功列表成功')

    return ResponseUtil.success(model_content=result)


@internal_power_controller.get(
    '/presets',
    summary='获取启用内功预设列表接口',
    description='用于个人内功管理读取可用内功预设',
    response_model=DynamicResponseModel[InternalPowerPresetListModel],
)
async def get_personal_internal_power_presets(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = InternalPowerPresetListModel(
        presets=await InternalPowerPresetService.get_personal_enabled_presets_service(query_db)
    )
    logger.info('获取启用内功预设成功')

    return ResponseUtil.success(model_content=result)


@internal_power_controller.get(
    '/entries',
    summary='获取启用内功词条列表接口',
    description='用于个人内功管理读取可用内功词条',
    response_model=DynamicResponseModel[InternalPowerEntryListModel],
)
async def get_personal_internal_power_entries(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = InternalPowerEntryListModel(
        entries=await InternalPowerEntryService.get_personal_enabled_entries_service(query_db)
    )
    logger.info('获取启用内功词条成功')

    return ResponseUtil.success(model_content=result)


@internal_power_controller.post(
    '',
    summary='新增当前用户内功接口',
    description='用于新增当前登录用户的内功',
    response_model=DynamicResponseModel[InternalPowerModel],
)
@Log(title='内功管理', business_type=BusinessType.INSERT)
async def add_personal_internal_power(
    request: Request,
    power: InternalPowerModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerService.add_power_services(query_db, current_user, power)
    logger.info('新增内功成功')

    return ResponseUtil.success(model_content=result)


@internal_power_controller.put(
    '/{power_id}',
    summary='编辑当前用户内功接口',
    description='用于编辑当前登录用户的内功',
    response_model=DynamicResponseModel[InternalPowerModel],
)
@Log(title='内功管理', business_type=BusinessType.UPDATE)
async def edit_personal_internal_power(
    request: Request,
    power: InternalPowerModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    power_id: Annotated[int, Path(description='内功ID')],
) -> Response:
    result = await InternalPowerService.edit_power_services(query_db, current_user, power_id, power)
    logger.info('编辑内功成功')

    return ResponseUtil.success(model_content=result)


@internal_power_controller.delete(
    '/{power_id:int}',
    summary='删除当前用户内功接口',
    description='用于删除当前登录用户的内功',
    response_model=ResponseBaseModel,
)
@Log(title='内功管理', business_type=BusinessType.DELETE)
async def delete_personal_internal_power(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    power_id: Annotated[int, Path(description='内功ID')],
) -> Response:
    result = await InternalPowerService.delete_power_services(query_db, current_user, power_id)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@internal_power_controller.post(
    '/import-local',
    summary='导入当前用户本地内功接口',
    description='用于首次把浏览器localStorage内功导入后端',
    response_model=DynamicResponseModel[InternalPowerListModel],
)
@Log(title='内功管理', business_type=BusinessType.IMPORT)
async def import_personal_internal_power_from_local(
    request: Request,
    import_data: InternalPowerImportModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerService.import_local_services(query_db, current_user, import_data)
    logger.info('导入本地内功成功')

    return ResponseUtil.success(model_content=result)


@internal_power_controller.post(
    '/recognize-images',
    summary='内功图片AI识别接口',
    description='用于上传一张或多张内功图片并调用Mimo识别，成功解析的图片才消耗AI识图次数',
    response_model=DynamicResponseModel[InternalPowerRecognizeResultModel],
)
@Log(title='内功图片识别', business_type=BusinessType.OTHER)
async def recognize_personal_internal_power_images(
    request: Request,
    files: Annotated[list[UploadFile], File(description='待识别图片列表')],
    prompt: Annotated[str, Form(description='固定识别提示词')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    if not files:
        return ResponseUtil.failure(msg='请至少上传一张图片')
    for file in files:
        if not (file.content_type or '').startswith('image/'):
            return ResponseUtil.failure(msg='只能上传图片文件')
    result = await InternalPowerService.recognize_images_services(query_db, current_user, files, prompt)
    logger.info(f'内功图片识别完成，消耗{result.consumed_count}次')

    return ResponseUtil.success(model_content=result, msg='识别完成')


@internal_power_controller.get(
    '/recognition-history',
    summary='获取内功图片识别历史接口',
    description='用于分页获取当前登录用户最近50条内功图片识别历史',
    response_model=DynamicResponseModel[InternalPowerRecognitionHistoryListModel],
)
async def get_personal_internal_power_recognition_history(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    page_num: Annotated[int, Query(alias='pageNum', ge=1)] = 1,
    page_size: Annotated[int, Query(alias='pageSize', ge=1, le=10)] = 10,
) -> Response:
    result = await InternalPowerService.get_recognition_history_services(query_db, current_user, page_num, page_size)
    logger.info('获取内功图片识别历史成功')

    return ResponseUtil.success(model_content=result)


@internal_power_controller.delete(
    '/recognition-history',
    summary='清空内功图片识别历史接口',
    description='用于清空当前登录用户的内功图片识别历史',
    response_model=ResponseBaseModel,
)
@Log(title='内功图片识别历史', business_type=BusinessType.DELETE)
async def clear_personal_internal_power_recognition_history(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InternalPowerService.clear_recognition_history_services(query_db, current_user)
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)


@internal_power_controller.put(
    '/recognition-history/{record_id}/saved',
    summary='标记内功图片识别历史已保存接口',
    description='用于在识别结果新增内功后回写识别历史状态',
    response_model=ResponseBaseModel,
)
async def mark_personal_internal_power_recognition_history_saved(
    request: Request,
    payload: InternalPowerRecognitionSavedModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    record_id: Annotated[int, Path(description='识别记录ID')],
) -> Response:
    result = await InternalPowerService.mark_recognition_history_saved_services(
        query_db, current_user, record_id, payload
    )
    logger.info(result.message)

    return ResponseUtil.success(msg=result.message)

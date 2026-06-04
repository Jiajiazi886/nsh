from datetime import datetime
from typing import Annotated

from fastapi import Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from exceptions.exception import ServiceException
from module_guild.entity.vo.profession_vo import DeleteProfessionModel, ProfessionModel, ProfessionPageQueryModel
from module_guild.service.profession_service import ProfessionService
from utils.log_util import logger
from utils.response_util import ResponseUtil

profession_controller = APIRouterPro(
    prefix='/guild/profession', order_num=25, tags=['帮会管理-职业信息'], dependencies=[PreAuthDependency()]
)


@profession_controller.get(
    '/list',
    summary='获取职业信息列表',
    dependencies=[UserInterfaceAuthDependency('guild:profession:read')],
)
async def get_profession_list(
    profession_page_query: Annotated[ProfessionPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    profession_list_result = await ProfessionService.get_profession_list_service(
        query_db, profession_page_query, is_page=True
    )
    return ResponseUtil.success(model_content=profession_list_result)


@profession_controller.get(
    '/options',
    summary='获取可用职业选项',
    dependencies=[UserInterfaceAuthDependency('guild:profession:read')],
)
async def get_profession_options(query_db: Annotated[AsyncSession, DBSessionDependency()] = None) -> Response:
    result = await ProfessionService.get_enabled_profession_options_service(query_db)
    return ResponseUtil.success(data=result)


@profession_controller.post(
    '',
    summary='新增职业信息',
    dependencies=[UserInterfaceAuthDependency('guild:profession:write')],
)
async def add_profession(
    add_model: ProfessionModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        add_model.create_by = current_user.user.user_name
        add_model.create_time = datetime.now()
        add_model.update_by = current_user.user.user_name
        add_model.update_time = datetime.now()
        result = await ProfessionService.add_profession_service(query_db, add_model)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增职业信息失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@profession_controller.put(
    '',
    summary='修改职业信息',
    dependencies=[UserInterfaceAuthDependency('guild:profession:write')],
)
async def edit_profession(
    edit_model: ProfessionModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        edit_model.update_by = current_user.user.user_name
        edit_model.update_time = datetime.now()
        result = await ProfessionService.edit_profession_service(query_db, edit_model)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'修改职业信息失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@profession_controller.delete(
    '/{profession_ids}',
    summary='删除职业信息',
    dependencies=[UserInterfaceAuthDependency('guild:profession:write')],
)
async def delete_profession(
    profession_ids: Annotated[str, Path(description='需要删除的职业ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    try:
        result = await ProfessionService.delete_profession_service(
            query_db, DeleteProfessionModel(professionIds=profession_ids)
        )
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除职业信息失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@profession_controller.get(
    '/{profession_id}',
    summary='获取职业详情',
    dependencies=[UserInterfaceAuthDependency('guild:profession:read')],
)
async def get_profession_detail(
    profession_id: Annotated[int, Path(description='职业ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
) -> Response:
    result = await ProfessionService.profession_detail_service(query_db, profession_id)
    return ResponseUtil.success(data=result)

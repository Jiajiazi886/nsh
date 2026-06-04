from typing import Annotated
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from exceptions.exception import ServiceException
from module_guild.entity.vo.class_color_vo import ClassColorSaveModel
from module_guild.service.class_color_service import ClassColorService
from utils.log_util import logger
from utils.response_util import ResponseUtil

class_color_controller = APIRouterPro(
    prefix='/guild/class-color', order_num=23, tags=['帮会管理-职业颜色设置'], dependencies=[PreAuthDependency()]
)

@class_color_controller.get('/list', summary='获取职业颜色配置', dependencies=[UserInterfaceAuthDependency('guild:class-color:query')])
async def get_class_colors(
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ClassColorService.get_colors_service(query_db, current_user)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'获取颜色配置失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))

@class_color_controller.post('/save', summary='保存职业颜色配置', dependencies=[UserInterfaceAuthDependency('guild:class-color:edit')])
async def save_class_colors(
    data: ClassColorSaveModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await ClassColorService.save_colors_service(query_db, current_user, data)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'保存颜色配置失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))
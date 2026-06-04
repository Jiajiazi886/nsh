from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import ResponseBaseModel
from exceptions.exception import ServiceException
from module_guild.entity.vo.battle_vo import BattleImportModel
from module_guild.service.battle_service import BattleService
from utils.log_util import logger
from utils.response_util import ResponseUtil

battle_controller = APIRouterPro(
    prefix='/guild/battle', order_num=20, tags=['帮会管理-约战管理'], dependencies=[PreAuthDependency()]
)


@battle_controller.post(
    '/import',
    summary='导入约战数据接口',
    description='用于批量导入约战数据及玩家明细',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('guild:battle:import')],
)
@Log(title='约战管理', business_type=BusinessType.IMPORT)
async def import_battle(
    request: Request,
    import_data: BattleImportModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[dict, CurrentUserDependency()],
) -> Response:
    try:
        import_result = await BattleService.import_battle_service(query_db, current_user, import_data)
        logger.info(import_result.message)
        return ResponseUtil.success(msg=import_result.message)
    except Exception as e:
        logger.error(f'导入约战数据失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@battle_controller.get(
    '/list',
    summary='查询历史记录列表',
    description='分页查询当前用户的约战历史记录',
    dependencies=[UserInterfaceAuthDependency('guild:battle:list')],
)
async def query_history(
    request: Request,
    page: int = 1,
    size: int = 10,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleService.query_history_service(query_db, current_user, page, size)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'查询历史记录失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@battle_controller.get(
    '/records/{battle_id}',
    summary='查询战斗记录明细',
    description='根据约战ID查询所有玩家战斗明细',
)
async def get_battle_records(
    request: Request,
    battle_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleService.query_records_service(query_db, battle_id)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'查询战斗明细失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@battle_controller.delete(
    '/{battle_id}',
    summary='删除战斗记录',
    description='软删除指定的约战记录及其明细',
)
async def soft_delete_battle(
    request: Request,
    battle_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleService.soft_delete_service(query_db, current_user, battle_id)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除战斗记录失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@battle_controller.get(
    '/check-filename',
    summary='校验文件名是否重复',
    description='根据当前用户和文件名查询是否已存在同名记录',
)
async def check_filename(
    filename: str,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: Annotated[dict, CurrentUserDependency()] = None,
) -> Response:
    try:
        result = await BattleService.check_duplicate_filename_service(query_db, current_user, filename)
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'校验文件名失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))
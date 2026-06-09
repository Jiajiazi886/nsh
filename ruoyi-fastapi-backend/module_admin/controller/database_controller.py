from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel
from module_admin.entity.vo.database_vo import (
    DatabaseColumnModel,
    DatabaseOverviewModel,
    DatabaseRowsModel,
    DatabaseUsersModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.database_service import DatabaseService
from utils.log_util import logger
from utils.response_util import ResponseUtil

database_controller = APIRouterPro(
    prefix='/system/database',
    order_num=6,
    tags=['系统管理-数据库管理'],
    dependencies=[PreAuthDependency()],
)


@database_controller.get(
    '/overview',
    summary='获取数据库总览',
    response_model=DataResponseModel[DatabaseOverviewModel],
    dependencies=[UserInterfaceAuthDependency('system:database:list')],
)
async def get_database_overview(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await DatabaseService.get_database_overview_services(query_db, current_user)
    logger.info('获取数据库总览成功')
    return ResponseUtil.success(data=result)


@database_controller.get(
    '/users',
    summary='获取所有用户数据总览',
    response_model=DataResponseModel[DatabaseUsersModel],
    dependencies=[UserInterfaceAuthDependency('system:database:list')],
)
async def get_database_users(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    page_num: Annotated[int, Query(alias='pageNum')] = 1,
    page_size: Annotated[int, Query(alias='pageSize')] = 10,
) -> Response:
    result = await DatabaseService.get_all_users_services(query_db, page_num, page_size, current_user)
    logger.info('获取全部用户数据成功')
    return ResponseUtil.success(data=result)


@database_controller.get(
    '/tables/{table_name}/columns',
    summary='获取数据表字段',
    response_model=DataResponseModel[list[DatabaseColumnModel]],
    dependencies=[UserInterfaceAuthDependency('system:database:list')],
)
async def get_database_table_columns(
    request: Request,
    table_name: Annotated[str, Path(description='表名')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await DatabaseService.get_table_columns_services(query_db, table_name, current_user)
    logger.info(f'获取数据表{table_name}字段成功')
    return ResponseUtil.success(data=result)


@database_controller.get(
    '/tables/{table_name}/rows',
    summary='获取数据表分页数据',
    response_model=DataResponseModel[DatabaseRowsModel],
    dependencies=[UserInterfaceAuthDependency('system:database:query')],
)
async def get_database_table_rows(
    request: Request,
    table_name: Annotated[str, Path(description='表名')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    page_num: Annotated[int, Query(alias='pageNum')] = 1,
    page_size: Annotated[int, Query(alias='pageSize')] = 10,
) -> Response:
    result = await DatabaseService.get_table_rows_services(query_db, table_name, page_num, page_size, current_user)
    logger.info(f'获取数据表{table_name}分页数据成功')
    return ResponseUtil.success(data=result)

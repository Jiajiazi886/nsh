from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config.env import DataBaseConfig
from exceptions.exception import PermissionException, ServiceException
from module_admin.entity.vo.database_vo import (
    DatabaseColumnModel,
    DatabaseOverviewModel,
    DatabaseRowsModel,
    DatabaseTableModel,
    DatabaseUserRowModel,
    DatabaseUsersModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel


class DatabaseService:
    """
    Read-only database browser for the super administrator.
    """

    @classmethod
    def ensure_super_admin(cls, current_user: CurrentUserModel) -> None:
        if not current_user.user or not current_user.user.admin:
            raise PermissionException(message='只有超级管理员可以访问数据库管理')

    @classmethod
    async def get_database_overview_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> DatabaseOverviewModel:
        cls.ensure_super_admin(current_user)
        if DataBaseConfig.db_type == 'postgresql':
            rows = (
                await query_db.execute(
                    text(
                        """
                        SELECT
                            c.relname AS table_name,
                            COALESCE(obj_description(c.oid), '') AS table_comment,
                            GREATEST(c.reltuples::bigint, 0) AS row_count,
                            pg_total_relation_size(c.oid) AS data_length,
                            0 AS index_length,
                            NULL AS create_time,
                            NULL AS update_time
                        FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE c.relkind = 'r'
                          AND n.nspname = 'public'
                        ORDER BY c.relname
                        """
                    )
                )
            ).mappings().all()
        else:
            rows = (
                await query_db.execute(
                    text(
                        """
                        SELECT
                            table_name,
                            table_comment,
                            COALESCE(table_rows, 0) AS row_count,
                            COALESCE(data_length, 0) AS data_length,
                            COALESCE(index_length, 0) AS index_length,
                            create_time,
                            update_time
                        FROM information_schema.tables
                        WHERE table_schema = :database_name
                        ORDER BY table_name
                        """
                    ),
                    {'database_name': DataBaseConfig.db_database},
                )
            ).mappings().all()

        tables = [DatabaseTableModel(**cls._serialize_mapping(row, normalize_keys=True)) for row in rows]
        return DatabaseOverviewModel(
            databaseName=DataBaseConfig.db_database,
            databaseType=DataBaseConfig.db_type,
            totalTables=len(tables),
            tables=tables,
        )

    @classmethod
    async def get_table_columns_services(
        cls, query_db: AsyncSession, table_name: str, current_user: CurrentUserModel
    ) -> list[DatabaseColumnModel]:
        cls.ensure_super_admin(current_user)
        await cls._assert_table_exists(query_db, table_name)
        if DataBaseConfig.db_type == 'postgresql':
            rows = (
                await query_db.execute(
                    text(
                        """
                        SELECT
                            c.column_name,
                            c.data_type,
                            c.udt_name AS column_type,
                            c.is_nullable,
                            CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'PRI' ELSE '' END AS column_key,
                            c.column_default,
                            COALESCE(pgd.description, '') AS column_comment,
                            c.ordinal_position
                        FROM information_schema.columns c
                        LEFT JOIN information_schema.key_column_usage kcu
                          ON c.table_name = kcu.table_name
                         AND c.column_name = kcu.column_name
                         AND c.table_schema = kcu.table_schema
                        LEFT JOIN information_schema.table_constraints tc
                          ON kcu.constraint_name = tc.constraint_name
                         AND kcu.table_schema = tc.table_schema
                         AND tc.constraint_type = 'PRIMARY KEY'
                        LEFT JOIN pg_catalog.pg_statio_all_tables st
                          ON st.relname = c.table_name
                        LEFT JOIN pg_catalog.pg_description pgd
                          ON pgd.objoid = st.relid
                         AND pgd.objsubid = c.ordinal_position
                        WHERE c.table_schema = 'public'
                          AND c.table_name = :table_name
                        ORDER BY c.ordinal_position
                        """
                    ),
                    {'table_name': table_name},
                )
            ).mappings().all()
        else:
            rows = (
                await query_db.execute(
                    text(
                        """
                        SELECT
                            column_name,
                            data_type,
                            column_type,
                            is_nullable,
                            column_key,
                            column_default,
                            column_comment,
                            ordinal_position
                        FROM information_schema.columns
                        WHERE table_schema = :database_name
                          AND table_name = :table_name
                        ORDER BY ordinal_position
                        """
                    ),
                    {'database_name': DataBaseConfig.db_database, 'table_name': table_name},
                )
            ).mappings().all()
        return [DatabaseColumnModel(**cls._serialize_mapping(row, normalize_keys=True)) for row in rows]

    @classmethod
    async def get_table_rows_services(
        cls,
        query_db: AsyncSession,
        table_name: str,
        page_num: int,
        page_size: int,
        current_user: CurrentUserModel,
    ) -> DatabaseRowsModel:
        cls.ensure_super_admin(current_user)
        await cls._assert_table_exists(query_db, table_name)
        page_num = max(page_num, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page_num - 1) * page_size
        quoted_table_name = cls._quote_identifier(table_name)

        total = (
            await query_db.execute(text(f'SELECT COUNT(*) AS total FROM {quoted_table_name}'))
        ).mappings().one()['total']
        result = (
            await query_db.execute(
                text(f'SELECT * FROM {quoted_table_name} LIMIT :page_size OFFSET :offset'),
                {'page_size': page_size, 'offset': offset},
            )
        ).mappings().all()
        rows = [cls._serialize_mapping(row) for row in result]
        columns = list(rows[0].keys()) if rows else [item.column_name for item in await cls.get_table_columns_services(query_db, table_name, current_user)]
        return DatabaseRowsModel(
            tableName=table_name,
            columns=columns,
            rows=rows,
            pageNum=page_num,
            pageSize=page_size,
            total=int(total),
        )

    @classmethod
    async def get_all_users_services(
        cls, query_db: AsyncSession, page_num: int, page_size: int, current_user: CurrentUserModel
    ) -> DatabaseUsersModel:
        cls.ensure_super_admin(current_user)
        page_num = max(page_num, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page_num - 1) * page_size
        total = (
            await query_db.execute(text("SELECT COUNT(*) AS total FROM sys_user WHERE del_flag = '0'"))
        ).mappings().one()['total']

        if DataBaseConfig.db_type == 'postgresql':
            role_names_expr = "string_agg(r.role_name, ', ' ORDER BY r.role_sort)"
            role_keys_expr = "string_agg(r.role_key, ', ' ORDER BY r.role_sort)"
        else:
            role_names_expr = "GROUP_CONCAT(r.role_name ORDER BY r.role_sort SEPARATOR ', ')"
            role_keys_expr = "GROUP_CONCAT(r.role_key ORDER BY r.role_sort SEPARATOR ', ')"

        rows = (
            await query_db.execute(
                text(
                    f"""
                    SELECT
                        u.user_id,
                        u.user_name,
                        u.nick_name,
                        u.user_type,
                        u.email,
                        u.status,
                        u.del_flag,
                        u.login_ip,
                        u.login_date,
                        u.create_time,
                        COALESCE({role_names_expr}, '') AS role_names,
                        COALESCE({role_keys_expr}, '') AS role_keys,
                        u.remark
                    FROM sys_user u
                    LEFT JOIN sys_user_role ur ON ur.user_id = u.user_id
                    LEFT JOIN sys_role r ON r.role_id = ur.role_id
                    WHERE u.del_flag = '0'
                    GROUP BY
                        u.user_id, u.user_name, u.nick_name, u.user_type, u.email,
                        u.status, u.del_flag, u.login_ip, u.login_date, u.create_time, u.remark
                    ORDER BY u.user_id ASC
                    LIMIT :page_size OFFSET :offset
                    """
                ),
                {'page_size': page_size, 'offset': offset},
            )
        ).mappings().all()
        return DatabaseUsersModel(
            rows=[DatabaseUserRowModel(**cls._serialize_mapping(row, normalize_keys=True)) for row in rows],
            pageNum=page_num,
            pageSize=page_size,
            total=int(total),
        )

    @classmethod
    async def _assert_table_exists(cls, query_db: AsyncSession, table_name: str) -> None:
        if not table_name or any(char in table_name for char in ['`', '"', "'", ';', '/', '\\', '\x00']):
            raise ServiceException(message='表名不合法')
        if DataBaseConfig.db_type == 'postgresql':
            exists = (
                await query_db.execute(
                    text(
                        """
                        SELECT COUNT(*) AS total
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = :table_name
                        """
                    ),
                    {'table_name': table_name},
                )
            ).mappings().one()['total']
        else:
            exists = (
                await query_db.execute(
                    text(
                        """
                        SELECT COUNT(*) AS total
                        FROM information_schema.tables
                        WHERE table_schema = :database_name
                          AND table_name = :table_name
                        """
                    ),
                    {'database_name': DataBaseConfig.db_database, 'table_name': table_name},
                )
            ).mappings().one()['total']
        if int(exists) <= 0:
            raise ServiceException(message='表不存在或无权访问')

    @classmethod
    def _quote_identifier(cls, identifier: str) -> str:
        if DataBaseConfig.db_type == 'postgresql':
            return f'"{identifier.replace(chr(34), chr(34) * 2)}"'
        return f'`{identifier.replace("`", "``")}`'

    @classmethod
    def _serialize_mapping(cls, row: Any, normalize_keys: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in dict(row).items():
            normalized_key = str(key).lower() if normalize_keys else str(key)
            if isinstance(value, datetime | date):
                result[normalized_key] = value.isoformat(sep=' ') if isinstance(value, datetime) else value.isoformat()
            elif isinstance(value, Decimal):
                result[normalized_key] = float(value)
            elif isinstance(value, bytes):
                result[normalized_key] = value.hex()
            else:
                result[normalized_key] = value
        return result

from typing import Any

from sqlalchemy import delete, inspect, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.internal_power_entry_do import SystemInternalPowerEntry
from module_admin.entity.vo.internal_power_entry_vo import InternalPowerEntryQueryModel
from utils.page_util import PageUtil


class InternalPowerEntryDao:
    """
    系统内功词条数据库操作层
    """

    _schema_checked = False

    @classmethod
    async def _ensure_entry_schema(cls, db: AsyncSession) -> None:
        if cls._schema_checked:
            return

        def _inspect_columns(sync_session) -> tuple[str, set[str], bool]:
            bind = sync_session.get_bind()
            dialect_name = bind.dialect.name
            inspector = inspect(bind)
            table_exists = 'system_internal_power_entry' in inspector.get_table_names()
            if not table_exists:
                return dialect_name, set(), False
            columns = {column['name'] for column in inspector.get_columns('system_internal_power_entry')}
            return dialect_name, columns, True

        dialect_name, columns, table_exists = await db.run_sync(_inspect_columns)
        if not table_exists:
            cls._schema_checked = True
            return

        column_defs = {
            'conversion_percent': {
                'postgresql': 'ALTER TABLE system_internal_power_entry ADD COLUMN conversion_percent DOUBLE PRECISION',
                'mysql': "ALTER TABLE system_internal_power_entry ADD COLUMN conversion_percent double DEFAULT NULL COMMENT '数值转换百分比' AFTER entry_name",
            },
            'conversion_desc': {
                'postgresql': "ALTER TABLE system_internal_power_entry ADD COLUMN conversion_desc VARCHAR(255) DEFAULT ''",
                'mysql': "ALTER TABLE system_internal_power_entry ADD COLUMN conversion_desc varchar(255) DEFAULT '' COMMENT '转换说明' AFTER conversion_percent",
            },
            'limit_text': {
                'postgresql': "ALTER TABLE system_internal_power_entry ADD COLUMN limit_text VARCHAR(32) DEFAULT ''",
                'mysql': "ALTER TABLE system_internal_power_entry ADD COLUMN limit_text varchar(32) DEFAULT '' COMMENT '固定上限展示值' AFTER conversion_desc",
            },
            'limit_value': {
                'postgresql': 'ALTER TABLE system_internal_power_entry ADD COLUMN limit_value DOUBLE PRECISION',
                'mysql': "ALTER TABLE system_internal_power_entry ADD COLUMN limit_value double DEFAULT NULL COMMENT '固定上限数值' AFTER limit_text",
            },
            'value_type': {
                'postgresql': "ALTER TABLE system_internal_power_entry ADD COLUMN value_type VARCHAR(16) NOT NULL DEFAULT 'number'",
                'mysql': "ALTER TABLE system_internal_power_entry ADD COLUMN value_type varchar(16) NOT NULL DEFAULT 'number' COMMENT '数值类型（number数值 percent百分比）' AFTER limit_value",
            },
        }
        statements = [
            defs['postgresql' if dialect_name == 'postgresql' else 'mysql']
            for column, defs in column_defs.items()
            if column not in columns
        ]
        if statements:
            for statement in statements:
                await db.execute(text(statement))
            await db.commit()
        cls._schema_checked = True

    @classmethod
    async def get_list(
        cls, db: AsyncSession, query_object: InternalPowerEntryQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        await cls._ensure_entry_schema(db)
        query = (
            select(SystemInternalPowerEntry)
            .where(
                SystemInternalPowerEntry.entry_name.like(f'%{query_object.entry_name}%')
                if query_object.entry_name
                else True,
                SystemInternalPowerEntry.status == query_object.status if query_object.status else True,
            )
            .order_by(SystemInternalPowerEntry.entry_id)
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def list_enabled(cls, db: AsyncSession) -> list[SystemInternalPowerEntry]:
        await cls._ensure_entry_schema(db)
        result = await db.execute(
            select(SystemInternalPowerEntry)
            .where(SystemInternalPowerEntry.status == '0')
            .order_by(SystemInternalPowerEntry.entry_id)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, db: AsyncSession, entry_id: int) -> SystemInternalPowerEntry | None:
        await cls._ensure_entry_schema(db)
        result = await db.execute(
            select(SystemInternalPowerEntry).where(SystemInternalPowerEntry.entry_id == entry_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_name(cls, db: AsyncSession, entry_name: str) -> SystemInternalPowerEntry | None:
        await cls._ensure_entry_schema(db)
        result = await db.execute(
            select(SystemInternalPowerEntry).where(SystemInternalPowerEntry.entry_name == entry_name)
        )
        return result.scalars().first()

    @classmethod
    async def add(cls, db: AsyncSession, entry: SystemInternalPowerEntry) -> SystemInternalPowerEntry:
        await cls._ensure_entry_schema(db)
        db.add(entry)
        await db.flush()
        return entry

    @classmethod
    async def update(cls, db: AsyncSession, values: dict) -> None:
        await cls._ensure_entry_schema(db)
        await db.execute(update(SystemInternalPowerEntry), [values])

    @classmethod
    async def delete(cls, db: AsyncSession, entry_id: int) -> None:
        await cls._ensure_entry_schema(db)
        await db.execute(delete(SystemInternalPowerEntry).where(SystemInternalPowerEntry.entry_id == entry_id))

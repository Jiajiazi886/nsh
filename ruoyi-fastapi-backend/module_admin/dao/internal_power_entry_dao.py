from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.internal_power_entry_do import SystemInternalPowerEntry
from module_admin.entity.vo.internal_power_entry_vo import InternalPowerEntryQueryModel
from utils.page_util import PageUtil


class InternalPowerEntryDao:
    """
    系统内功词条数据库操作层
    """

    @classmethod
    async def get_list(
        cls, db: AsyncSession, query_object: InternalPowerEntryQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
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
        result = await db.execute(
            select(SystemInternalPowerEntry)
            .where(SystemInternalPowerEntry.status == '0')
            .order_by(SystemInternalPowerEntry.entry_id)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, db: AsyncSession, entry_id: int) -> SystemInternalPowerEntry | None:
        result = await db.execute(
            select(SystemInternalPowerEntry).where(SystemInternalPowerEntry.entry_id == entry_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_name(cls, db: AsyncSession, entry_name: str) -> SystemInternalPowerEntry | None:
        result = await db.execute(
            select(SystemInternalPowerEntry).where(SystemInternalPowerEntry.entry_name == entry_name)
        )
        return result.scalars().first()

    @classmethod
    async def add(cls, db: AsyncSession, entry: SystemInternalPowerEntry) -> SystemInternalPowerEntry:
        db.add(entry)
        await db.flush()
        return entry

    @classmethod
    async def update(cls, db: AsyncSession, values: dict) -> None:
        await db.execute(update(SystemInternalPowerEntry), [values])

    @classmethod
    async def delete(cls, db: AsyncSession, entry_id: int) -> None:
        await db.execute(delete(SystemInternalPowerEntry).where(SystemInternalPowerEntry.entry_id == entry_id))

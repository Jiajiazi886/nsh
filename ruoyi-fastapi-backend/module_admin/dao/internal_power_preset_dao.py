from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.internal_power_preset_do import SystemInternalPowerPreset
from module_admin.entity.vo.internal_power_preset_vo import InternalPowerPresetModel, InternalPowerPresetQueryModel
from utils.page_util import PageUtil


class InternalPowerPresetDao:
    """
    系统内功预设数据库操作层
    """

    @classmethod
    async def get_list(
        cls, db: AsyncSession, query_object: InternalPowerPresetQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        query = (
            select(SystemInternalPowerPreset)
            .where(
                SystemInternalPowerPreset.name.like(f'%{query_object.name}%') if query_object.name else True,
                SystemInternalPowerPreset.element_key == query_object.element_key if query_object.element_key else True,
                SystemInternalPowerPreset.status == query_object.status if query_object.status else True,
            )
            .order_by(SystemInternalPowerPreset.preset_id)
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def list_enabled(cls, db: AsyncSession) -> list[SystemInternalPowerPreset]:
        result = await db.execute(
            select(SystemInternalPowerPreset)
            .where(SystemInternalPowerPreset.status == '0')
            .order_by(SystemInternalPowerPreset.preset_id)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, db: AsyncSession, preset_id: int) -> SystemInternalPowerPreset | None:
        result = await db.execute(
            select(SystemInternalPowerPreset).where(SystemInternalPowerPreset.preset_id == preset_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_name_element(
        cls, db: AsyncSession, name: str, element_key: str
    ) -> SystemInternalPowerPreset | None:
        result = await db.execute(
            select(SystemInternalPowerPreset).where(
                SystemInternalPowerPreset.name == name,
                SystemInternalPowerPreset.element_key == element_key,
            )
        )
        return result.scalars().first()

    @classmethod
    async def add(cls, db: AsyncSession, preset: SystemInternalPowerPreset) -> SystemInternalPowerPreset:
        db.add(preset)
        await db.flush()
        return preset

    @classmethod
    async def update(cls, db: AsyncSession, values: dict) -> None:
        await db.execute(update(SystemInternalPowerPreset), [values])

    @classmethod
    async def delete(cls, db: AsyncSession, preset_id: int) -> None:
        await db.execute(delete(SystemInternalPowerPreset).where(SystemInternalPowerPreset.preset_id == preset_id))

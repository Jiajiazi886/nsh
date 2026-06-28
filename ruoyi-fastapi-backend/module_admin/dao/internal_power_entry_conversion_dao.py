from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.internal_power_entry_conversion_do import (
    PersonalInternalPowerEntrySetting,
    PersonalInternalPowerEntryValue,
)


class InternalPowerEntryConversionDao:
    """
    个人内功词条换算数据库操作层
    """

    @classmethod
    async def get_setting(cls, db: AsyncSession, user_id: int) -> PersonalInternalPowerEntrySetting | None:
        result = await db.execute(
            select(PersonalInternalPowerEntrySetting).where(PersonalInternalPowerEntrySetting.user_id == user_id)
        )
        return result.scalars().first()

    @classmethod
    async def upsert_setting(cls, db: AsyncSession, setting: PersonalInternalPowerEntrySetting) -> None:
        await db.merge(setting)
        await db.flush()

    @classmethod
    async def list_values(cls, db: AsyncSession, user_id: int) -> list[PersonalInternalPowerEntryValue]:
        result = await db.execute(
            select(PersonalInternalPowerEntryValue)
            .where(PersonalInternalPowerEntryValue.user_id == user_id)
            .order_by(PersonalInternalPowerEntryValue.entry_name)
        )
        return list(result.scalars().all())

    @classmethod
    async def replace_values(
        cls, db: AsyncSession, user_id: int, values: list[PersonalInternalPowerEntryValue]
    ) -> None:
        await db.execute(delete(PersonalInternalPowerEntryValue).where(PersonalInternalPowerEntryValue.user_id == user_id))
        for value in values:
            db.add(value)
        await db.flush()

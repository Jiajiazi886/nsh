from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.internal_power_do import PersonalInternalPower


class InternalPowerDao:
    """
    个人内功数据库操作层
    """

    @classmethod
    async def list_by_user_id(cls, db: AsyncSession, user_id: int) -> list[PersonalInternalPower]:
        result = await db.execute(
            select(PersonalInternalPower)
            .where(PersonalInternalPower.user_id == user_id)
            .order_by(PersonalInternalPower.update_time.desc(), PersonalInternalPower.power_id.desc())
        )
        return list(result.scalars().all())

    @classmethod
    async def count_by_user_id(cls, db: AsyncSession, user_id: int) -> int:
        result = await db.execute(
            select(func.count(PersonalInternalPower.power_id)).where(PersonalInternalPower.user_id == user_id)
        )
        return int(result.scalar() or 0)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, power_id: int, user_id: int) -> PersonalInternalPower | None:
        result = await db.execute(
            select(PersonalInternalPower).where(
                PersonalInternalPower.power_id == power_id,
                PersonalInternalPower.user_id == user_id,
            )
        )
        return result.scalars().first()

    @classmethod
    async def add(cls, db: AsyncSession, power: PersonalInternalPower) -> PersonalInternalPower:
        db.add(power)
        await db.flush()
        return power

    @classmethod
    async def update(cls, db: AsyncSession, power_id: int, user_id: int, values: dict) -> None:
        await db.execute(
            update(PersonalInternalPower)
            .where(PersonalInternalPower.power_id == power_id, PersonalInternalPower.user_id == user_id)
            .values(**values)
        )

    @classmethod
    async def delete(cls, db: AsyncSession, power_id: int, user_id: int) -> None:
        await db.execute(
            delete(PersonalInternalPower).where(
                PersonalInternalPower.power_id == power_id,
                PersonalInternalPower.user_id == user_id,
            )
        )

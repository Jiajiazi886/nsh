from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.pvp_defense_profession_bonus_do import SystemPvpDefenseProfessionBonus


class PvpDefenseProfessionBonusDao:
    @classmethod
    async def list_all(cls, db: AsyncSession) -> list[SystemPvpDefenseProfessionBonus]:
        result = await db.execute(select(SystemPvpDefenseProfessionBonus))
        return list(result.scalars().all())

    @classmethod
    async def upsert(cls, db: AsyncSession, bonus: SystemPvpDefenseProfessionBonus) -> None:
        await db.merge(bonus)
        await db.flush()

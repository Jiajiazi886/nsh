from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.personal_defense_calculator_do import (
    PersonalDefenseCalculatorSetting,
    PersonalPvpAttackPanel,
)


class PersonalDefenseCalculatorDao:
    @classmethod
    async def list_panels(cls, db: AsyncSession, user_id: int) -> list[PersonalPvpAttackPanel]:
        result = await db.execute(
            select(PersonalPvpAttackPanel)
            .where(PersonalPvpAttackPanel.user_id == user_id)
            .order_by(PersonalPvpAttackPanel.sequence_no.asc())
        )
        return list(result.scalars().all())

    @classmethod
    async def get_panel(cls, db: AsyncSession, user_id: int, panel_id: int) -> PersonalPvpAttackPanel | None:
        result = await db.execute(
            select(PersonalPvpAttackPanel).where(
                PersonalPvpAttackPanel.user_id == user_id,
                PersonalPvpAttackPanel.panel_id == panel_id,
            )
        )
        return result.scalars().first()

    @classmethod
    async def get_next_sequence_no(cls, db: AsyncSession, user_id: int) -> int:
        result = await db.execute(
            select(func.coalesce(func.max(PersonalPvpAttackPanel.sequence_no), 0)).where(
                PersonalPvpAttackPanel.user_id == user_id
            )
        )
        return int(result.scalar_one() or 0) + 1

    @classmethod
    async def add_panel(cls, db: AsyncSession, panel: PersonalPvpAttackPanel) -> PersonalPvpAttackPanel:
        db.add(panel)
        await db.flush()
        return panel

    @classmethod
    async def update_panel(cls, db: AsyncSession, panel_id: int, panel_json: str) -> None:
        await db.execute(
            update(PersonalPvpAttackPanel)
            .where(PersonalPvpAttackPanel.panel_id == panel_id)
            .values(panel_json=panel_json, update_time=datetime.now())
        )

    @classmethod
    async def delete_panel(cls, db: AsyncSession, panel_id: int) -> None:
        await db.execute(delete(PersonalPvpAttackPanel).where(PersonalPvpAttackPanel.panel_id == panel_id))

    @classmethod
    async def get_setting(cls, db: AsyncSession, user_id: int) -> PersonalDefenseCalculatorSetting | None:
        result = await db.execute(
            select(PersonalDefenseCalculatorSetting).where(PersonalDefenseCalculatorSetting.user_id == user_id)
        )
        return result.scalars().first()

    @classmethod
    async def upsert_setting(cls, db: AsyncSession, setting: PersonalDefenseCalculatorSetting) -> None:
        await db.merge(setting)
        await db.flush()

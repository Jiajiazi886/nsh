from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.internal_power_panel_setting_do import PersonalInternalPowerPanelRecognitionHistory


class InternalPowerPanelRecognitionHistoryDao:
    """
    玩家面板识别历史数据库操作层
    """

    MAX_HISTORY_COUNT = 10

    @classmethod
    async def add(
        cls, db: AsyncSession, history: PersonalInternalPowerPanelRecognitionHistory
    ) -> PersonalInternalPowerPanelRecognitionHistory:
        db.add(history)
        await db.flush()
        return history

    @classmethod
    async def update(cls, db: AsyncSession, record_id: int, user_id: int, values: dict) -> None:
        await db.execute(
            update(PersonalInternalPowerPanelRecognitionHistory)
            .where(
                PersonalInternalPowerPanelRecognitionHistory.record_id == record_id,
                PersonalInternalPowerPanelRecognitionHistory.user_id == user_id,
            )
            .values(**values)
        )

    @classmethod
    async def list_by_user_id(
        cls, db: AsyncSession, user_id: int, limit: int
    ) -> list[PersonalInternalPowerPanelRecognitionHistory]:
        result = await db.execute(
            select(PersonalInternalPowerPanelRecognitionHistory)
            .where(PersonalInternalPowerPanelRecognitionHistory.user_id == user_id)
            .order_by(desc(PersonalInternalPowerPanelRecognitionHistory.create_time))
            .limit(limit)
        )
        return list(result.scalars().all())

    @classmethod
    async def clear_by_user_id(cls, db: AsyncSession, user_id: int) -> None:
        await db.execute(
            delete(PersonalInternalPowerPanelRecognitionHistory).where(
                PersonalInternalPowerPanelRecognitionHistory.user_id == user_id
            )
        )

    @classmethod
    async def trim_by_user_id(cls, db: AsyncSession, user_id: int) -> None:
        rows = await cls.list_by_user_id(db, user_id, cls.MAX_HISTORY_COUNT + 1)
        stale_ids = [row.record_id for row in rows[cls.MAX_HISTORY_COUNT :]]
        if stale_ids:
            await db.execute(
                delete(PersonalInternalPowerPanelRecognitionHistory).where(
                    PersonalInternalPowerPanelRecognitionHistory.record_id.in_(stale_ids),
                    PersonalInternalPowerPanelRecognitionHistory.user_id == user_id,
                )
            )

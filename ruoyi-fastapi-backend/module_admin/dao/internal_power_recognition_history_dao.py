from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.internal_power_do import PersonalInternalPowerRecognitionHistory


class InternalPowerRecognitionHistoryDao:
    """
    个人内功图片识别历史数据库操作层。
    """

    MAX_HISTORY_COUNT = 50

    @classmethod
    async def list_by_user_id(
        cls, db: AsyncSession, user_id: int, page_num: int = 1, page_size: int = 10
    ) -> PageModel:
        page_num = max(1, int(page_num or 1))
        page_size = min(10, max(1, int(page_size or 10)))
        total_result = await db.execute(
            select(func.count()).select_from(PersonalInternalPowerRecognitionHistory).where(
                PersonalInternalPowerRecognitionHistory.user_id == user_id
            )
        )
        total = min(int(total_result.scalar() or 0), cls.MAX_HISTORY_COUNT)
        latest_ids = (
            select(PersonalInternalPowerRecognitionHistory.record_id)
            .where(PersonalInternalPowerRecognitionHistory.user_id == user_id)
            .order_by(
                PersonalInternalPowerRecognitionHistory.create_time.desc(),
                PersonalInternalPowerRecognitionHistory.record_id.desc(),
            )
            .limit(cls.MAX_HISTORY_COUNT)
            .subquery()
        )
        result = await db.execute(
            select(PersonalInternalPowerRecognitionHistory)
            .where(PersonalInternalPowerRecognitionHistory.record_id.in_(select(latest_ids.c.record_id)))
            .order_by(
                PersonalInternalPowerRecognitionHistory.create_time.desc(),
                PersonalInternalPowerRecognitionHistory.record_id.desc(),
            )
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        return PageModel(
            rows=list(result.scalars().all()),
            pageNum=page_num,
            pageSize=page_size,
            total=total,
            hasNext=page_num * page_size < total,
        )

    @classmethod
    async def add(cls, db: AsyncSession, values: dict[str, Any]) -> PersonalInternalPowerRecognitionHistory:
        history = PersonalInternalPowerRecognitionHistory(**values)
        db.add(history)
        await db.flush()
        return history

    @classmethod
    async def update(cls, db: AsyncSession, record_id: int, user_id: int, values: dict[str, Any]) -> None:
        await db.execute(
            update(PersonalInternalPowerRecognitionHistory)
            .where(
                PersonalInternalPowerRecognitionHistory.record_id == record_id,
                PersonalInternalPowerRecognitionHistory.user_id == user_id,
            )
            .values(**values, update_time=datetime.now())
        )

    @classmethod
    async def clear_by_user_id(cls, db: AsyncSession, user_id: int) -> None:
        await db.execute(
            delete(PersonalInternalPowerRecognitionHistory).where(
                PersonalInternalPowerRecognitionHistory.user_id == user_id
            )
        )

    @classmethod
    async def trim_by_user_id(cls, db: AsyncSession, user_id: int, keep_count: int = MAX_HISTORY_COUNT) -> None:
        keep_result = await db.execute(
            select(PersonalInternalPowerRecognitionHistory.record_id)
            .where(PersonalInternalPowerRecognitionHistory.user_id == user_id)
            .order_by(
                PersonalInternalPowerRecognitionHistory.create_time.desc(),
                PersonalInternalPowerRecognitionHistory.record_id.desc(),
            )
            .limit(keep_count)
        )
        keep_ids = [int(record_id) for record_id in keep_result.scalars().all()]
        if len(keep_ids) < keep_count:
            return
        await db.execute(
            delete(PersonalInternalPowerRecognitionHistory).where(
                PersonalInternalPowerRecognitionHistory.user_id == user_id,
                PersonalInternalPowerRecognitionHistory.record_id.not_in(keep_ids),
            )
        )

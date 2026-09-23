from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.ai_usage_do import AiUsagePolicy


class AiUsagePolicyService:
    """管理唯一一条 AI 识图额度策略。"""

    POLICY_ID = 1

    @classmethod
    async def get_policy(cls, db: AsyncSession, *, for_update: bool = False) -> AiUsagePolicy:
        statement = select(AiUsagePolicy).where(AiUsagePolicy.policy_id == cls.POLICY_ID)
        if for_update:
            statement = statement.with_for_update()
        policy = (await db.execute(statement)).scalars().first()
        if policy is None:
            policy = AiUsagePolicy(
                policy_id=cls.POLICY_ID,
                default_recognition_count=0,
                vip_grant_count=0,
                update_by='system',
                update_time=datetime.now(),
            )
            db.add(policy)
            await db.flush()
        return policy

    @classmethod
    async def set_default_count(cls, db: AsyncSession, count: int, update_by: str) -> None:
        policy = await cls.get_policy(db, for_update=True)
        policy.default_recognition_count = count
        policy.update_by = update_by
        policy.update_time = datetime.now()

    @classmethod
    async def set_vip_grant_count(cls, db: AsyncSession, count: int, update_by: str) -> None:
        policy = await cls.get_policy(db, for_update=True)
        policy.vip_grant_count = count
        policy.update_by = update_by
        policy.update_time = datetime.now()

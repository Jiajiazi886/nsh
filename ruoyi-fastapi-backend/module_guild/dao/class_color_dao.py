from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from module_guild.entity.do.class_color_do import GuildClassColor

class ClassColorDao:
    @classmethod
    async def query_by_user(cls, db: AsyncSession, user_id: int) -> list[GuildClassColor]:
        stmt = select(GuildClassColor).where(GuildClassColor.user_id == user_id).order_by(GuildClassColor.class_name)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def delete_by_user(cls, db: AsyncSession, user_id: int):
        stmt = delete(GuildClassColor).where(GuildClassColor.user_id == user_id)
        await db.execute(stmt)

    @classmethod
    async def batch_insert(cls, db: AsyncSession, items: list[dict]):
        for item in items:
            db.add(GuildClassColor(**item))
        await db.flush()
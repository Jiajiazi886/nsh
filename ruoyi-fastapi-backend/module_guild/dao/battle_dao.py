from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from module_guild.entity.do.battle_do import GuildBattle, GuildBattleRecord


class BattleDao:
    @classmethod
    async def create_battle(cls, db: AsyncSession, battle_data: dict) -> int:
        battle = GuildBattle(**battle_data)
        db.add(battle)
        await db.flush()
        return battle.battle_id

    @classmethod
    async def batch_create_records(cls, db: AsyncSession, records: list[dict]):
        for record in records:
            db.add(GuildBattleRecord(**record))
        await db.flush()

    @classmethod
    async def get_battle_by_id(cls, db: AsyncSession, battle_id: int) -> GuildBattle | None:
        stmt = select(GuildBattle).where(GuildBattle.battle_id == battle_id, GuildBattle.del_flag == '0')
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def query_battle_list(cls, db: AsyncSession, user_id: int, page: int = 1, size: int = 10) -> dict:
        offset = (page - 1) * size
        stmt = (
            select(GuildBattle)
            .where(GuildBattle.user_id == user_id, GuildBattle.del_flag == '0')
            .order_by(GuildBattle.create_time.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        count_stmt = (
            select(func.count())
            .select_from(GuildBattle)
            .where(GuildBattle.user_id == user_id, GuildBattle.del_flag == '0')
        )
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        return {'rows': rows, 'total': total}

    @classmethod
    async def query_battle_records(cls, db: AsyncSession, battle_id: int) -> list:
        stmt = (
            select(GuildBattleRecord)
            .where(
                GuildBattleRecord.battle_id == battle_id,
                GuildBattleRecord.del_flag == '0',
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def soft_delete_battle(cls, db: AsyncSession, battle_id: int):
        stmt1 = (
            update(GuildBattle)
            .where(GuildBattle.battle_id == battle_id)
            .values(del_flag='1')
        )
        await db.execute(stmt1)
        stmt2 = (
            update(GuildBattleRecord)
            .where(GuildBattleRecord.battle_id == battle_id)
            .values(del_flag='1')
        )
        await db.execute(stmt2)
        await db.flush()

    @classmethod
    async def check_filename_exists(cls, db: AsyncSession, user_id: int, filename: str) -> bool:
        stmt = select(GuildBattle).where(
            GuildBattle.user_id == user_id,
            GuildBattle.battle_name == filename,
            GuildBattle.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def get_distinct_guild_names(cls, db: AsyncSession, user_id: int) -> list[str]:
        stmt = (
            select(func.distinct(GuildBattleRecord.guild_name))
            .join(GuildBattle, GuildBattle.battle_id == GuildBattleRecord.battle_id)
            .where(
                GuildBattle.user_id == user_id,
                GuildBattle.del_flag == '0',
                GuildBattleRecord.del_flag == '0',
            )
            .order_by(GuildBattleRecord.guild_name)
        )
        result = await db.execute(stmt)
        return [row[0] for row in result.fetchall()]
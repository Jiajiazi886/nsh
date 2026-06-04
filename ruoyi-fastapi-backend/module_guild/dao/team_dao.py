from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_guild.entity.do.team_do import GuildTeam
from module_guild.entity.do.member_do import GuildMember

class TeamDao:
    @classmethod
    async def query_teams_by_user(cls, db: AsyncSession, user_id: int) -> list:
        stmt = select(GuildTeam).where(GuildTeam.user_id == user_id).order_by(GuildTeam.team_type, GuildTeam.team_name)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def create_team(cls, db: AsyncSession, data: dict) -> GuildTeam:
        team = GuildTeam(**data)
        db.add(team)
        await db.flush()
        return team

    @classmethod
    async def delete_team(cls, db: AsyncSession, user_id: int, team_id: int):
        stmt = delete(GuildTeam).where(
            GuildTeam.id == team_id,
            GuildTeam.user_id == user_id,
        )
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def clear_team_members(cls, db: AsyncSession, team_id: int):
        stmt = update(GuildMember).where(GuildMember.team_id == team_id).values(team_id=None, squad_number=None)
        await db.execute(stmt)
        await db.flush()
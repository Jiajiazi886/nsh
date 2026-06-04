from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_guild.entity.do.member_do import GuildMember
from module_guild.entity.do.schedule_do import (
    GuildSchedule,
    GuildScheduleAssignment,
    GuildScheduleSquad,
    GuildScheduleTeam,
)


class ScheduleDao:
    @classmethod
    async def get_active_schedule(cls, db: AsyncSession, user_id: int) -> GuildSchedule | None:
        stmt = select(GuildSchedule).where(
            GuildSchedule.user_id == user_id,
            GuildSchedule.is_active == '1',
            GuildSchedule.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_schedule_by_id(cls, db: AsyncSession, user_id: int, schedule_id: int) -> GuildSchedule | None:
        stmt = select(GuildSchedule).where(
            GuildSchedule.schedule_id == schedule_id,
            GuildSchedule.user_id == user_id,
            GuildSchedule.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_schedule(cls, db: AsyncSession, data: dict) -> GuildSchedule:
        schedule = GuildSchedule(**data)
        db.add(schedule)
        await db.flush()
        return schedule

    @classmethod
    async def list_history(cls, db: AsyncSession, user_id: int) -> list[GuildSchedule]:
        stmt = (
            select(GuildSchedule)
            .where(
                GuildSchedule.user_id == user_id,
                GuildSchedule.is_active == '0',
                GuildSchedule.del_flag == '0',
            )
            .order_by(GuildSchedule.create_time.desc(), GuildSchedule.schedule_id.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def list_schedule_teams(cls, db: AsyncSession, schedule_id: int) -> list[GuildScheduleTeam]:
        stmt = (
            select(GuildScheduleTeam)
            .where(GuildScheduleTeam.schedule_id == schedule_id)
            .order_by(GuildScheduleTeam.order_num, GuildScheduleTeam.team_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def list_schedule_squads(cls, db: AsyncSession, team_ids: list[int]) -> list[GuildScheduleSquad]:
        if not team_ids:
            return []
        stmt = (
            select(GuildScheduleSquad)
            .where(GuildScheduleSquad.team_id.in_(team_ids))
            .order_by(GuildScheduleSquad.team_id, GuildScheduleSquad.order_num, GuildScheduleSquad.squad_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def list_schedule_assignments(cls, db: AsyncSession, schedule_id: int) -> list[GuildScheduleAssignment]:
        stmt = (
            select(GuildScheduleAssignment)
            .where(GuildScheduleAssignment.schedule_id == schedule_id)
            .order_by(GuildScheduleAssignment.team_id, GuildScheduleAssignment.squad_id, GuildScheduleAssignment.order_num)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_team(cls, db: AsyncSession, team_id: int) -> GuildScheduleTeam | None:
        result = await db.execute(select(GuildScheduleTeam).where(GuildScheduleTeam.team_id == team_id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_squad(cls, db: AsyncSession, squad_id: int) -> GuildScheduleSquad | None:
        result = await db.execute(select(GuildScheduleSquad).where(GuildScheduleSquad.squad_id == squad_id))
        return result.scalar_one_or_none()

    @classmethod
    async def count_teams(cls, db: AsyncSession, schedule_id: int) -> int:
        result = await db.execute(
            select(func.count()).select_from(GuildScheduleTeam).where(GuildScheduleTeam.schedule_id == schedule_id)
        )
        return result.scalar_one()

    @classmethod
    async def count_squads(cls, db: AsyncSession, team_id: int) -> int:
        result = await db.execute(
            select(func.count()).select_from(GuildScheduleSquad).where(GuildScheduleSquad.team_id == team_id)
        )
        return result.scalar_one()

    @classmethod
    async def count_squad_assignments(cls, db: AsyncSession, squad_id: int, exclude_member_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(GuildScheduleAssignment).where(GuildScheduleAssignment.squad_id == squad_id)
        if exclude_member_id:
            stmt = stmt.where(GuildScheduleAssignment.member_id != exclude_member_id)
        result = await db.execute(stmt)
        return result.scalar_one()

    @classmethod
    async def create_team(cls, db: AsyncSession, data: dict) -> GuildScheduleTeam:
        team = GuildScheduleTeam(**data)
        db.add(team)
        await db.flush()
        return team

    @classmethod
    async def create_squad(cls, db: AsyncSession, data: dict) -> GuildScheduleSquad:
        squad = GuildScheduleSquad(**data)
        db.add(squad)
        await db.flush()
        return squad

    @classmethod
    async def delete_team(cls, db: AsyncSession, schedule_id: int, team_id: int) -> None:
        await db.execute(delete(GuildScheduleAssignment).where(GuildScheduleAssignment.team_id == team_id))
        await db.execute(delete(GuildScheduleSquad).where(GuildScheduleSquad.team_id == team_id))
        await db.execute(delete(GuildScheduleTeam).where(GuildScheduleTeam.schedule_id == schedule_id, GuildScheduleTeam.team_id == team_id))
        await db.flush()

    @classmethod
    async def delete_squad(cls, db: AsyncSession, team_id: int, squad_id: int) -> None:
        await db.execute(delete(GuildScheduleAssignment).where(GuildScheduleAssignment.squad_id == squad_id))
        await db.execute(delete(GuildScheduleSquad).where(GuildScheduleSquad.team_id == team_id, GuildScheduleSquad.squad_id == squad_id))
        await db.flush()

    @classmethod
    async def clear_schedule_structure(cls, db: AsyncSession, schedule_id: int) -> None:
        teams = await cls.list_schedule_teams(db, schedule_id)
        team_ids = [team.team_id for team in teams]
        await db.execute(delete(GuildScheduleAssignment).where(GuildScheduleAssignment.schedule_id == schedule_id))
        if team_ids:
            await db.execute(delete(GuildScheduleSquad).where(GuildScheduleSquad.team_id.in_(team_ids)))
        await db.execute(delete(GuildScheduleTeam).where(GuildScheduleTeam.schedule_id == schedule_id))
        await db.flush()

    @classmethod
    async def upsert_assignment(cls, db: AsyncSession, data: dict) -> None:
        result = await db.execute(
            select(GuildScheduleAssignment).where(
                GuildScheduleAssignment.schedule_id == data['schedule_id'],
                GuildScheduleAssignment.member_id == data['member_id'],
            )
        )
        assignment = result.scalar_one_or_none()
        if assignment:
            await db.execute(
                update(GuildScheduleAssignment)
                .where(GuildScheduleAssignment.assignment_id == assignment.assignment_id)
                .values(**data)
            )
        else:
            db.add(GuildScheduleAssignment(**data))
        await db.flush()

    @classmethod
    async def clear_assignment(cls, db: AsyncSession, schedule_id: int, member_id: int) -> None:
        await db.execute(
            delete(GuildScheduleAssignment).where(
                GuildScheduleAssignment.schedule_id == schedule_id,
                GuildScheduleAssignment.member_id == member_id,
            )
        )
        await db.flush()

    @classmethod
    async def get_member(cls, db: AsyncSession, user_id: int, member_id: int) -> GuildMember | None:
        result = await db.execute(
            select(GuildMember).where(GuildMember.user_id == user_id, GuildMember.member_id == member_id)
        )
        return result.scalar_one_or_none()

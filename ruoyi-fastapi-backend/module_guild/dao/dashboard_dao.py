from datetime import datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.role_do import SysRole
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_guild.dao.battle_registration_dao import BattleRegistrationDao
from module_guild.entity.do.battle_do import GuildBattle, GuildBattleRecord
from module_guild.entity.do.battle_registration_do import GuildBattleInvite, GuildBattleRegistration
from module_guild.entity.do.join_application_do import GuildJoinApplication
from module_guild.entity.do.member_do import GuildMember
from module_guild.entity.do.profession_do import GuildProfession
from module_guild.entity.do.schedule_do import (
    GuildSchedule,
    GuildScheduleAssignment,
    GuildScheduleSquad,
    GuildScheduleTeam,
)


class DashboardDao:
    @classmethod
    async def list_enabled_professions(cls, db: AsyncSession) -> list[GuildProfession]:
        stmt = (
            select(GuildProfession)
            .where(GuildProfession.status == '0')
            .order_by(GuildProfession.order_num, GuildProfession.profession_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def count_guild_owners(cls, db: AsyncSession) -> int:
        stmt = (
            select(func.count(func.distinct(SysUser.user_id)))
            .select_from(SysUser)
            .join(SysUserRole, SysUserRole.user_id == SysUser.user_id)
            .join(SysRole, SysRole.role_id == SysUserRole.role_id)
            .where(
                SysRole.role_key == 'common',
                SysRole.status == '0',
                SysRole.del_flag == '0',
                SysUser.status == '0',
                SysUser.del_flag == '0',
            )
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def get_guild_owner(cls, db: AsyncSession, owner_user_id: int):
        stmt = select(SysUser.user_id, SysUser.user_name, SysUser.nick_name).where(
            SysUser.user_id == owner_user_id,
            SysUser.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.first()

    @classmethod
    async def get_active_member_by_user(cls, db: AsyncSession, member_user_id: int) -> GuildMember | None:
        stmt = (
            select(GuildMember)
            .where(GuildMember.member_user_id == member_user_id, GuildMember.is_active == '1')
            .order_by(GuildMember.member_id.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def count_members(
        cls,
        db: AsyncSession,
        owner_user_id: int | None = None,
        member_user_id: int | None = None,
        active_only: bool = False,
    ) -> int:
        stmt = select(func.count()).select_from(GuildMember)
        if owner_user_id is not None:
            stmt = stmt.where(GuildMember.user_id == owner_user_id)
        if member_user_id is not None:
            stmt = stmt.where(GuildMember.member_user_id == member_user_id)
        if active_only:
            stmt = stmt.where(GuildMember.is_active == '1')
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def list_class_distribution(
        cls,
        db: AsyncSession,
        profession_names: list[str],
        owner_user_id: int | None = None,
        member_user_id: int | None = None,
    ) -> list:
        if not profession_names:
            return []
        stmt = (
            select(GuildMember.player_class.label('class_name'), func.count().label('item_count'))
            .where(
                GuildMember.is_active == '1',
                GuildMember.player_class.in_(profession_names),
            )
            .group_by(GuildMember.player_class)
            .order_by(func.count().desc(), GuildMember.player_class)
        )
        if owner_user_id is not None:
            stmt = stmt.where(GuildMember.user_id == owner_user_id)
        if member_user_id is not None:
            stmt = stmt.where(GuildMember.member_user_id == member_user_id)
        result = await db.execute(stmt)
        return result.all()

    @classmethod
    async def count_unmatched_profession_members(
        cls,
        db: AsyncSession,
        profession_names: list[str],
        owner_user_id: int | None = None,
        member_user_id: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(GuildMember).where(GuildMember.is_active == '1')
        if profession_names:
            stmt = stmt.where(or_(GuildMember.player_class.is_(None), GuildMember.player_class == '', GuildMember.player_class.notin_(profession_names)))
        if owner_user_id is not None:
            stmt = stmt.where(GuildMember.user_id == owner_user_id)
        if member_user_id is not None:
            stmt = stmt.where(GuildMember.member_user_id == member_user_id)
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def list_member_roster_by_class(
        cls,
        db: AsyncSession,
        profession_names: list[str],
        owner_user_id: int | None = None,
        member_user_id: int | None = None,
    ) -> list[GuildMember]:
        stmt = select(GuildMember).where(GuildMember.is_active == '1')
        if profession_names:
            stmt = stmt.where(GuildMember.player_class.in_(profession_names))
        if owner_user_id is not None:
            stmt = stmt.where(GuildMember.user_id == owner_user_id)
        if member_user_id is not None:
            stmt = stmt.where(GuildMember.member_user_id == member_user_id)
        stmt = stmt.order_by(GuildMember.player_class, GuildMember.player_name, GuildMember.member_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_latest_active_invite(
        cls, db: AsyncSession, owner_user_id: int | None = None
    ) -> GuildBattleInvite | None:
        stmt = select(GuildBattleInvite).where(
            GuildBattleInvite.status == '0',
            GuildBattleInvite.expire_time >= datetime.now(),
            GuildBattleInvite.del_flag == '0',
        )
        if owner_user_id is not None:
            stmt = stmt.where(GuildBattleInvite.owner_user_id == owner_user_id)
        stmt = stmt.order_by(GuildBattleInvite.create_time.desc(), GuildBattleInvite.invite_id.desc()).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def count_registrations_for_invite(
        cls, db: AsyncSession, invite_id: int, registration_type: str = 'signup'
    ) -> int:
        await BattleRegistrationDao.ensure_registration_schema(db)
        stmt = select(func.count()).select_from(GuildBattleRegistration).where(
            GuildBattleRegistration.invite_id == invite_id,
            GuildBattleRegistration.registration_type == registration_type,
            GuildBattleRegistration.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def list_registration_class_distribution(
        cls, db: AsyncSession, invite_id: int, registration_type: str = 'signup'
    ) -> list:
        await BattleRegistrationDao.ensure_registration_schema(db)
        stmt = (
            select(GuildBattleRegistration.player_class.label('class_name'), func.count().label('item_count'))
            .where(
                GuildBattleRegistration.invite_id == invite_id,
                GuildBattleRegistration.registration_type == registration_type,
                GuildBattleRegistration.del_flag == '0',
            )
            .group_by(GuildBattleRegistration.player_class)
            .order_by(func.count().desc(), GuildBattleRegistration.player_class)
        )
        result = await db.execute(stmt)
        return result.all()

    @classmethod
    async def list_registrations_for_invite(
        cls, db: AsyncSession, invite_id: int, limit: int = 12, registration_type: str = 'signup'
    ) -> list[GuildBattleRegistration]:
        await BattleRegistrationDao.ensure_registration_schema(db)
        stmt = (
            select(GuildBattleRegistration)
            .where(
                GuildBattleRegistration.invite_id == invite_id,
                GuildBattleRegistration.registration_type == registration_type,
                GuildBattleRegistration.del_flag == '0',
            )
            .order_by(GuildBattleRegistration.apply_time.desc(), GuildBattleRegistration.registration_id.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def list_join_applications(
        cls, db: AsyncSession, guild_id: int | None = None, limit: int = 12
    ) -> list[GuildJoinApplication]:
        stmt = select(GuildJoinApplication).where(GuildJoinApplication.del_flag == '0')
        if guild_id is not None:
            stmt = stmt.where(GuildJoinApplication.guild_id == guild_id)
        stmt = stmt.order_by(
            case((GuildJoinApplication.review_status == '0', 0), else_=1),
            GuildJoinApplication.apply_time.desc(),
            GuildJoinApplication.application_id.desc(),
        ).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_battle_summary(cls, db: AsyncSession, owner_user_id: int | None = None) -> dict:
        stmt = select(
            func.count().label('total'),
            func.coalesce(func.sum(case((GuildBattle.status == '2', 1), else_=0)), 0).label('completed'),
            func.coalesce(func.sum(case((GuildBattle.battle_result.like('%胜%'), 1), else_=0)), 0).label('wins'),
            func.coalesce(
                func.sum(
                    case((or_(GuildBattle.battle_result.like('%败%'), GuildBattle.battle_result.like('%负%')), 1), else_=0)
                ),
                0,
            ).label('losses'),
        ).where(GuildBattle.del_flag == '0')
        if owner_user_id is not None:
            stmt = stmt.where(GuildBattle.user_id == owner_user_id)
        result = await db.execute(stmt)
        row = result.first()
        return {
            'total': row.total or 0,
            'completed': row.completed or 0,
            'wins': row.wins or 0,
            'losses': row.losses or 0,
        }

    @classmethod
    async def list_latest_battles(
        cls, db: AsyncSession, owner_user_id: int | None = None, limit: int = 5
    ) -> list[GuildBattle]:
        stmt = select(GuildBattle).where(GuildBattle.del_flag == '0')
        if owner_user_id is not None:
            stmt = stmt.where(GuildBattle.user_id == owner_user_id)
        stmt = stmt.order_by(GuildBattle.create_time.desc(), GuildBattle.battle_id.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def list_record_summaries(cls, db: AsyncSession, battle_ids: list[int]) -> list:
        if not battle_ids:
            return []
        stmt = (
            select(
                GuildBattleRecord.battle_id,
                GuildBattleRecord.guild_name,
                func.count().label('participants'),
                func.coalesce(func.sum(GuildBattleRecord.kills), 0).label('kills'),
                func.coalesce(func.sum(GuildBattleRecord.assists), 0).label('assists'),
                func.coalesce(func.sum(GuildBattleRecord.resources), 0).label('resources'),
                func.coalesce(func.sum(GuildBattleRecord.dmg_to_players), 0).label('damage'),
                func.coalesce(func.sum(GuildBattleRecord.healing), 0).label('healing'),
                func.coalesce(func.sum(GuildBattleRecord.deaths), 0).label('deaths'),
                func.coalesce(func.sum(GuildBattleRecord.revives), 0).label('revives'),
            )
            .where(GuildBattleRecord.battle_id.in_(battle_ids), GuildBattleRecord.del_flag == '0')
            .group_by(GuildBattleRecord.battle_id, GuildBattleRecord.guild_name)
            .order_by(GuildBattleRecord.battle_id.desc(), GuildBattleRecord.guild_name)
        )
        result = await db.execute(stmt)
        return result.all()

    @classmethod
    async def list_top_records(cls, db: AsyncSession, battle_id: int | None, limit: int = 6) -> list[GuildBattleRecord]:
        if not battle_id:
            return []
        stmt = (
            select(GuildBattleRecord)
            .where(GuildBattleRecord.battle_id == battle_id, GuildBattleRecord.del_flag == '0')
            .order_by(
                GuildBattleRecord.kills.desc(),
                GuildBattleRecord.assists.desc(),
                GuildBattleRecord.dmg_to_players.desc(),
                GuildBattleRecord.record_id,
            )
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def count_pending_join_applications(
        cls,
        db: AsyncSession,
        guild_id: int | None = None,
        applicant_user_id: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(GuildJoinApplication).where(
            GuildJoinApplication.review_status == '0',
            GuildJoinApplication.del_flag == '0',
        )
        if guild_id is not None:
            stmt = stmt.where(GuildJoinApplication.guild_id == guild_id)
        if applicant_user_id is not None:
            stmt = stmt.where(GuildJoinApplication.applicant_user_id == applicant_user_id)
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def list_my_applications(cls, db: AsyncSession, applicant_user_id: int, limit: int = 5) -> list[GuildJoinApplication]:
        stmt = (
            select(GuildJoinApplication)
            .where(GuildJoinApplication.applicant_user_id == applicant_user_id)
            .order_by(GuildJoinApplication.apply_time.desc(), GuildJoinApplication.application_id.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def count_battle_registrations(
        cls,
        db: AsyncSession,
        owner_user_id: int | None = None,
        applicant_user_id: int | None = None,
        status: str | None = None,
    ) -> int:
        await BattleRegistrationDao.ensure_registration_schema(db)
        stmt = select(func.count()).select_from(GuildBattleRegistration).where(GuildBattleRegistration.del_flag == '0')
        if owner_user_id is not None:
            stmt = stmt.where(GuildBattleRegistration.owner_user_id == owner_user_id)
        if applicant_user_id is not None:
            stmt = stmt.where(GuildBattleRegistration.applicant_user_id == applicant_user_id)
        if status is not None:
            stmt = stmt.where(GuildBattleRegistration.approval_status == status)
        stmt = stmt.where(GuildBattleRegistration.registration_type == 'signup')
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def list_active_schedules(
        cls, db: AsyncSession, owner_user_id: int | None = None, limit: int = 20
    ) -> list[GuildSchedule]:
        stmt = select(GuildSchedule).where(GuildSchedule.is_active == '1', GuildSchedule.del_flag == '0')
        if owner_user_id is not None:
            stmt = stmt.where(GuildSchedule.user_id == owner_user_id)
        stmt = stmt.order_by(GuildSchedule.update_time.desc(), GuildSchedule.schedule_id.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_schedule_counts(cls, db: AsyncSession, schedule_ids: list[int]) -> dict[int, dict]:
        if not schedule_ids:
            return {}
        counts = {
            schedule_id: {'team_count': 0, 'squad_count': 0, 'assignment_count': 0}
            for schedule_id in schedule_ids
        }

        team_rows = await db.execute(
            select(GuildScheduleTeam.schedule_id, func.count().label('item_count'))
            .where(GuildScheduleTeam.schedule_id.in_(schedule_ids))
            .group_by(GuildScheduleTeam.schedule_id)
        )
        for row in team_rows.all():
            counts[row.schedule_id]['team_count'] = row.item_count or 0

        squad_rows = await db.execute(
            select(GuildScheduleTeam.schedule_id, func.count(GuildScheduleSquad.squad_id).label('item_count'))
            .select_from(GuildScheduleSquad)
            .join(GuildScheduleTeam, GuildScheduleTeam.team_id == GuildScheduleSquad.team_id)
            .where(GuildScheduleTeam.schedule_id.in_(schedule_ids))
            .group_by(GuildScheduleTeam.schedule_id)
        )
        for row in squad_rows.all():
            counts[row.schedule_id]['squad_count'] = row.item_count or 0

        assignment_rows = await db.execute(
            select(GuildScheduleAssignment.schedule_id, func.count().label('item_count'))
            .where(GuildScheduleAssignment.schedule_id.in_(schedule_ids))
            .group_by(GuildScheduleAssignment.schedule_id)
        )
        for row in assignment_rows.all():
            counts[row.schedule_id]['assignment_count'] = row.item_count or 0

        return counts

    @classmethod
    async def get_member_schedule_assignment(
        cls, db: AsyncSession, schedule_id: int, member_id: int
    ):
        stmt = (
            select(
                GuildScheduleAssignment,
                GuildScheduleTeam.team_name.label('team_name'),
                GuildScheduleSquad.squad_name.label('squad_name'),
            )
            .join(GuildScheduleTeam, GuildScheduleTeam.team_id == GuildScheduleAssignment.team_id, isouter=True)
            .join(GuildScheduleSquad, GuildScheduleSquad.squad_id == GuildScheduleAssignment.squad_id, isouter=True)
            .where(
                GuildScheduleAssignment.schedule_id == schedule_id,
                GuildScheduleAssignment.member_id == member_id,
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.first()

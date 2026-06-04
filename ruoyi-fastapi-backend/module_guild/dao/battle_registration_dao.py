from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_guild.entity.do.battle_registration_do import GuildBattleInvite, GuildBattleRegistration
from module_guild.entity.do.member_do import GuildMember


class BattleRegistrationDao:
    @classmethod
    async def create_invite(cls, db: AsyncSession, data: dict) -> GuildBattleInvite:
        invite = GuildBattleInvite(**data)
        db.add(invite)
        await db.flush()
        return invite

    @classmethod
    async def get_invite_by_code(cls, db: AsyncSession, invite_code: str) -> GuildBattleInvite | None:
        stmt = select(GuildBattleInvite).where(
            GuildBattleInvite.invite_code == invite_code,
            GuildBattleInvite.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list_invites(cls, db: AsyncSession, owner_user_id: int | None = None) -> list[GuildBattleInvite]:
        stmt = select(GuildBattleInvite).where(GuildBattleInvite.del_flag == '0')
        if owner_user_id is not None:
            stmt = stmt.where(GuildBattleInvite.owner_user_id == owner_user_id)
        stmt = stmt.order_by(GuildBattleInvite.create_time.desc(), GuildBattleInvite.invite_id.desc()).limit(100)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def search_members(cls, db: AsyncSession, owner_user_id: int, keyword: str) -> list[GuildMember]:
        stmt = (
            select(GuildMember)
            .where(
                GuildMember.user_id == owner_user_id,
                GuildMember.is_active == '1',
                GuildMember.player_name.like(f'%{keyword}%'),
            )
            .order_by(GuildMember.player_name)
            .limit(20)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_member_for_invite(cls, db: AsyncSession, owner_user_id: int, member_id: int) -> GuildMember | None:
        stmt = select(GuildMember).where(
            GuildMember.user_id == owner_user_id,
            GuildMember.member_id == member_id,
            GuildMember.is_active == '1',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def has_effective_registration(cls, db: AsyncSession, invite_id: int, member_id: int) -> bool:
        stmt = select(func.count()).select_from(GuildBattleRegistration).where(
            GuildBattleRegistration.invite_id == invite_id,
            GuildBattleRegistration.member_id == member_id,
            GuildBattleRegistration.del_flag == '0',
            GuildBattleRegistration.approval_status.in_(['0', '1']),
        )
        result = await db.execute(stmt)
        return (result.scalar() or 0) > 0

    @classmethod
    async def create_registration(cls, db: AsyncSession, data: dict) -> GuildBattleRegistration:
        registration = GuildBattleRegistration(**data)
        db.add(registration)
        await db.flush()
        return registration

    @classmethod
    async def get_pending_registration_by_id(
        cls, db: AsyncSession, registration_id: int
    ) -> GuildBattleRegistration | None:
        stmt = select(GuildBattleRegistration).where(
            GuildBattleRegistration.registration_id == registration_id,
            GuildBattleRegistration.approval_status == '0',
            GuildBattleRegistration.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list_registrations(
        cls, db: AsyncSession, owner_user_id: int | None = None, status: str | None = None
    ) -> list[GuildBattleRegistration]:
        stmt = select(GuildBattleRegistration).where(GuildBattleRegistration.del_flag == '0')
        if owner_user_id is not None:
            stmt = stmt.where(GuildBattleRegistration.owner_user_id == owner_user_id)
        if status is not None:
            stmt = stmt.where(GuildBattleRegistration.approval_status == status)
        stmt = stmt.order_by(GuildBattleRegistration.apply_time.desc(), GuildBattleRegistration.registration_id.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def update_registration(cls, db: AsyncSession, registration_id: int, data: dict) -> None:
        stmt = update(GuildBattleRegistration).where(
            GuildBattleRegistration.registration_id == registration_id
        ).values(**data)
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def count_approved_for_invite(cls, db: AsyncSession, invite_id: int) -> int:
        stmt = select(func.count()).select_from(GuildBattleRegistration).where(
            GuildBattleRegistration.invite_id == invite_id,
            GuildBattleRegistration.approval_status == '1',
            GuildBattleRegistration.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def mark_expired_invites(cls, db: AsyncSession) -> None:
        stmt = update(GuildBattleInvite).where(
            GuildBattleInvite.expire_time < datetime.now(),
            GuildBattleInvite.status == '0',
            GuildBattleInvite.del_flag == '0',
        ).values(status='1')
        await db.execute(stmt)
        await db.flush()

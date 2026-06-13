from datetime import datetime

from sqlalchemy import func, inspect, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_guild.entity.do.battle_registration_do import GuildBattleInvite, GuildBattleRegistration
from module_guild.entity.do.member_do import GuildMember


class BattleRegistrationDao:
    _registration_schema_checked = False

    @classmethod
    async def ensure_registration_schema(cls, db: AsyncSession) -> None:
        await cls._ensure_registration_schema(db)

    @classmethod
    async def _ensure_registration_schema(cls, db: AsyncSession) -> None:
        if cls._registration_schema_checked:
            return

        def _inspect_columns(sync_session) -> tuple[str, set[str], bool]:
            bind = sync_session.get_bind()
            dialect_name = bind.dialect.name
            inspector = inspect(bind)
            table_exists = 'guild_battle_registration' in inspector.get_table_names()
            if not table_exists:
                return dialect_name, set(), False
            columns = {column['name'] for column in inspector.get_columns('guild_battle_registration')}
            return dialect_name, columns, True

        dialect_name, columns, table_exists = await db.run_sync(_inspect_columns)
        if not table_exists:
            cls._registration_schema_checked = True
            return

        statements: list[str] = []
        if 'registration_type' not in columns:
            if dialect_name == 'postgresql':
                statements.append("ALTER TABLE guild_battle_registration ADD COLUMN registration_type VARCHAR(20) DEFAULT 'signup'")
            else:
                statements.append(
                    "ALTER TABLE guild_battle_registration ADD COLUMN registration_type varchar(20) DEFAULT 'signup' COMMENT '申请类型(signup/leave)' AFTER team_id"
                )
        if statements:
            for statement in statements:
                await db.execute(text(statement))
            if 'registration_type' not in columns:
                await db.execute(
                    text(
                        "UPDATE guild_battle_registration SET registration_type = 'signup' "
                        "WHERE registration_type IS NULL OR registration_type = ''"
                    )
                )
            await db.commit()
        cls._registration_schema_checked = True

    @classmethod
    async def create_invite(cls, db: AsyncSession, data: dict) -> GuildBattleInvite:
        invite = GuildBattleInvite(**data)
        db.add(invite)
        await db.flush()
        return invite

    @classmethod
    async def disable_active_invites_for_owner(cls, db: AsyncSession, owner_user_id: int) -> None:
        stmt = update(GuildBattleInvite).where(
            GuildBattleInvite.owner_user_id == owner_user_id,
            GuildBattleInvite.status == '0',
            GuildBattleInvite.expire_time >= datetime.now(),
            GuildBattleInvite.del_flag == '0',
        ).values(status='1')
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def get_invite_by_id(cls, db: AsyncSession, invite_id: int) -> GuildBattleInvite | None:
        stmt = select(GuildBattleInvite).where(
            GuildBattleInvite.invite_id == invite_id,
            GuildBattleInvite.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

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
        await cls._ensure_registration_schema(db)
        stmt = select(func.count()).select_from(GuildBattleRegistration).where(
            GuildBattleRegistration.invite_id == invite_id,
            GuildBattleRegistration.member_id == member_id,
            GuildBattleRegistration.registration_type == 'signup',
            GuildBattleRegistration.del_flag == '0',
            GuildBattleRegistration.approval_status.in_(['0', '1']),
        )
        result = await db.execute(stmt)
        return (result.scalar() or 0) > 0

    @classmethod
    async def has_effective_registration_by_type(
        cls, db: AsyncSession, invite_id: int, member_id: int, registration_type: str
    ) -> bool:
        await cls._ensure_registration_schema(db)
        stmt = select(func.count()).select_from(GuildBattleRegistration).where(
            GuildBattleRegistration.invite_id == invite_id,
            GuildBattleRegistration.member_id == member_id,
            GuildBattleRegistration.registration_type == registration_type,
            GuildBattleRegistration.del_flag == '0',
            GuildBattleRegistration.approval_status.in_(['0', '1']),
        )
        result = await db.execute(stmt)
        return (result.scalar() or 0) > 0

    @classmethod
    async def get_effective_registration(
        cls,
        db: AsyncSession,
        invite_id: int,
        member_id: int,
        registration_type: str | None = None,
    ) -> GuildBattleRegistration | None:
        await cls._ensure_registration_schema(db)
        stmt = select(GuildBattleRegistration).where(
            GuildBattleRegistration.invite_id == invite_id,
            GuildBattleRegistration.member_id == member_id,
            GuildBattleRegistration.del_flag == '0',
            GuildBattleRegistration.approval_status.in_(['0', '1']),
        )
        if registration_type:
            stmt = stmt.where(GuildBattleRegistration.registration_type == registration_type)
        stmt = stmt.order_by(GuildBattleRegistration.apply_time.desc(), GuildBattleRegistration.registration_id.desc())
        result = await db.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    @classmethod
    async def list_effective_registrations_for_members(
        cls, db: AsyncSession, invite_id: int, member_ids: list[int]
    ) -> list[GuildBattleRegistration]:
        await cls._ensure_registration_schema(db)
        if not member_ids:
            return []
        stmt = (
            select(GuildBattleRegistration)
            .where(
                GuildBattleRegistration.invite_id == invite_id,
                GuildBattleRegistration.member_id.in_(member_ids),
                GuildBattleRegistration.del_flag == '0',
                GuildBattleRegistration.approval_status.in_(['0', '1']),
            )
            .order_by(GuildBattleRegistration.apply_time.desc(), GuildBattleRegistration.registration_id.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def create_registration(cls, db: AsyncSession, data: dict) -> GuildBattleRegistration:
        await cls._ensure_registration_schema(db)
        registration = GuildBattleRegistration(**data)
        db.add(registration)
        await db.flush()
        return registration

    @classmethod
    async def get_pending_registration_by_id(
        cls, db: AsyncSession, registration_id: int
    ) -> GuildBattleRegistration | None:
        await cls._ensure_registration_schema(db)
        stmt = select(GuildBattleRegistration).where(
            GuildBattleRegistration.registration_id == registration_id,
            GuildBattleRegistration.approval_status == '0',
            GuildBattleRegistration.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list_registrations(
        cls,
        db: AsyncSession,
        owner_user_id: int | None = None,
        status: str | None = None,
        invite_id: int | None = None,
        registration_type: str | None = 'signup',
        status_list: list[str] | None = None,
    ) -> list[GuildBattleRegistration]:
        await cls._ensure_registration_schema(db)
        stmt = select(GuildBattleRegistration).where(GuildBattleRegistration.del_flag == '0')
        if owner_user_id is not None:
            stmt = stmt.where(GuildBattleRegistration.owner_user_id == owner_user_id)
        if status_list:
            stmt = stmt.where(GuildBattleRegistration.approval_status.in_(status_list))
        elif status is not None:
            stmt = stmt.where(GuildBattleRegistration.approval_status == status)
        if invite_id is not None:
            stmt = stmt.where(GuildBattleRegistration.invite_id == invite_id)
        if registration_type:
            stmt = stmt.where(GuildBattleRegistration.registration_type == registration_type)
        stmt = stmt.order_by(GuildBattleRegistration.apply_time.desc(), GuildBattleRegistration.registration_id.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def update_registration(cls, db: AsyncSession, registration_id: int, data: dict) -> None:
        await cls._ensure_registration_schema(db)
        stmt = update(GuildBattleRegistration).where(
            GuildBattleRegistration.registration_id == registration_id
        ).values(**data)
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def cancel_effective_registration(
        cls, db: AsyncSession, invite_id: int, member_id: int, registration_type: str
    ) -> int:
        await cls._ensure_registration_schema(db)
        stmt = (
            update(GuildBattleRegistration)
            .where(
                GuildBattleRegistration.invite_id == invite_id,
                GuildBattleRegistration.member_id == member_id,
                GuildBattleRegistration.registration_type == registration_type,
                GuildBattleRegistration.del_flag == '0',
                GuildBattleRegistration.approval_status.in_(['0', '1']),
            )
            .values(del_flag='1')
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount or 0

    @classmethod
    async def count_approved_for_invite(cls, db: AsyncSession, invite_id: int) -> int:
        await cls._ensure_registration_schema(db)
        stmt = select(func.count()).select_from(GuildBattleRegistration).where(
            GuildBattleRegistration.invite_id == invite_id,
            GuildBattleRegistration.registration_type == 'signup',
            GuildBattleRegistration.approval_status == '1',
            GuildBattleRegistration.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def count_registrations_for_invite(cls, db: AsyncSession, invite_id: int) -> int:
        await cls._ensure_registration_schema(db)
        stmt = select(func.count()).select_from(GuildBattleRegistration).where(
            GuildBattleRegistration.invite_id == invite_id,
            GuildBattleRegistration.registration_type == 'signup',
            GuildBattleRegistration.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def disable_invite(cls, db: AsyncSession, invite_id: int) -> None:
        stmt = update(GuildBattleInvite).where(
            GuildBattleInvite.invite_id == invite_id,
            GuildBattleInvite.del_flag == '0',
        ).values(status='1')
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def delete_invite(cls, db: AsyncSession, invite_id: int) -> None:
        stmt = update(GuildBattleInvite).where(
            GuildBattleInvite.invite_id == invite_id,
            GuildBattleInvite.del_flag == '0',
        ).values(del_flag='1')
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def mark_expired_invites(cls, db: AsyncSession) -> None:
        stmt = update(GuildBattleInvite).where(
            GuildBattleInvite.expire_time < datetime.now(),
            GuildBattleInvite.status == '0',
            GuildBattleInvite.del_flag == '0',
        ).values(status='1')
        await db.execute(stmt)
        await db.flush()

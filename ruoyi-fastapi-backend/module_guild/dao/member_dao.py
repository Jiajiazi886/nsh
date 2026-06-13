from sqlalchemy import delete, func, inspect, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_guild.dao.battle_registration_dao import BattleRegistrationDao
from module_guild.entity.do.battle_do import GuildBattle, GuildBattleRecord
from module_guild.entity.do.battle_registration_do import GuildBattleInvite, GuildBattleRegistration
from module_guild.entity.do.member_do import GuildMember


class MemberDao:
    _schema_checked = False

    @classmethod
    async def _ensure_member_schema(cls, db: AsyncSession) -> None:
        if cls._schema_checked:
            return

        def _inspect_columns(sync_session) -> tuple[str, set[str], bool]:
            bind = sync_session.get_bind()
            dialect_name = bind.dialect.name
            inspector = inspect(bind)
            table_exists = 'guild_member' in inspector.get_table_names()
            if not table_exists:
                return dialect_name, set(), False
            columns = {column['name'] for column in inspector.get_columns('guild_member')}
            return dialect_name, columns, True

        dialect_name, columns, table_exists = await db.run_sync(_inspect_columns)
        if not table_exists:
            cls._schema_checked = True
            return

        statements: list[str] = []
        if 'member_user_id' not in columns:
            if dialect_name == 'postgresql':
                statements.append('ALTER TABLE guild_member ADD COLUMN member_user_id BIGINT NOT NULL DEFAULT 0')
            else:
                statements.append(
                    "ALTER TABLE guild_member ADD COLUMN member_user_id bigint NOT NULL DEFAULT 0 COMMENT '成员账号用户ID' AFTER user_id"
                )
        if 'source_type' not in columns:
            if dialect_name == 'postgresql':
                statements.append("ALTER TABLE guild_member ADD COLUMN source_type VARCHAR(20) DEFAULT 'manual'")
            else:
                statements.append(
                    "ALTER TABLE guild_member ADD COLUMN source_type varchar(20) DEFAULT 'manual' COMMENT '成员来源' AFTER is_active"
                )
        if statements:
            for statement in statements:
                await db.execute(text(statement))
            if 'member_user_id' not in columns:
                await db.execute(
                    text('UPDATE guild_member SET member_user_id = COALESCE(member_user_id, 0) WHERE member_user_id IS NULL')
                )
            if 'source_type' not in columns:
                await db.execute(
                    text("UPDATE guild_member SET source_type = 'manual' WHERE source_type IS NULL OR source_type = ''")
                )
            await db.commit()
        cls._schema_checked = True

    @classmethod
    async def query_member_list(cls, db: AsyncSession, user_id: int) -> list:
        await cls._ensure_member_schema(db)
        stmt = (
            select(GuildMember)
            .where(GuildMember.user_id == user_id, GuildMember.is_active == '1')
            .order_by(GuildMember.member_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def query_member_list_payload(cls, db: AsyncSession, user_id: int) -> list[dict]:
        await cls._ensure_member_schema(db)
        stmt = (
            select(
                GuildMember.member_id,
                GuildMember.guild_id,
                GuildMember.user_id,
                GuildMember.member_user_id,
                GuildMember.player_name,
                GuildMember.player_class,
                GuildMember.secondary_class,
                GuildMember.role_in_guild,
                GuildMember.is_active,
                GuildMember.source_type,
                GuildMember.join_time,
                GuildMember.remark,
                GuildMember.team_id,
                GuildMember.squad_number,
            )
            .where(GuildMember.user_id == user_id, GuildMember.is_active == '1')
            .order_by(GuildMember.member_id)
        )
        result = await db.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

    @classmethod
    async def list_leave_records_for_members(cls, db: AsyncSession, user_id: int, member_ids: list[int]) -> list:
        await BattleRegistrationDao.ensure_registration_schema(db)
        if not member_ids:
            return []
        stmt = (
            select(
                GuildBattleRegistration.member_id,
                GuildBattleRegistration.registration_id,
                GuildBattleRegistration.approval_status,
                GuildBattleInvite.battle_name,
                GuildBattleInvite.battle_time,
            )
            .select_from(GuildBattleRegistration)
            .join(GuildBattleInvite, GuildBattleInvite.invite_id == GuildBattleRegistration.invite_id, isouter=True)
            .where(
                GuildBattleRegistration.owner_user_id == user_id,
                GuildBattleRegistration.member_id.in_(member_ids),
                GuildBattleRegistration.registration_type == 'leave',
                GuildBattleRegistration.approval_status.in_(['0', '1']),
                GuildBattleRegistration.del_flag == '0',
            )
            .order_by(GuildBattleInvite.battle_time.desc(), GuildBattleRegistration.apply_time.desc())
        )
        result = await db.execute(stmt)
        return result.all()

    @classmethod
    async def get_member_by_id(cls, db: AsyncSession, member_id: int) -> GuildMember | None:
        await cls._ensure_member_schema(db)
        stmt = select(GuildMember).where(GuildMember.member_id == member_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_member_by_member_user(cls, db: AsyncSession, member_user_id: int) -> GuildMember | None:
        await cls._ensure_member_schema(db)
        stmt = (
            select(GuildMember)
            .where(GuildMember.member_user_id == member_user_id, GuildMember.is_active == '1')
            .order_by(GuildMember.member_id.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_active_member_profile_by_user(cls, db: AsyncSession, member_user_id: int) -> GuildMember | None:
        await cls._ensure_member_schema(db)
        stmt = (
            select(GuildMember)
            .where(GuildMember.member_user_id == member_user_id, GuildMember.is_active == '1')
            .order_by(GuildMember.member_id.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_member_by_guild_and_member_user(
        cls, db: AsyncSession, guild_owner_user_id: int, member_user_id: int
    ) -> GuildMember | None:
        await cls._ensure_member_schema(db)
        stmt = (
            select(GuildMember)
            .where(GuildMember.user_id == guild_owner_user_id, GuildMember.member_user_id == member_user_id)
            .order_by(GuildMember.member_id.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def update_member(cls, db: AsyncSession, member_id: int, data: dict) -> None:
        await cls._ensure_member_schema(db)
        stmt = update(GuildMember).where(GuildMember.member_id == member_id).values(**data)
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def batch_delete_members(cls, db: AsyncSession, user_id: int, member_ids: list[int]) -> int:
        await cls._ensure_member_schema(db)
        stmt = delete(GuildMember).where(
            GuildMember.member_id.in_(member_ids),
            GuildMember.user_id == user_id,
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount

    @classmethod
    async def create_member(cls, db: AsyncSession, data: dict) -> GuildMember:
        await cls._ensure_member_schema(db)
        member = GuildMember(**data)
        db.add(member)
        await db.flush()
        return member

    @classmethod
    async def check_member_exists(cls, db: AsyncSession, user_id: int, player_name: str) -> bool:
        await cls._ensure_member_schema(db)
        stmt = select(GuildMember).where(
            GuildMember.user_id == user_id,
            GuildMember.player_name == player_name,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def batch_insert_members(cls, db: AsyncSession, members_list: list[dict]) -> None:
        await cls._ensure_member_schema(db)
        for m in members_list:
            db.add(GuildMember(**m))
        await db.flush()

    @classmethod
    async def delete_member_by_member_user(cls, db: AsyncSession, member_user_id: int) -> int:
        await cls._ensure_member_schema(db)
        stmt = delete(GuildMember).where(GuildMember.member_user_id == member_user_id)
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount or 0

    @classmethod
    async def get_battle_guild_names(cls, db: AsyncSession, user_id: int, battle_id: int) -> list[str]:
        stmt = (
            select(func.distinct(GuildBattleRecord.guild_name))
            .join(GuildBattle, GuildBattle.battle_id == GuildBattleRecord.battle_id)
            .where(
                GuildBattle.user_id == user_id,
                GuildBattle.battle_id == battle_id,
                GuildBattle.del_flag == '0',
                GuildBattleRecord.del_flag == '0',
            )
            .order_by(GuildBattleRecord.guild_name)
        )
        result = await db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    @classmethod
    async def get_battle_records_by_guild(cls, db: AsyncSession, battle_id: int, guild_name: str) -> list:
        stmt = (
            select(GuildBattleRecord.player_name, GuildBattleRecord.player_class)
            .where(
                GuildBattleRecord.battle_id == battle_id,
                GuildBattleRecord.guild_name == guild_name,
                GuildBattleRecord.del_flag == '0',
            )
            .order_by(GuildBattleRecord.player_name)
        )
        result = await db.execute(stmt)
        return result.fetchall()

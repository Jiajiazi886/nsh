from sqlalchemy import Select, or_, select, update
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.role_do import SysRole
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_guild.entity.do.join_application_do import GuildJoinApplication


class JoinApplicationDao:
    @classmethod
    def _guild_user_stmt(cls) -> Select:
        return (
            select(SysUser.user_id, SysUser.user_name, SysUser.nick_name)
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

    @classmethod
    async def search_guilds(cls, db: AsyncSession, keyword: str) -> list:
        stmt = cls._guild_user_stmt().where(SysUser.nick_name.like(f'%{keyword}%')).order_by(SysUser.nick_name).limit(20)
        result = await db.execute(stmt)
        return result.all()

    @classmethod
    async def get_guild_by_id(cls, db: AsyncSession, guild_id: int) -> Row | None:
        stmt = cls._guild_user_stmt().where(SysUser.user_id == guild_id)
        result = await db.execute(stmt)
        return result.first()

    @classmethod
    async def create_application(cls, db: AsyncSession, data: dict) -> GuildJoinApplication:
        application = GuildJoinApplication(**data)
        db.add(application)
        await db.flush()
        return application

    @classmethod
    async def list_my_applications(cls, db: AsyncSession, applicant_user_id: int) -> list[GuildJoinApplication]:
        stmt = (
            select(GuildJoinApplication)
            .where(GuildJoinApplication.applicant_user_id == applicant_user_id)
            .order_by(GuildJoinApplication.apply_time.desc(), GuildJoinApplication.application_id.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_latest_effective_application(cls, db: AsyncSession, applicant_user_id: int) -> GuildJoinApplication | None:
        stmt = (
            select(GuildJoinApplication)
            .where(
                GuildJoinApplication.applicant_user_id == applicant_user_id,
                GuildJoinApplication.del_flag == '0',
                GuildJoinApplication.review_status.in_(['0', '1']),
            )
            .order_by(GuildJoinApplication.apply_time.desc(), GuildJoinApplication.application_id.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_application_by_id(cls, db: AsyncSession, application_id: int) -> GuildJoinApplication | None:
        stmt = select(GuildJoinApplication).where(GuildJoinApplication.application_id == application_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_pending_application_by_id(cls, db: AsyncSession, application_id: int) -> GuildJoinApplication | None:
        stmt = select(GuildJoinApplication).where(
            GuildJoinApplication.application_id == application_id,
            GuildJoinApplication.review_status == '0',
            GuildJoinApplication.del_flag == '0',
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list_pending_applications(cls, db: AsyncSession, guild_id: int | None = None) -> list:
        stmt = (
            select(
                GuildJoinApplication,
                SysUser.user_name.label('applicant_user_name'),
                SysUser.nick_name.label('applicant_nick_name'),
            )
            .join(SysUser, SysUser.user_id == GuildJoinApplication.applicant_user_id, isouter=True)
            .where(
                GuildJoinApplication.review_status == '0',
                GuildJoinApplication.del_flag == '0',
                or_(SysUser.del_flag == '0', GuildJoinApplication.applicant_user_id == 0),
            )
            .order_by(GuildJoinApplication.apply_time.asc(), GuildJoinApplication.application_id.asc())
        )
        if guild_id is not None:
            stmt = stmt.where(GuildJoinApplication.guild_id == guild_id)
        result = await db.execute(stmt)
        return result.all()

    @classmethod
    async def update_application(cls, db: AsyncSession, application_id: int, data: dict) -> None:
        stmt = update(GuildJoinApplication).where(GuildJoinApplication.application_id == application_id).values(**data)
        await db.execute(stmt)
        await db.flush()

    @classmethod
    async def archive_effective_applications(cls, db: AsyncSession, applicant_user_id: int) -> None:
        stmt = (
            update(GuildJoinApplication)
            .where(
                GuildJoinApplication.applicant_user_id == applicant_user_id,
                GuildJoinApplication.del_flag == '0',
                GuildJoinApplication.review_status.in_(['0', '1']),
            )
            .values(del_flag='1')
        )
        await db.execute(stmt)
        await db.flush()

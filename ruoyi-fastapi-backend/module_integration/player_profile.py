"""Account-owned game profile; never changes membership or historic activity JSON."""
from datetime import datetime
from pydantic import ConfigDict, Field, StrictBool
from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, select, update
from config.database import Base
from module_admin.entity.do.user_do import SysUser
from module_guild.entity.do.member_do import GuildMember
from module_guild.entity.do.profession_do import GuildProfession
from module_integration.activities.schema import Input
from module_integration.activities.service import ActivityService, uid, fail


class AccountPlayerProfile(Base):
    __tablename__ = 'integration_account_player_profile'
    account_id = Column(BigInteger, primary_key=True, autoincrement=False)
    name = Column(String(30), nullable=False)
    player_uid = Column(String(64), nullable=False, default='')
    wechat_id = Column(String(64), nullable=False, default='')
    has_orange_weapon = Column(Boolean, nullable=False, default=False)
    profession = Column(String(20), nullable=False, default='')
    secondary_profession = Column(String(20), nullable=False, default='')
    remark = Column(String(500), nullable=False, default='')
    updated_at = Column(DateTime, nullable=False, default=datetime.now)


class PlayerProfileInput(Input):
    model_config = ConfigDict(extra='forbid', alias_generator=Input.model_config['alias_generator'],
                              populate_by_name=True, str_strip_whitespace=True, strict=True)
    name: str = Field(min_length=1, max_length=30)
    player_uid: str = Field(default='', max_length=64)
    wechat_id: str = Field(default='', max_length=64)
    has_orange_weapon: StrictBool = False
    profession: str = Field(default='', max_length=20)
    secondary_profession: str = Field(default='', max_length=20)
    remark: str = Field(default='', max_length=500)


class PlayerProfileService:
    @staticmethod
    def dto(profile):
        return dict(name=profile.name, playerUid=profile.player_uid, wechatId=profile.wechat_id,
                    hasOrangeWeapon=bool(profile.has_orange_weapon), profession=profile.profession,
                    secondaryProfession=profile.secondary_profession, remark=profile.remark)

    @classmethod
    async def read_account(cls, db, account_id):
        profile = await ActivityService.scalar(db, select(AccountPlayerProfile).where(AccountPlayerProfile.account_id == account_id))
        if profile:
            return cls.dto(profile)
        member = await ActivityService.scalar(db, select(GuildMember).where(
            GuildMember.member_user_id == account_id, GuildMember.is_active == '1').order_by(GuildMember.member_id.desc()).limit(1))
        return dict(name=(member.player_name or '') if member else '', playerUid='', wechatId='', hasOrangeWeapon=False,
                    profession=(member.player_class or '') if member else '',
                    secondaryProfession=(member.secondary_class or '') if member else '', remark=(member.remark or '') if member else '')

    @classmethod
    async def get(cls, db, actor):
        return await cls.read_account(db, uid(actor))

    @classmethod
    async def save(cls, db, actor, data):
        account_id = uid(actor)
        try:
            # Serialize saves per existing authenticated account, including first insert.
            await db.execute(select(SysUser.user_id).where(SysUser.user_id == account_id).with_for_update())
            enabled = set((await db.execute(select(GuildProfession.profession_name).where(GuildProfession.status == '0'))).scalars().all())
            if any(p and p not in enabled for p in (data.profession, data.secondary_profession)):
                fail(422, 'VALIDATION_FAILED', '职业不存在或已停用，请重新选择')
            profile = await ActivityService.scalar(db, select(AccountPlayerProfile).where(AccountPlayerProfile.account_id == account_id))
            if not profile:
                profile = AccountPlayerProfile(account_id=account_id)
                db.add(profile)
            for key, value in data.model_dump().items():
                setattr(profile, key, value)
            profile.updated_at = datetime.now()
            await db.execute(update(GuildMember).where(GuildMember.member_user_id == account_id, GuildMember.is_active == '1').values(
                player_name=data.name, player_class=data.profession, secondary_class=data.secondary_profession, remark=data.remark))
            result = cls.dto(profile)  # No expired ORM attribute reads after async commit.
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def managed_get(cls, db, actor, org_id, account_id):
        if not account_id.isdecimal() or len(account_id)>19 or not 0<int(account_id)<2**63:
            fail(422, 'VALIDATION_FAILED', '账号 ID 不正确')
        org = await ActivityService.organization(db, actor, org_id)
        if org.org_type != 'guild':
            fail(403, 'FORBIDDEN', '仅本帮会管理员或助手可以查看成员微信号')
        await ActivityService.require_manager(db, actor, org)
        member = await ActivityService.scalar(db, select(GuildMember.member_id).where(
            GuildMember.user_id == org.source_owner_id, GuildMember.member_user_id == int(account_id), GuildMember.is_active == '1').limit(1))
        if member is None:
            fail(404, 'NOT_FOUND', '成员不存在或不属于本帮会')
        return await cls.read_account(db, int(account_id))

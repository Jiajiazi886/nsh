from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String

from config.database import Base


class GuildBattleInvite(Base):
    __tablename__ = 'guild_battle_invite'
    __table_args__ = {'comment': '约战临时邀请链接表'}

    invite_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='邀请ID')
    invite_code = Column(String(64), nullable=False, unique=True, comment='邀请码')
    owner_user_id = Column(BigInteger, nullable=False, server_default='0', comment='帮会大当家用户ID')
    guild_name = Column(String(64), nullable=True, server_default="''", comment='帮会名称快照')
    battle_name = Column(String(100), nullable=False, server_default="''", comment='约战名称')
    battle_time = Column(DateTime, nullable=True, comment='约战时间')
    expire_time = Column(DateTime, nullable=False, comment='链接过期时间')
    status = Column(CHAR(1), nullable=False, server_default='0', comment='状态（0启用 1停用）')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    del_flag = Column(CHAR(1), nullable=False, server_default='0', comment='删除标志（0正常 1删除）')


class GuildBattleRegistration(Base):
    __tablename__ = 'guild_battle_registration'
    __table_args__ = {'comment': '约战报名表'}

    registration_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='报名ID')
    invite_id = Column(BigInteger, nullable=True, comment='邀请ID')
    invite_code = Column(String(64), nullable=True, server_default="''", comment='邀请码快照')
    battle_id = Column(BigInteger, nullable=True, comment='约战ID')
    guild_id = Column(BigInteger, nullable=False, server_default='0', comment='帮会ID')
    owner_user_id = Column(BigInteger, nullable=False, server_default='0', comment='帮会大当家用户ID')
    applicant_user_id = Column(BigInteger, nullable=False, server_default='0', comment='报名账号用户ID，公开报名为0')
    member_id = Column(BigInteger, nullable=True, comment='成员ID')
    team_id = Column(BigInteger, nullable=True, comment='团队ID')
    player_name = Column(String(30), nullable=False, server_default="''", comment='玩家名快照')
    player_class = Column(String(20), nullable=True, server_default="''", comment='主职业')
    secondary_class = Column(String(20), nullable=True, server_default="''", comment='副职')
    role_in_guild = Column(String(20), nullable=True, server_default="''", comment='帮会身份')
    applicant_name = Column(String(50), nullable=True, server_default="''", comment='报名人称呼')
    applicant_contact = Column(String(100), nullable=True, server_default="''", comment='联系方式')
    apply_time = Column(DateTime, nullable=True, default=datetime.now, comment='报名时间')
    approval_status = Column(CHAR(1), nullable=True, server_default='0', comment='审核状态（0待审核 1已通过 2已拒绝）')
    approval_time = Column(DateTime, nullable=True, comment='审核时间')
    approval_by = Column(String(64), nullable=True, comment='审核人')
    approval_comment = Column(String(500), nullable=True, comment='审核备注')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    del_flag = Column(CHAR(1), nullable=False, server_default='0', comment='删除标志（0正常 1删除）')

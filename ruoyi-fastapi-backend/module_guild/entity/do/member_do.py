from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String

from config.database import Base


class GuildMember(Base):
    __tablename__ = 'guild_member'
    __table_args__ = {'comment': '帮会成员表'}

    member_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='成员ID')
    guild_id = Column(BigInteger, nullable=False, server_default='0', comment='所属帮会ID')
    user_id = Column(BigInteger, nullable=False, server_default='0', comment='所属用户ID')
    member_user_id = Column(BigInteger, nullable=False, server_default='0', comment='成员账号用户ID')
    player_name = Column(String(30), nullable=False, server_default="''", comment='玩家角色名')
    player_class = Column(String(20), nullable=True, server_default="''", comment='职业')
    secondary_class = Column(String(20), nullable=True, server_default="''", comment='副职')
    role_in_guild = Column(String(20), nullable=True, server_default='成员', comment='帮会身份')
    join_time = Column(DateTime, nullable=True, comment='加入时间')
    is_active = Column(CHAR(1), nullable=True, server_default='0', comment='活跃状态')
    source_type = Column(String(20), nullable=True, server_default='manual', comment='成员来源')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    team_id = Column(BigInteger, nullable=True, default=None, comment='团队ID')
    squad_number = Column(Integer, nullable=True, default=None, comment='队编号')

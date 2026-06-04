from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String

from config.database import Base


class GuildJoinApplication(Base):
    __tablename__ = 'guild_join_application'
    __table_args__ = {'comment': '帮会入会申请表'}

    application_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='申请ID')
    applicant_user_id = Column(BigInteger, nullable=False, server_default='0', comment='申请用户ID')
    guild_id = Column(BigInteger, nullable=False, server_default='0', comment='目标帮会ID')
    guild_name = Column(String(30), nullable=False, server_default="''", comment='目标帮会名称快照')
    player_name = Column(String(30), nullable=False, server_default="''", comment='玩家角色名')
    player_class = Column(String(20), nullable=True, server_default="''", comment='主职业')
    secondary_class = Column(String(20), nullable=True, server_default="''", comment='副职')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    review_status = Column(CHAR(1), nullable=False, server_default='0', comment='审核状态（0待审核 1已通过 2已拒绝）')
    del_flag = Column(CHAR(1), nullable=False, server_default='0', comment='删除标志（0有效 1归档）')
    apply_time = Column(DateTime, nullable=True, default=datetime.now, comment='申请时间')
    review_time = Column(DateTime, nullable=True, comment='审核时间')
    reviewer_user_id = Column(BigInteger, nullable=True, default=None, comment='审核人用户ID')

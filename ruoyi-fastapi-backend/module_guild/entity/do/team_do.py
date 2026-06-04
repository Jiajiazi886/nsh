from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, String
from config.database import Base

class GuildTeam(Base):
    __tablename__ = 'guild_team'
    __table_args__ = {'comment': '帮会团队表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='主键ID')
    team_name = Column(String(50), nullable=False, comment='团队名称')
    team_type = Column(String(20), nullable=False, comment='团队类型')
    user_id = Column(BigInteger, nullable=False, server_default='0', comment='用户ID')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
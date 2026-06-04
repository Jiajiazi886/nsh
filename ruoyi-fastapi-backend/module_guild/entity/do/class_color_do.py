from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, BigInteger
from config.database import Base

class GuildClassColor(Base):
    __tablename__ = 'guild_class_color'
    __table_args__ = {'comment': '职业颜色配置表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    class_name = Column(String(20), nullable=False, comment='职业名称')
    bg_color = Column(String(7), nullable=False, server_default='#FFFFFF', comment='背景颜色')
    text_color = Column(String(7), nullable=False, server_default='#000000', comment='文字颜色')
    user_id = Column(BigInteger, nullable=False, server_default='0', comment='所属用户ID')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
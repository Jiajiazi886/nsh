from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String

from config.database import Base


class GuildProfession(Base):
    """职业信息表"""

    __tablename__ = 'guild_profession'
    __table_args__ = {'comment': '职业信息表'}

    profession_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='职业ID')
    profession_name = Column(String(30), nullable=False, unique=True, comment='职业名称')
    order_num = Column(Integer, nullable=False, server_default='0', comment='显示顺序')
    status = Column(CHAR(1), nullable=False, server_default='0', comment='状态（0正常 1停用）')
    create_by = Column(String(64), nullable=True, server_default='', comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')
    remark = Column(String(500), nullable=True, comment='备注')

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, String

from config.database import Base


class SystemInternalPowerEntry(Base):
    """
    系统内功词条表
    """

    __tablename__ = 'system_internal_power_entry'
    __table_args__ = {'comment': '系统内功词条表'}

    entry_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='词条ID')
    entry_name = Column(String(64), unique=True, nullable=False, comment='词条名称')
    conversion_percent = Column(Float, nullable=True, comment='数值转换百分比')
    conversion_desc = Column(String(255), nullable=True, server_default="''", comment='转换说明')
    status = Column(String(1), nullable=False, server_default='0', comment='状态（0正常 1停用）')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

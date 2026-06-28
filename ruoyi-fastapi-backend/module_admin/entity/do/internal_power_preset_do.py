from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, String, Text, UniqueConstraint

from config.database import Base


class SystemInternalPowerPreset(Base):
    """
    系统内功预设表
    """

    __tablename__ = 'system_internal_power_preset'
    __table_args__ = (
        UniqueConstraint('name', 'element_key', name='uk_system_internal_power_preset_name_element'),
        {'comment': '系统内功预设表'},
    )

    preset_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='预设ID')
    name = Column(String(64), nullable=False, comment='内功名称')
    element_key = Column(String(16), nullable=False, comment='元素标识')
    elements_json = Column(Text, nullable=False, comment='五行JSON')
    bonus_percent = Column(Float, nullable=False, server_default='0', comment='基础百分比增益')
    bonus_type = Column(String(32), nullable=True, server_default="''", comment='增益类型')
    bonus_desc = Column(String(255), nullable=True, server_default="''", comment='增益描述')
    image_url = Column(String(255), nullable=True, server_default="''", comment='内功图片地址')
    entries_json = Column(Text, nullable=True, comment='词条JSON')
    status = Column(String(1), nullable=False, server_default='0', comment='状态（0正常 1停用）')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

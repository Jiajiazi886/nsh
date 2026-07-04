from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Text

from config.database import Base


class PersonalInternalPowerPanelSetting(Base):
    """
    个人内功PVP收益面板设置表
    """

    __tablename__ = 'personal_internal_power_panel_setting'
    __table_args__ = {'comment': '个人内功PVP收益面板设置表'}

    user_id = Column(BigInteger, primary_key=True, autoincrement=False, nullable=False, comment='用户ID')
    target_panel_json = Column(Text, nullable=False, comment='受击方面板JSON')
    attack_panel_json = Column(Text, nullable=False, comment='攻击方无内功基础面板JSON')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

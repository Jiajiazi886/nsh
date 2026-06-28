from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, String, UniqueConstraint

from config.database import Base


class PersonalInternalPowerEntrySetting(Base):
    """
    个人内功词条换算基准表
    """

    __tablename__ = 'personal_internal_power_entry_setting'
    __table_args__ = {'comment': '个人内功词条换算基准表'}

    user_id = Column(BigInteger, primary_key=True, nullable=False, comment='用户ID')
    base_attack_power = Column(Float, nullable=False, server_default='0', comment='基准进攻能力')
    base_percent = Column(Float, nullable=False, server_default='0', comment='基准百分比')
    unit_percent = Column(Float, nullable=False, server_default='0', comment='1点进攻能力对应百分比')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')


class PersonalInternalPowerEntryValue(Base):
    """
    个人内功词条数值表
    """

    __tablename__ = 'personal_internal_power_entry_value'
    __table_args__ = (
        UniqueConstraint('user_id', 'entry_name', name='uk_personal_internal_power_entry_user_name'),
        {'comment': '个人内功词条数值表'},
    )

    value_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='数值ID')
    user_id = Column(BigInteger, nullable=False, index=True, comment='用户ID')
    entry_name = Column(String(64), nullable=False, comment='词条名称')
    entry_value = Column(Float, nullable=False, server_default='0', comment='用户内功数值')
    attack_power = Column(Float, nullable=False, server_default='0', comment='进攻能力')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

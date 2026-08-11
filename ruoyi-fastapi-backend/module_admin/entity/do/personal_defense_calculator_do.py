from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT

from config.database import Base


class PersonalPvpAttackPanel(Base):
    """当前用户私有的防守计算器进攻方面板模板。"""

    __tablename__ = 'personal_pvp_attack_panel'
    __table_args__ = (
        UniqueConstraint('user_id', 'sequence_no', name='uq_personal_pvp_attack_panel_user_sequence'),
        {'comment': '个人PVP进攻方面板模板表'},
    )

    panel_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='面板主键')
    user_id = Column(BigInteger, nullable=False, index=True, comment='所属用户ID')
    sequence_no = Column(Integer, nullable=False, comment='用户内模板序号')
    panel_name = Column(String(100), nullable=False, comment='系统生成的面板名称')
    panel_json = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=False, comment='进攻方面板JSON')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')


class PersonalDefenseCalculatorSetting(Base):
    """当前用户防守计算器的防守面板及选中攻击面板。"""

    __tablename__ = 'personal_defense_calculator_setting'
    __table_args__ = {'comment': '个人防守计算器设置表'}

    user_id = Column(BigInteger, primary_key=True, autoincrement=False, nullable=False, comment='用户ID')
    defender_json = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=False, comment='防守方面板JSON')
    selected_panel_source = Column(String(16), nullable=False, default='system', comment='面板来源 system 或 personal')
    selected_panel_id = Column(BigInteger, nullable=False, default=0, comment='选中面板ID')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

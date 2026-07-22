from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, String, Text

from config.database import Base


class SystemPvpAttackPanel(Base):
    """管理员维护的 PVP 进攻方面板。"""

    __tablename__ = 'system_pvp_attack_panel'
    __table_args__ = {'comment': '系统PVP进攻方面板表'}

    panel_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='面板主键')
    panel_name = Column(String(100), nullable=False, comment='面板名称')
    panel_json = Column(Text, nullable=False, comment='进攻方面板JSON')
    status = Column(String(1), nullable=False, default='0', comment='状态（0启用 1停用）')
    remark = Column(String(500), nullable=True, default='', comment='备注')
    create_by = Column(String(64), nullable=True, default='', comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

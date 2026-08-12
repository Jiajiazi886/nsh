from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, String

from config.database import Base


class SystemPvpDefenseProfessionBonus(Base):
    """管理员维护的 PVP 防守职业默认加成。"""

    __tablename__ = 'system_pvp_defense_profession_bonus'
    __table_args__ = {'comment': 'PVP防守职业默认加成表'}

    profession_id = Column(BigInteger, primary_key=True, autoincrement=False, comment='职业ID')
    defense_bonus_pct = Column(Float, nullable=False, default=0, comment='内功防御增量加成百分比')
    hp_bonus_pct = Column(Float, nullable=False, default=0, comment='内功气血增量加成百分比')
    update_by = Column(String(64), nullable=True, default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

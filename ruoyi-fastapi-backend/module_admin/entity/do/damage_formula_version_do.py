from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT

from config.database import Base


class SystemDamageFormulaVersion(Base):
    """
    系统伤害公式版本表
    """

    __tablename__ = 'system_damage_formula_version'
    __table_args__ = {'comment': '系统伤害公式版本表'}

    version_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='公式版本ID')
    version_name = Column(String(100), nullable=False, comment='版本名称')
    formula_scope = Column(String(64), nullable=False, comment='公式作用域')
    status = Column(String(16), nullable=False, server_default='draft', comment='状态（draft草稿 published已发布 archived历史）')
    formula_package_json = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=False, comment='公式包JSON')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    publish_time = Column(DateTime, nullable=True, comment='发布时间')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT

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


class PersonalInternalPowerPanelRecognitionHistory(Base):
    """
    个人玩家面板AI识别历史表
    """

    __tablename__ = 'personal_internal_power_panel_recognition_history'
    __table_args__ = {'comment': '个人玩家面板AI识别历史表'}

    record_id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False, comment='记录ID')
    user_id = Column(BigInteger, nullable=False, index=True, comment='用户ID')
    file_name = Column(String(255), nullable=True, default='', comment='图片文件名')
    mime_type = Column(String(64), nullable=True, default='image/png', comment='图片MIME类型')
    image_base64 = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=True, comment='图片Base64')
    status = Column(String(20), nullable=False, default='recognizing', comment='识别状态')
    parsed_json = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=True, comment='识别JSON')
    raw_text = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=True, comment='模型原始文本')
    error = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=True, comment='错误信息')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')


class SystemInternalPowerPanelTemplate(Base):
    """
    系统内功PVP收益面板模板表
    """

    __tablename__ = 'system_internal_power_panel_template'
    __table_args__ = {'comment': '系统内功PVP收益面板模板表'}

    template_id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False, comment='模板ID')
    template_name = Column(String(100), nullable=False, comment='模板名称')
    status = Column(String(1), nullable=False, default='0', comment='启用状态（0启用 1停用）')
    target_panel_json = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=False, comment='受击方面板JSON')
    attack_panel_json = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=False, comment='攻击方面板JSON')
    remark = Column(String(500), nullable=True, default='', comment='备注')
    create_by = Column(String(64), nullable=True, default='', comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

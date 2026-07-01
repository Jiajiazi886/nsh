from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT

from config.database import Base


LongText = Text().with_variant(LONGTEXT, 'mysql')


class PersonalInternalPower(Base):
    """
    个人内功表
    """

    __tablename__ = 'personal_internal_power'
    __table_args__ = {'comment': '个人内功表'}

    power_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='内功ID')
    user_id = Column(BigInteger, nullable=False, index=True, comment='用户ID')
    name = Column(String(64), nullable=False, comment='内功名称')
    category = Column(String(64), nullable=True, server_default="''", comment='内功种类')
    category_trait = Column(String(128), nullable=True, server_default="''", comment='种类特性')
    bonus_percent = Column(Float, nullable=False, server_default='0', comment='基础百分比增伤')
    lingyun_enabled = Column(String(1), nullable=False, server_default='0', comment='是否启用灵韵（0否 1是）')
    lingyun_bonus_percent = Column(Float, nullable=False, server_default='0', comment='灵韵百分比提升')
    entries_json = Column(Text, nullable=True, comment='词条JSON')
    elements_json = Column(Text, nullable=True, comment='五行JSON')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')


class PersonalInternalPowerRecognitionHistory(Base):
    """
    个人内功图片识别历史表
    """

    __tablename__ = 'personal_internal_power_recognition_history'
    __table_args__ = {'comment': '个人内功图片识别历史表'}

    record_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='识别记录ID')
    user_id = Column(BigInteger, nullable=False, index=True, comment='用户ID')
    file_name = Column(String(255), nullable=False, server_default="''", comment='文件名')
    image_base64 = Column(LongText, nullable=True, comment='图片Base64')
    mime_type = Column(String(64), nullable=False, server_default='image/png', comment='图片MIME类型')
    status = Column(String(20), nullable=False, server_default='recognizing', comment='状态')
    parsed_json = Column(LongText, nullable=True, comment='解析JSON')
    raw_text = Column(LongText, nullable=True, comment='模型原始返回')
    error = Column(LongText, nullable=True, comment='完整错误')
    preset_candidates_json = Column(LongText, nullable=True, comment='候选预设JSON')
    saved_power_id = Column(BigInteger, nullable=True, comment='已保存内功ID')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

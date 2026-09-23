from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, String

from config.database import Base


class AiUsagePolicy(Base):
    """AI 识图额度的全局单行策略。"""

    __tablename__ = 'ai_usage_policy'
    __table_args__ = {'comment': 'AI识图额度策略表'}

    policy_id = Column(Integer, primary_key=True, nullable=False, comment='固定策略ID')
    default_recognition_count = Column(Integer, nullable=False, server_default='0', comment='新用户默认识图次数')
    vip_grant_count = Column(Integer, nullable=False, server_default='0', comment='VIP开通赠送识图次数')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新人')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')


class AiRequestUsageLog(Base):
    """真实大模型生成请求的 Token 使用记录；不保存请求和回答内容。"""

    __tablename__ = 'ai_request_usage_log'
    __table_args__ = (
        Index('idx_ai_usage_user_time', 'user_id', 'request_time'),
        Index('idx_ai_usage_connection_time', 'connection_id', 'request_time'),
        Index('idx_ai_usage_status_time', 'status', 'request_time'),
        Index('idx_ai_usage_model_time', 'model', 'request_time'),
        {'comment': '大模型请求Token使用记录'},
    )

    record_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='记录ID')
    request_id = Column(String(36), nullable=False, unique=True, comment='唯一请求ID')
    user_id = Column(BigInteger, nullable=False, comment='请求用户ID')
    user_name = Column(String(30), nullable=False, server_default="''", comment='账号快照')
    nick_name = Column(String(30), nullable=False, server_default="''", comment='昵称快照')
    connection_id = Column(BigInteger, nullable=True, comment='AI连接ID')
    connection_name = Column(String(100), nullable=False, server_default="''", comment='连接名称快照')
    provider = Column(String(50), nullable=False, server_default="''", comment='供应商')
    protocol = Column(String(32), nullable=False, comment='接口协议')
    model = Column(String(100), nullable=False, comment='模型')
    scene = Column(String(64), nullable=False, comment='业务场景')
    status = Column(String(16), nullable=False, server_default='pending', comment='pending/success/failed')
    input_tokens = Column(BigInteger, nullable=True, comment='输入Token')
    output_tokens = Column(BigInteger, nullable=True, comment='输出Token')
    total_tokens = Column(BigInteger, nullable=True, comment='总Token')
    usage_reported = Column(String(1), nullable=False, server_default='0', comment='供应商是否上报Usage')
    request_time = Column(DateTime, nullable=False, default=datetime.now, comment='请求时间')
    complete_time = Column(DateTime, nullable=True, comment='完成时间')
    duration_ms = Column(BigInteger, nullable=True, comment='耗时毫秒')
    error_message = Column(String(500), nullable=True, server_default="''", comment='脱敏错误摘要')

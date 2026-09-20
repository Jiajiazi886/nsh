from datetime import datetime

from sqlalchemy import CHAR, Column, DateTime, Integer, LargeBinary, String
from sqlalchemy.dialects import mysql
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine

from config.database import Base
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil

LOW_SURROGATE_BYTE_START = 0xDC00
LOW_SURROGATE_BYTE_END = 0xDCFF


def decode_notice_content(value: str | bytes | None) -> str | None:
    """Decode legacy notice blobs without leaking bytes into JSON responses.

    Older database exports can contain UTF-8 text that was first decoded with
    ``surrogateescape`` and then persisted with ``surrogatepass``.  Those rows
    contain byte sequences such as ``ED B3 A6`` and cannot be decoded as normal
    UTF-8.  Restore the escaped source bytes first, then decode the original
    UTF-8 text.  Truly damaged input remains visible with replacement markers
    instead of crashing every notice-list response.
    """
    if value is None or isinstance(value, str):
        return value
    try:
        return value.decode('utf-8')
    except UnicodeDecodeError:
        try:
            surrogate_text = value.decode('utf-8', errors='surrogatepass')
            restored = bytearray()
            for char in surrogate_text:
                codepoint = ord(char)
                if LOW_SURROGATE_BYTE_START <= codepoint <= LOW_SURROGATE_BYTE_END:
                    restored.append(codepoint - LOW_SURROGATE_BYTE_START)
                else:
                    restored.extend(char.encode('utf-8'))
            restored_bytes = bytes(restored)
            return restored_bytes.decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            return value.decode('utf-8', errors='replace')


class NoticeContentType(TypeDecorator):
    """Text semantics backed by the legacy BLOB/bytea schema."""

    impl = LargeBinary
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
        if dialect.name == 'mysql':
            return dialect.type_descriptor(mysql.LONGBLOB())
        return dialect.type_descriptor(LargeBinary())

    def process_bind_param(self, value: str | bytes | None, dialect: Dialect) -> bytes | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        return value.encode('utf-8')

    def process_result_value(self, value: str | bytes | None, dialect: Dialect) -> str | None:
        return decode_notice_content(value)


class SysNotice(Base):
    """
    通知公告表
    """

    __tablename__ = 'sys_notice'
    __table_args__ = {'comment': '通知公告表'}

    notice_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='公告ID')
    notice_title = Column(String(50), nullable=False, comment='公告标题')
    notice_type = Column(CHAR(1), nullable=False, comment='公告类型（1通知 2公告）')
    notice_content = Column(
        NoticeContentType(),
        nullable=True,
        server_default=SqlalchemyUtil.get_server_default_null(DataBaseConfig.db_type, False),
        comment='公告内容',
    )
    status = Column(CHAR(1), nullable=True, server_default='0', comment='公告状态（0正常 1关闭）')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, comment='更新时间', default=datetime.now())
    remark = Column(
        String(255),
        nullable=True,
        server_default=SqlalchemyUtil.get_server_default_null(DataBaseConfig.db_type),
        comment='备注',
    )

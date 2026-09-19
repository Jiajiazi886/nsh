"""Persistent rotating refresh-token storage.

Only SHA-256 digests are stored in the database. Redis remains a cache and
backward-compatibility store for tokens issued before this table existed.
"""

from datetime import datetime, timedelta
import secrets
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import Base


class SystemAuthRefreshToken(Base):
    __tablename__ = "system_auth_refresh_token"
    __table_args__ = (
        Index("ix_system_auth_refresh_token_user", "user_id"),
        Index("ix_system_auth_refresh_token_family", "token_family_id"),
        Index("ix_system_auth_refresh_token_device", "device_id"),
    )

    token_id = Column(String(64), primary_key=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    user_id = Column(BigInteger, ForeignKey('sys_user.user_id'), nullable=False)
    client_type = Column(String(40), nullable=False, default="")
    token_family_id = Column(String(64), nullable=False)
    device_id = Column(String(128), nullable=True)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by_token_id = Column(String(64), nullable=True)


def refresh_token_hash(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()


def new_refresh_token() -> str:
    return "rt_" + secrets.token_urlsafe(48)


def refresh_token_is_usable(row: SystemAuthRefreshToken, now: datetime) -> bool:
    return row.revoked_at is None and row.last_used_at is None and row.expires_at > now


async def issue_refresh_token(
    db: AsyncSession, raw_token: str, *, user_id: int, client_type: str, session_id: str,
    family_id: str | None = None, device_id: str | None = None, now: datetime | None = None,
    expires_days: int = 30,
) -> SystemAuthRefreshToken | None:
    # Contract-test fake sessions intentionally do not persist ORM entities.
    if not isinstance(db, AsyncSession):
        return None
    now = now or datetime.now()
    row = SystemAuthRefreshToken(
        token_id=f"rtid_{uuid4().hex}", token_hash=refresh_token_hash(raw_token), user_id=user_id,
        client_type=client_type[:40], token_family_id=family_id or f"family_{uuid4().hex}",
        device_id=(device_id or session_id)[:128], issued_at=now,
        expires_at=now + timedelta(days=expires_days),
    )
    db.add(row)
    await db.flush()
    return row


async def find_refresh_token(
    db: AsyncSession, raw_token: str
) -> SystemAuthRefreshToken | None:
    if not isinstance(db, AsyncSession):
        return None
    return await db.scalar(
        select(SystemAuthRefreshToken)
        .where(SystemAuthRefreshToken.token_hash == refresh_token_hash(raw_token))
        .with_for_update()
    )


async def rotate_loaded_refresh_token(
    db: AsyncSession, old: SystemAuthRefreshToken, replacement_raw_token: str, *,
    client_type: str, session_id: str, now: datetime | None = None, expires_days: int = 30,
) -> SystemAuthRefreshToken | None:
    if not isinstance(db, AsyncSession):
        return None
    now = now or datetime.now()
    if not refresh_token_is_usable(old, now):
        return None
    next_row = SystemAuthRefreshToken(
        token_id=f"rtid_{uuid4().hex}", token_hash=refresh_token_hash(replacement_raw_token),
        user_id=old.user_id, client_type=client_type[:40], token_family_id=old.token_family_id,
        device_id=session_id[:128], issued_at=now,
        expires_at=now + timedelta(days=expires_days),
    )
    old.last_used_at, old.revoked_at, old.replaced_by_token_id = now, now, next_row.token_id
    db.add(next_row)
    await db.flush()
    return next_row


async def revoke_refresh_tokens(
    db: AsyncSession, *, user_id: int, session_id: str | None = None, now: datetime | None = None
) -> None:
    if not isinstance(db, AsyncSession):
        return
    now = now or datetime.now()
    query = select(SystemAuthRefreshToken).where(
        SystemAuthRefreshToken.user_id == user_id, SystemAuthRefreshToken.revoked_at.is_(None)
    )
    if session_id:
        query = query.where(SystemAuthRefreshToken.device_id == session_id[:128])
    for row in (await db.scalars(query.with_for_update())).all():
        row.revoked_at = now

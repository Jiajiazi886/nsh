from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, JSON, String, UniqueConstraint, Index
from config.database import Base


class Organization(Base):
    __tablename__ = 'integration_organization'
    org_id = Column(String(64), primary_key=True)
    org_type = Column(String(10), nullable=False)
    name = Column(String(80), nullable=False)
    owner_user_id = Column(BigInteger, nullable=False, index=True)
    source_owner_id = Column(BigInteger, nullable=True)
    __table_args__ = (UniqueConstraint('org_type', 'source_owner_id'),)


class OrganizationMember(Base):
    __tablename__ = 'integration_organization_member'
    org_id = Column(String(64), primary_key=True)
    account_id = Column(BigInteger, primary_key=True)
    role = Column(String(12), nullable=False, default='member')


class Activity(Base):
    __tablename__ = 'integration_activity'
    activity_id = Column(String(64), primary_key=True)
    org_id = Column(String(64), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    remark = Column(String(500), nullable=False, default='')
    state = Column(String(12), nullable=False, default='open')
    is_public = Column(Integer, nullable=False, default=0)
    revision = Column(Integer, nullable=False, default=0)
    latest_snapshot_id = Column(String(64), nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = (Index('ix_integration_activity_public_state', 'is_public', 'state'),)


class ActivitySnapshot(Base):
    __tablename__ = 'integration_activity_snapshot'
    snapshot_id = Column(String(64), primary_key=True)
    activity_id = Column(String(64), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    teams = Column(JSON, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = (UniqueConstraint('activity_id', 'version'),)


class Participation(Base):
    __tablename__ = 'integration_activity_participation'
    participation_id = Column(String(64), primary_key=True)
    activity_id = Column(String(64), nullable=False, index=True)
    account_id = Column(BigInteger, nullable=False, index=True)
    member_id = Column(BigInteger, nullable=False)
    squad_id = Column(String(100), nullable=True)
    position = Column(Integer, nullable=True)
    state = Column(String(10), nullable=False)
    player = Column(JSON, nullable=False)
    __table_args__ = (
        UniqueConstraint('activity_id', 'member_id'),
        UniqueConstraint('activity_id', 'squad_id', 'position'),
    )


class MutationReceipt(Base):
    __tablename__ = 'integration_activity_receipt'
    receipt_id = Column(String(64), primary_key=True)
    activity_id = Column(String(64), nullable=False)
    actor_id = Column(BigInteger, nullable=False)
    operation_key = Column(String(100), nullable=False)
    action = Column(String(20), nullable=False)
    digest = Column(String(64), nullable=False)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = (UniqueConstraint('activity_id', 'actor_id', 'operation_key'),)


class ReportLink(Base):
    __tablename__ = 'integration_activity_report'
    battle_id = Column(BigInteger, primary_key=True)
    activity_id = Column(String(64), nullable=False, index=True)
    linked_by = Column(BigInteger, nullable=False)
    linked_at = Column(DateTime, nullable=False, default=datetime.now)


class ActivityLeaveLink(Base):
    __tablename__ = 'integration_activity_leave_link'
    activity_id = Column(String(64), primary_key=True)
    org_id = Column(String(64), nullable=False, index=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class ActivityLeaveRecord(Base):
    __tablename__ = 'integration_activity_leave_record'
    record_id = Column(String(64), primary_key=True)
    activity_id = Column(String(64), nullable=False, index=True)
    member_id = Column(BigInteger, nullable=False)
    account_id = Column(BigInteger, nullable=True)
    player = Column(JSON, nullable=False)
    remark = Column(String(500), nullable=False, default='')
    left_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = (UniqueConstraint('activity_id', 'member_id'),)

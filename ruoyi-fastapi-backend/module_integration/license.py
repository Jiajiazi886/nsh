"""Account entitlement domain for desktop clients.

The UI may keep the legacy label "卡密管理", but the domain object is an
account entitlement. No license string or machine fingerprint is stored.
"""

from datetime import datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from common.constant import CommonConstant
from config.database import Base
from exceptions.exception import PermissionException
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.user_service import UserService
from module_integration.contract import ApiProblem


PLAN_DAYS = {'daily': 1, 'weekly': 7, 'monthly': 30}
PlanType = Literal['daily', 'weekly', 'monthly', 'permanent']


class SystemAccountLicense(Base):
    __tablename__ = 'system_account_license'
    __table_args__ = (UniqueConstraint('user_id', name='uk_system_account_license_user'),)

    license_id = Column(String(64), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('sys_user.user_id'), nullable=False, index=True)
    plan_type = Column(String(16), nullable=False)
    status = Column(String(16), nullable=False, default='active')
    valid_from = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    remark = Column(String(500), nullable=False, default='')
    version = Column(Integer, nullable=False, default=1)
    create_by = Column(String(64), nullable=False, default='system')
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_by = Column(String(64), nullable=False, default='system')
    update_time = Column(DateTime, nullable=False, default=datetime.now)


class SystemAccountLicenseAudit(Base):
    __tablename__ = 'system_account_license_audit'
    __table_args__ = (UniqueConstraint('request_id', 'user_id', name='uk_system_account_license_audit_request_user'),)

    audit_id = Column(String(64), primary_key=True)
    batch_id = Column(String(64), nullable=False, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('sys_user.user_id'), nullable=False, index=True)
    operator_user_id = Column(BigInteger, ForeignKey('sys_user.user_id'), nullable=False)
    action = Column(String(32), nullable=False)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    remark = Column(String(500), nullable=False, default='')
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class LicenseGrantInput(BaseModel):
    model_config = ConfigDict(extra='forbid', alias_generator=to_camel, populate_by_name=True)

    request_id: str = Field(min_length=8, max_length=64)
    user_ids: list[str] = Field(min_length=1, max_length=200)
    plan_type: PlanType
    remark: str = Field(default='', max_length=500)

    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values):
            raise ValueError('userIds must not contain duplicates')
        if any(not value.isdecimal() or not 0 < int(value) < 2**63 for value in values):
            raise ValueError('userIds must be positive decimal strings')
        return values


class LicenseRevokeInput(BaseModel):
    model_config = ConfigDict(extra='forbid', alias_generator=to_camel, populate_by_name=True)

    request_id: str = Field(min_length=8, max_length=64)
    user_ids: list[str] = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values):
            raise ValueError('userIds must not contain duplicates')
        if any(not value.isdecimal() or not 0 < int(value) < 2**63 for value in values):
            raise ValueError('userIds must be positive decimal strings')
        return values


class LicenseRemarkInput(BaseModel):
    model_config = ConfigDict(extra='forbid', alias_generator=to_camel, populate_by_name=True)

    remark: str = Field(default='', max_length=500)


def calculate_grant(
    now: datetime,
    existing_expires_at: datetime | None,
    existing_plan_type: str | None,
    plan_type: PlanType,
    existing_status: str | None = 'active',
) -> tuple[datetime, datetime | None]:
    """Calculate an entitlement extension without reading client time."""
    if existing_status == 'active' and existing_plan_type == 'permanent' and existing_expires_at is None:
        raise ApiProblem(409, 'PERMANENT_LICENSE_REQUIRES_REVOKE', '永久授权必须先撤销后才能改为临时授权')
    valid_from = now
    if existing_expires_at is not None and existing_expires_at > now:
        valid_from = existing_expires_at
    if plan_type == 'permanent':
        return now, None
    return valid_from, valid_from + timedelta(days=PLAN_DAYS[plan_type])


def license_state(row: SystemAccountLicense | None, now: datetime) -> dict[str, Any]:
    if row is None:
        return {'authorized': False, 'status': 'none', 'planType': None, 'validFrom': None, 'expiresAt': None}
    authorized = row.status == 'active' and (row.expires_at is None or row.expires_at > now)
    state = 'active' if authorized else ('revoked' if row.status == 'revoked' else 'expired')
    remaining_seconds = None
    if authorized and row.expires_at is not None:
        remaining_seconds = max(0, int((row.expires_at - now).total_seconds()))
    return {
        'authorized': authorized,
        'status': state,
        'planType': row.plan_type,
        'validFrom': row.valid_from.isoformat() if row.valid_from else None,
        'expiresAt': row.expires_at.isoformat() if row.expires_at else None,
        'remainingSeconds': remaining_seconds,
    }


class LicenseService:
    @staticmethod
    def _has_canonical_super_admin_role(actor: CurrentUserModel) -> bool:
        """Return true only for the database's canonical super-admin role.

        The legacy ``UserService.is_admin_role`` helper intentionally keeps
        compatibility for unrelated modules.  License management is a
        privileged boundary, so it must require the role row itself to carry
        both the immutable id and the new permission character.
        """
        user = getattr(actor, 'user', None)
        roles = getattr(user, 'role', None) or []
        for role in roles:
            role_id = role.get('role_id') if isinstance(role, dict) else getattr(role, 'role_id', None)
            role_key = role.get('role_key') if isinstance(role, dict) else getattr(role, 'role_key', None)
            if role_id == CommonConstant.SUPER_ADMIN_ROLE_ID and role_key == CommonConstant.SUPER_ADMIN_ROLE_KEY:
                return True
        # Some lightweight authentication contexts expose only roleIds and
        # the role-key list. Keep the same pair requirement for those callers.
        if not roles:
            role_ids = {str(value).strip() for value in str(getattr(user, 'role_ids', '') or '').split(',') if str(value).strip()}
            role_keys = {str(value).strip() for value in (getattr(actor, 'roles', None) or [])}
            return str(CommonConstant.SUPER_ADMIN_ROLE_ID) in role_ids and CommonConstant.SUPER_ADMIN_ROLE_KEY in role_keys
        return False

    @staticmethod
    def require_super_admin(actor: CurrentUserModel, permission: str | None = None) -> None:
        if not LicenseService._has_canonical_super_admin_role(actor):
            raise PermissionException(data={'errorKey': 'SUPER_ADMIN_REQUIRED'}, message='只有超级管理员可以管理账号授权')
        if permission and '*:*:*' not in (actor.permissions or []) and permission not in (actor.permissions or []):
            raise PermissionException(data={'errorKey': 'LICENSE_PERMISSION_REQUIRED'}, message='当前账号没有该授权管理权限')

    @staticmethod
    async def _member_user_ids(db: AsyncSession, user_ids: list[int]) -> set[int]:
        rows = await db.execute(
            select(SysUserRole.user_id).where(
                SysUserRole.user_id.in_(user_ids), SysUserRole.role_id == CommonConstant.MEMBER_ROLE_ID
            )
        )
        return set(rows.scalars().all())

    @staticmethod
    async def _request_result(
        db: AsyncSession, request_id: str, accepted_actions: set[str]
    ) -> list[dict[str, Any]] | None:
        rows = (
            await db.scalars(
                select(SystemAccountLicenseAudit)
                .where(SystemAccountLicenseAudit.request_id == request_id)
                .order_by(SystemAccountLicenseAudit.created_at, SystemAccountLicenseAudit.audit_id)
            )
        ).all()
        if not rows:
            return None
        if any(row.action not in accepted_actions for row in rows):
            raise ApiProblem(409, 'REQUEST_ID_REUSED', 'requestId 已被其他授权操作使用')
        return [row.new_state | {'userId': str(row.user_id)} for row in rows if row.new_state]

    @classmethod
    async def me(cls, db: AsyncSession, actor: CurrentUserModel, now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now()
        user_id = int(actor.user.user_id)
        user = await db.scalar(select(SysUser).where(SysUser.user_id == user_id))
        member = user is not None and user.status == '0' and user.del_flag == '0' and user_id in await cls._member_user_ids(db, [user_id])
        row = await db.scalar(select(SystemAccountLicense).where(SystemAccountLicense.user_id == user_id))
        result = license_state(row, now)
        result.update({'userId': str(user_id), 'userName': user.user_name if user else None, 'eligibleRole': member, 'serverTime': now.isoformat()})
        if not member:
            if user is None or user.del_flag != '0':
                result['reason'] = 'ACCOUNT_DELETED'
            elif user.status != '0':
                result['reason'] = 'ACCOUNT_DISABLED'
            else:
                result['reason'] = 'MEMBER_ROLE_REQUIRED'
        elif not result['authorized']:
            result['reason'] = 'LICENSE_REVOKED' if result['status'] == 'revoked' else ('LICENSE_EXPIRED' if result['status'] == 'expired' else 'LICENSE_NOT_GRANTED')
        else:
            result['reason'] = None
        return result

    @classmethod
    async def grant(cls, db: AsyncSession, actor: CurrentUserModel, data: LicenseGrantInput) -> list[dict[str, Any]]:
        cls.require_super_admin(actor, 'system:license:grant')
        try:
            ids = [int(value) for value in data.user_ids]
            existing_result = await cls._request_result(db, data.request_id, {'grant', 'extend'})
            if existing_result is not None:
                return existing_result
            eligible = await cls._member_user_ids(db, ids)
            users = {row.user_id: row for row in (await db.scalars(select(SysUser).where(SysUser.user_id.in_(ids)).with_for_update())).all()}
            if len(eligible) != len(ids) or any(user_id not in users or users[user_id].status != '0' or users[user_id].del_flag != '0' for user_id in ids):
                raise ApiProblem(422, 'LICENSE_ACCOUNT_INELIGIBLE', '只能给正常的帮会成员账号授权')
            now = datetime.now()
            batch_id = f'batch_{uuid4().hex}'
            result = []
            for user_id in ids:
                row = await db.scalar(select(SystemAccountLicense).where(SystemAccountLicense.user_id == user_id).with_for_update())
                previous = license_state(row, now)
                valid_from, expires_at = calculate_grant(now, row.expires_at if row else None, row.plan_type if row else None, data.plan_type, row.status if row else None)
                if row is None:
                    row = SystemAccountLicense(license_id=f'lic_{uuid4().hex}', user_id=user_id, plan_type=data.plan_type, status='active', valid_from=valid_from, expires_at=expires_at, remark=data.remark, create_by=actor.user.user_name, update_by=actor.user.user_name)
                    db.add(row)
                else:
                    row.plan_type, row.status, row.valid_from, row.expires_at, row.remark, row.version, row.update_by, row.update_time = data.plan_type, 'active', valid_from, expires_at, data.remark, row.version + 1, actor.user.user_name, now
                state = license_state(row, now)
                action = 'extend' if previous['authorized'] else 'grant'
                db.add(SystemAccountLicenseAudit(audit_id=f'audit_{uuid4().hex}', batch_id=batch_id, request_id=data.request_id, user_id=user_id, operator_user_id=int(actor.user.user_id), action=action, previous_state=previous, new_state=state, remark=data.remark))
                result.append(state | {'userId': str(user_id)})
            await db.commit()
            return result
        except IntegrityError:
            await db.rollback()
            existing_result = await cls._request_result(db, data.request_id, {'grant', 'extend'})
            if existing_result is not None:
                return existing_result
            raise
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def revoke(cls, db: AsyncSession, actor: CurrentUserModel, data: LicenseRevokeInput) -> list[dict[str, Any]]:
        cls.require_super_admin(actor, 'system:license:revoke')
        try:
            existing_result = await cls._request_result(db, data.request_id, {'revoke'})
            if existing_result is not None:
                return existing_result
            now = datetime.now()
            batch_id = f'batch_{uuid4().hex}'
            result = []
            for raw_id in data.user_ids:
                user_id = int(raw_id)
                row = await db.scalar(select(SystemAccountLicense).where(SystemAccountLicense.user_id == user_id).with_for_update())
                if row is None:
                    raise ApiProblem(404, 'LICENSE_NOT_FOUND', f'账号 {raw_id} 没有授权记录')
                previous = license_state(row, now)
                row.status, row.version, row.update_by, row.update_time = 'revoked', row.version + 1, actor.user.user_name, now
                state = license_state(row, now)
                db.add(SystemAccountLicenseAudit(audit_id=f'audit_{uuid4().hex}', batch_id=batch_id, request_id=data.request_id, user_id=user_id, operator_user_id=int(actor.user.user_id), action='revoke', previous_state=previous, new_state=state, remark=data.reason))
                result.append(state | {'userId': raw_id})
            await db.commit()
            return result
        except IntegrityError:
            await db.rollback()
            existing_result = await cls._request_result(db, data.request_id, {'revoke'})
            if existing_result is not None:
                return existing_result
            raise
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def accounts(cls, db: AsyncSession, actor: CurrentUserModel, page: int = 1, page_size: int = 20, keyword: str | None = None, account_status: str | None = None, authorization_status: str | None = None, plan_type: str | None = None) -> dict[str, Any]:
        cls.require_super_admin(actor, 'system:license:list')
        member_ids = select(SysUserRole.user_id).where(SysUserRole.role_id == CommonConstant.MEMBER_ROLE_ID)
        query = select(SysUser, SystemAccountLicense).join(
            SystemAccountLicense, SystemAccountLicense.user_id == SysUser.user_id, isouter=True
        ).where(SysUser.user_id.in_(member_ids), SysUser.del_flag == '0')
        if keyword:
            query = query.where((SysUser.user_name.like(f'%{keyword}%')) | (SysUser.nick_name.like(f'%{keyword}%')))
        if account_status == 'normal':
            query = query.where(SysUser.status == '0')
        elif account_status == 'disabled':
            query = query.where(SysUser.status != '0')
        if plan_type:
            query = query.where(SystemAccountLicense.plan_type == plan_type)
        now = datetime.now()
        if authorization_status == 'none':
            query = query.where(SystemAccountLicense.license_id.is_(None))
        elif authorization_status == 'active':
            query = query.where(SystemAccountLicense.status == 'active', or_(SystemAccountLicense.expires_at.is_(None), SystemAccountLicense.expires_at > now))
        elif authorization_status == 'revoked':
            query = query.where(SystemAccountLicense.status == 'revoked')
        elif authorization_status == 'expired':
            query = query.where(SystemAccountLicense.status != 'revoked', SystemAccountLicense.expires_at.is_not(None), SystemAccountLicense.expires_at <= now)
        total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = (await db.execute(query.order_by(SysUser.user_id).offset((page - 1) * page_size).limit(page_size))).all()
        payload = {
            'pageNum': page,
            'pageSize': page_size,
            'total': total,
            'rows': [
                {
                    'userId': str(user.user_id),
                    'userName': user.user_name,
                    'nickName': user.nick_name,
                    'accountStatus': 'normal' if user.status == '0' else 'disabled',
                    'eligibleRole': True,
                    **license_state(license_row, now),
                    'remark': license_row.remark if license_row else '',
                    'lastOperator': license_row.update_by if license_row else '',
                    'lastOperationTime': license_row.update_time.isoformat() if license_row and license_row.update_time else None,
                }
                for user, license_row in rows
            ],
        }
        return payload

    @classmethod
    async def update_remark(cls, db: AsyncSession, actor: CurrentUserModel, user_id: int, data: LicenseRemarkInput) -> dict[str, Any]:
        cls.require_super_admin(actor, 'system:license:remark')
        try:
            row = await db.scalar(select(SystemAccountLicense).where(SystemAccountLicense.user_id == user_id).with_for_update())
            if row is None:
                raise ApiProblem(404, 'LICENSE_NOT_FOUND', '账号没有授权记录')
            now = datetime.now()
            previous = license_state(row, now) | {'remark': row.remark}
            row.remark, row.version, row.update_by, row.update_time = data.remark, row.version + 1, actor.user.user_name, now
            current = license_state(row, now) | {'remark': row.remark}
            db.add(SystemAccountLicenseAudit(audit_id=f'audit_{uuid4().hex}', batch_id=f'batch_{uuid4().hex}', request_id=f'remark_{uuid4().hex}', user_id=user_id, operator_user_id=int(actor.user.user_id), action='remark_update', previous_state=previous, new_state=current, remark=data.remark))
            await db.commit()
            return current | {'userId': str(user_id)}
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def audit(
        cls,
        db: AsyncSession,
        actor: CurrentUserModel,
        page: int = 1,
        page_size: int = 50,
        user_id: int | None = None,
        account_keyword: str | None = None,
        operator_keyword: str | None = None,
        action: str | None = None,
        batch_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        cls.require_super_admin(actor, 'system:license:audit')
        target_user = aliased(SysUser)
        operator_user = aliased(SysUser)
        query = (
            select(
                SystemAccountLicenseAudit,
                target_user.user_name.label('target_user_name'),
                operator_user.user_name.label('operator_user_name'),
            )
            .outerjoin(target_user, target_user.user_id == SystemAccountLicenseAudit.user_id)
            .outerjoin(operator_user, operator_user.user_id == SystemAccountLicenseAudit.operator_user_id)
        )
        if user_id is not None:
            query = query.where(SystemAccountLicenseAudit.user_id == user_id)
        if account_keyword:
            query = query.where(
                or_(
                    target_user.user_name.like(f'%{account_keyword}%'),
                    target_user.nick_name.like(f'%{account_keyword}%'),
                )
            )
        if operator_keyword:
            query = query.where(
                or_(
                    operator_user.user_name.like(f'%{operator_keyword}%'),
                    operator_user.nick_name.like(f'%{operator_keyword}%'),
                )
            )
        if action:
            query = query.where(SystemAccountLicenseAudit.action == action)
        if batch_id:
            query = query.where(SystemAccountLicenseAudit.batch_id == batch_id)
        if start_time:
            query = query.where(SystemAccountLicenseAudit.created_at >= start_time)
        if end_time:
            query = query.where(SystemAccountLicenseAudit.created_at <= end_time)
        total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = (
            await db.execute(
                query.order_by(SystemAccountLicenseAudit.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return {
            'pageNum': page,
            'pageSize': page_size,
            'total': total,
            'rows': [
                {
                    'auditId': row.audit_id,
                    'batchId': row.batch_id,
                    'requestId': row.request_id,
                    'userId': str(row.user_id),
                    'userName': target_user_name,
                    'operatorUserId': str(row.operator_user_id),
                    'operatorUserName': operator_user_name,
                    'action': row.action,
                    'previousState': row.previous_state,
                    'newState': row.new_state,
                    'remark': row.remark,
                    'createdAt': row.created_at.isoformat(),
                }
                for row, target_user_name, operator_user_name in rows
            ],
        }

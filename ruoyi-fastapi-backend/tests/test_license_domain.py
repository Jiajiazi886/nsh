from datetime import datetime, timedelta

import pytest

from module_integration.license import calculate_grant
from module_integration.license import LicenseService
from common.constant import CommonConstant
from types import SimpleNamespace


def _actor(role_id, role_key, *, permissions=None):
    return SimpleNamespace(
        permissions=permissions or [],
        roles=[role_key],
        user=SimpleNamespace(
            role=[SimpleNamespace(role_id=role_id, role_key=role_key)],
            role_ids=str(role_id),
        ),
    )


def test_license_super_admin_requires_canonical_role_pair():
    assert LicenseService._has_canonical_super_admin_role(_actor(1, CommonConstant.SUPER_ADMIN_ROLE_KEY))
    assert not LicenseService._has_canonical_super_admin_role(_actor(2, CommonConstant.SUPER_ADMIN_ROLE_KEY))
    assert not LicenseService._has_canonical_super_admin_role(_actor(1, 'admin'))


def test_new_monthly_grant_starts_now() -> None:
    now = datetime(2026, 9, 19, 10, 0, 0)
    valid_from, expires_at = calculate_grant(now, None, None, 'monthly')
    assert valid_from == now
    assert expires_at == now + timedelta(days=30)


def test_unexpired_grant_extends_from_existing_expiration() -> None:
    now = datetime(2026, 9, 19, 10, 0, 0)
    old_expiration = now + timedelta(days=3)
    valid_from, expires_at = calculate_grant(now, old_expiration, 'weekly', 'daily')
    assert valid_from == old_expiration
    assert expires_at == old_expiration + timedelta(days=1)


def test_expired_grant_starts_from_server_time() -> None:
    now = datetime(2026, 9, 19, 10, 0, 0)
    valid_from, expires_at = calculate_grant(now, now - timedelta(seconds=1), 'daily', 'weekly')
    assert valid_from == now
    assert expires_at == now + timedelta(days=7)


def test_permanent_grant_has_no_expiration() -> None:
    now = datetime(2026, 9, 19, 10, 0, 0)
    assert calculate_grant(now, None, None, 'permanent') == (now, None)


def test_temporary_grant_cannot_replace_permanent_without_revoke() -> None:
    now = datetime(2026, 9, 19, 10, 0, 0)
    with pytest.raises(Exception, match='永久授权必须先撤销'):
        calculate_grant(now, None, 'permanent', 'daily')


def test_revoked_permanent_grant_can_be_replaced_after_explicit_revoke() -> None:
    now = datetime(2026, 9, 19, 10, 0, 0)
    valid_from, expires_at = calculate_grant(now, None, 'permanent', 'daily', 'revoked')
    assert valid_from == now
    assert expires_at == now + timedelta(days=1)

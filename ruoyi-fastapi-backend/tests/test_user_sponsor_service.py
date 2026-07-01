from datetime import datetime
from types import SimpleNamespace

import pytest

from module_admin.service.user_service import UserService


class FakeDb:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True


def test_effective_vip_prefers_sponsored_source():
    user = SimpleNamespace(is_vip='0', vip_expire_time=None, sponsored_vip='1')

    assert UserService.is_effective_vip(user) is True
    assert UserService.get_effective_vip_type(user) == 'sponsored'


def test_effective_vip_uses_manual_vip_when_not_sponsored():
    user = SimpleNamespace(is_vip='1', vip_expire_time=datetime(2099, 1, 1), sponsored_vip='0')

    assert UserService.is_effective_vip(user) is True
    assert UserService.get_effective_vip_type(user) == 'manual'


@pytest.mark.asyncio
async def test_change_sponsor_updates_switch_and_syncs_members(monkeypatch):
    calls = []

    async def fake_change_sponsor_enabled(db, user_id, enabled, update_by):
        calls.append(('switch', user_id, enabled, update_by))

    async def fake_sync_sponsored_members(db, user_id, enabled, update_by):
        calls.append(('sync', user_id, enabled, update_by))

    monkeypatch.setattr('module_admin.service.user_service.UserDao.change_sponsor_enabled', fake_change_sponsor_enabled)
    monkeypatch.setattr('module_admin.service.user_service.UserDao.sync_sponsored_members', fake_sync_sponsored_members)

    db = FakeDb()
    result = await UserService.change_sponsor_services(db, 200, '1', 'admin')

    assert result.is_success is True
    assert db.committed is True
    assert calls == [('switch', 200, '1', 'admin'), ('sync', 200, True, 'admin')]

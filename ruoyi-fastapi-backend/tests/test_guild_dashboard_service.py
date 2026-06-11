from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from exceptions.exception import ServiceException
from module_guild.service.battle_registration_service import BattleRegistrationService
from module_guild.service.dashboard_service import DashboardService


def make_current_user(user_id=1, roles=None, admin=False):
    return SimpleNamespace(
        roles=roles or [],
        user=SimpleNamespace(
            user_id=user_id,
            user_name='tester',
            nick_name='测试用户',
            admin=admin,
        ),
    )


def test_dashboard_scope_admin_uses_global_data():
    current_user = make_current_user(user_id=1, roles=['admin'], admin=True)

    assert DashboardService._get_role_scope(current_user) == 'admin'
    assert DashboardService._get_owner_user_id('admin', current_user.user.user_id) is None


def test_dashboard_scope_common_uses_own_guild():
    current_user = make_current_user(user_id=101, roles=['common'])

    assert DashboardService._get_role_scope(current_user) == 'common'
    assert DashboardService._get_owner_user_id('common', current_user.user.user_id) == 101


def test_dashboard_scope_user_does_not_use_global_battle_data():
    current_user = make_current_user(user_id=106, roles=['user'])

    assert DashboardService._get_role_scope(current_user) == 'user'
    assert DashboardService._get_owner_user_id('user', current_user.user.user_id) is None


@pytest.mark.asyncio
async def test_dashboard_user_battle_payload_is_honest_empty_state():
    battle_summary, latest_battles, latest_record_summary, top_records = await DashboardService._build_battle_payload(
        db=None,
        scope='user',
        owner_user_id=None,
    )

    assert battle_summary == {'total': 0, 'completed': 0, 'wins': 0, 'losses': 0, 'win_rate': 0}
    assert latest_battles == []
    assert latest_record_summary is None
    assert top_records == []


@pytest.mark.asyncio
async def test_battle_registration_rejects_review_when_invite_disabled(monkeypatch):
    registration = SimpleNamespace(
        registration_id=10,
        owner_user_id=101,
        invite_id=20,
    )
    invite = SimpleNamespace(
        owner_user_id=101,
        status='1',
        expire_time=datetime.now(),
    )

    async def fake_get_pending_registration_by_id(db, registration_id):
        return registration

    async def fake_get_invite_by_id(db, invite_id):
        return invite

    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_pending_registration_by_id',
        fake_get_pending_registration_by_id,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_invite_by_id',
        fake_get_invite_by_id,
    )

    current_user = make_current_user(user_id=101, roles=['common'])

    with pytest.raises(ServiceException) as exc_info:
        await BattleRegistrationService._get_scoped_pending_registration(None, current_user, 10)
    assert exc_info.value.message == '报名链接已失效，不能继续审核'


@pytest.mark.asyncio
async def test_battle_registration_rejects_review_when_invite_expired(monkeypatch):
    registration = SimpleNamespace(
        registration_id=10,
        owner_user_id=101,
        invite_id=20,
    )
    invite = SimpleNamespace(
        owner_user_id=101,
        status='0',
        expire_time=datetime.now() - timedelta(minutes=1),
    )

    async def fake_get_pending_registration_by_id(db, registration_id):
        return registration

    async def fake_get_invite_by_id(db, invite_id):
        return invite

    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_pending_registration_by_id',
        fake_get_pending_registration_by_id,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_invite_by_id',
        fake_get_invite_by_id,
    )

    current_user = make_current_user(user_id=101, roles=['common'])

    with pytest.raises(ServiceException) as exc_info:
        await BattleRegistrationService._get_scoped_pending_registration(None, current_user, 10)
    assert exc_info.value.message == '报名链接已失效，不能继续审核'


@pytest.mark.asyncio
async def test_battle_registration_common_scope_rejects_foreign_registration(monkeypatch):
    registration = SimpleNamespace(
        registration_id=10,
        owner_user_id=202,
        invite_id=20,
    )

    async def fake_get_pending_registration_by_id(db, registration_id):
        return registration

    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_pending_registration_by_id',
        fake_get_pending_registration_by_id,
    )

    current_user = make_current_user(user_id=101, roles=['common'])

    with pytest.raises(ServiceException) as exc_info:
        await BattleRegistrationService._get_scoped_pending_registration(None, current_user, 10)
    assert exc_info.value.message == '只能处理自己帮会的约战报名'


@pytest.mark.asyncio
async def test_battle_invite_delete_rejects_active_invite(monkeypatch):
    invite = SimpleNamespace(
        invite_id=20,
        owner_user_id=101,
        status='0',
        expire_time=datetime.now() + timedelta(hours=1),
    )

    async def fake_get_invite_by_id(db, invite_id):
        return invite

    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_invite_by_id',
        fake_get_invite_by_id,
    )

    current_user = make_current_user(user_id=101, roles=['common'])

    with pytest.raises(ServiceException) as exc_info:
        await BattleRegistrationService.delete_invite_service(None, current_user, 20)
    assert exc_info.value.message == '生效中的链接不能删除，请先强制失效'


@pytest.mark.asyncio
async def test_battle_invite_delete_soft_deletes_disabled_invite(monkeypatch):
    calls = []
    invite = SimpleNamespace(
        invite_id=20,
        owner_user_id=101,
        status='1',
        expire_time=datetime.now() + timedelta(hours=1),
    )

    class FakeDb:
        async def commit(self):
            calls.append(('commit', None))

    async def fake_get_invite_by_id(db, invite_id):
        calls.append(('get', invite_id))
        return invite

    async def fake_delete_invite(db, invite_id):
        calls.append(('delete', invite_id))

    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_invite_by_id',
        fake_get_invite_by_id,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.delete_invite',
        fake_delete_invite,
    )

    current_user = make_current_user(user_id=101, roles=['common'])
    result = await BattleRegistrationService.delete_invite_service(FakeDb(), current_user, 20)

    assert calls == [('get', 20), ('delete', 20), ('commit', None)]
    assert result.message == '约战链接已删除'


@pytest.mark.asyncio
async def test_battle_invite_creation_disables_existing_active_invite(monkeypatch):
    events = []

    class FakeDb:
        async def commit(self):
            events.append(('commit', None))

    data = SimpleNamespace(
        battle_name='  周六据点约战  ',
        battle_time='2026-06-12T20:00:00',
        expire_hours=24,
        remark='  集合提前十分钟  ',
    )
    current_user = make_current_user(user_id=101, roles=['common'])

    async def fake_new_invite_code(db):
        return 'invitecode001'

    async def fake_disable_active_invites_for_owner(db, owner_user_id):
        events.append(('disable', owner_user_id))

    async def fake_create_invite(db, payload):
        events.append(('create', payload))
        return SimpleNamespace(invite_id=88)

    monkeypatch.setattr(BattleRegistrationService, '_new_invite_code', fake_new_invite_code)
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.disable_active_invites_for_owner',
        fake_disable_active_invites_for_owner,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.create_invite',
        fake_create_invite,
    )

    result = await BattleRegistrationService.create_invite_service(FakeDb(), current_user, data)

    assert events[0] == ('disable', 101)
    assert events[1][0] == 'create'
    assert events[2] == ('commit', None)
    assert events[1][1]['battle_name'] == '周六据点约战'
    assert events[1][1]['remark'] == '集合提前十分钟'
    assert result['invite_id'] == 88
    assert result['public_path'] == '/public/battle/invitecode001'


@pytest.mark.asyncio
async def test_battle_registration_list_uses_current_active_invite(monkeypatch):
    calls = []
    registration = SimpleNamespace(
        registration_id=1,
        invite_id=555,
        invite_code='active',
        guild_id=101,
        owner_user_id=101,
        member_id=9,
        player_name='测试玩家',
        player_class='素问',
        secondary_class='',
        role_in_guild='',
        applicant_name='',
        applicant_contact='',
        apply_time=datetime.now(),
        approval_status='0',
        approval_time=None,
        approval_by='',
        approval_comment='',
        remark='',
    )

    class FakeDb:
        def __init__(self):
            self.commit_count = 0

        async def commit(self):
            self.commit_count += 1
            calls.append(('commit', None))

    class ExpiringInvite:
        def __init__(self, db):
            self._db = db
            self._loaded_commit_count = db.commit_count

        @property
        def invite_id(self):
            if self._db.commit_count > self._loaded_commit_count:
                raise AssertionError('invite_id was read after commit expired the ORM object')
            return 555

    async def fake_mark_expired_invites(db):
        calls.append(('mark_expired', None))

    async def fake_get_latest_active_invite(db, owner_user_id):
        calls.append(('latest_active', owner_user_id))
        return ExpiringInvite(db)

    async def fake_list_registrations(db, owner_user_id, status, invite_id):
        calls.append(('list', owner_user_id, status, invite_id))
        return [registration]

    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.mark_expired_invites',
        fake_mark_expired_invites,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_latest_active_invite',
        fake_get_latest_active_invite,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.list_registrations',
        fake_list_registrations,
    )

    current_user = make_current_user(user_id=101, roles=['common'])
    result = await BattleRegistrationService.list_registrations_service(FakeDb(), current_user, status='0')

    assert ('mark_expired', None) in calls
    assert ('latest_active', 101) in calls
    assert ('commit', None) in calls
    assert ('list', 101, '0', 555) in calls
    assert result[0]['registration_id'] == 1

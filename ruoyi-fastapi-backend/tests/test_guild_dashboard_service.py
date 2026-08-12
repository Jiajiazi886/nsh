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


def test_dashboard_scope_admin_uses_own_member_management_roster():
    current_user = make_current_user(user_id=1, roles=['admin'], admin=True)

    assert DashboardService._get_role_scope(current_user) == 'admin'
    assert DashboardService._get_owner_user_id('admin', current_user.user.user_id) is None
    assert DashboardService._get_member_owner_user_id('admin', current_user.user.user_id) == 1


def test_dashboard_scope_common_uses_own_guild():
    current_user = make_current_user(user_id=101, roles=['common'])

    assert DashboardService._get_role_scope(current_user) == 'common'
    assert DashboardService._get_owner_user_id('common', current_user.user.user_id) == 101
    assert DashboardService._get_member_owner_user_id('common', current_user.user.user_id) == 101


def test_dashboard_scope_user_does_not_use_global_battle_data():
    current_user = make_current_user(user_id=106, roles=['user'])

    assert DashboardService._get_role_scope(current_user) == 'user'
    assert DashboardService._get_owner_user_id('user', current_user.user.user_id) is None
    assert DashboardService._get_member_owner_user_id('user', current_user.user.user_id) is None


@pytest.mark.asyncio
async def test_admin_dashboard_member_widgets_use_current_users_member_management_scope(monkeypatch):
    current_user = make_current_user(user_id=1, roles=['admin'], admin=True)
    calls = []

    async def fake_list_enabled_professions(db):
        return []

    async def fake_build_guild_payload(db, current_user, scope, membership):
        return {}

    async def fake_build_member_summary(db, scope, owner_user_id, current_user_id, profession_names):
        calls.append(('member_summary', owner_user_id))
        return {}

    async def fake_build_class_distribution(db, owner_user_id, member_user_id, profession_names):
        calls.append(('class_distribution', owner_user_id))
        return []

    async def fake_build_battle_payload(db, scope, owner_user_id):
        return {}, [], None, []

    async def fake_build_review_summary(db, scope, owner_user_id, current_user_id):
        return {}

    async def fake_build_schedule_summary(db, scope, owner_user_id, membership):
        return {}

    async def fake_build_active_invite_summary(db, scope, owner_user_id, profession_names):
        calls.append(('active_invite', owner_user_id))
        return None

    monkeypatch.setattr(
        'module_guild.service.dashboard_service.DashboardDao.list_enabled_professions',
        fake_list_enabled_professions,
    )
    monkeypatch.setattr(DashboardService, '_build_guild_payload', fake_build_guild_payload)
    monkeypatch.setattr(DashboardService, '_build_member_summary', fake_build_member_summary)
    monkeypatch.setattr(DashboardService, '_build_class_distribution', fake_build_class_distribution)
    monkeypatch.setattr(DashboardService, '_build_battle_payload', fake_build_battle_payload)
    monkeypatch.setattr(DashboardService, '_build_review_summary', fake_build_review_summary)
    monkeypatch.setattr(DashboardService, '_build_schedule_summary', fake_build_schedule_summary)
    monkeypatch.setattr(DashboardService, '_build_active_invite_summary', fake_build_active_invite_summary)

    await DashboardService.get_summary_service(db=None, current_user=current_user)

    assert ('member_summary', 1) in calls
    assert ('class_distribution', 1) in calls
    assert ('active_invite', 1) in calls


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
        registration_type='signup',
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

    async def fake_list_registrations(db, owner_user_id, status, invite_id, registration_type='signup', status_list=None):
        calls.append(('list', owner_user_id, status, invite_id, registration_type, status_list))
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
    assert ('list', 101, '0', 555, 'signup', None) in calls
    assert result[0]['registration_id'] == 1


@pytest.mark.asyncio
async def test_public_leave_submission_creates_leave_registration(monkeypatch):
    calls = []
    invite = SimpleNamespace(invite_id=88, invite_code='code001', owner_user_id=101)
    member = SimpleNamespace(
        member_id=9,
        player_name='测试玩家',
        player_class='素问',
        secondary_class='',
        role_in_guild='成员',
    )

    class FakeDb:
        async def commit(self):
            calls.append(('commit', None))

    async def fake_get_invite_or_raise(db, invite_code):
        return invite

    async def fake_get_member_for_invite(db, owner_user_id, member_id):
        return member

    async def fake_get_effective_registration(db, invite_id, member_id, registration_type=None):
        calls.append(('exists', invite_id, member_id, registration_type))
        return None

    async def fake_create_registration(db, payload):
        calls.append(('create', payload))
        return SimpleNamespace(registration_id=1)

    monkeypatch.setattr(BattleRegistrationService, '_get_active_invite_or_raise', fake_get_invite_or_raise)
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_member_for_invite',
        fake_get_member_for_invite,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_effective_registration',
        fake_get_effective_registration,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.create_registration',
        fake_create_registration,
    )

    result = await BattleRegistrationService.submit_public_leave_service(
        FakeDb(),
        'code001',
        SimpleNamespace(member_id=9, remark='周四加班'),
    )

    assert result.message == '请假申请已提交，请等待审核'
    assert ('exists', 88, 9, None) in calls
    assert calls[1][0] == 'create'
    assert calls[1][1]['registration_type'] == 'leave'
    assert calls[1][1]['remark'] == '周四加班'
    assert calls[2] == ('commit', None)


@pytest.mark.asyncio
async def test_public_signup_submission_auto_cancels_existing_leave(monkeypatch):
    calls = []
    invite = SimpleNamespace(invite_id=88, invite_code='code001', owner_user_id=101)
    member = SimpleNamespace(
        member_id=9,
        player_name='测试玩家',
        player_class='素问',
        secondary_class='',
        role_in_guild='成员',
    )
    existing = SimpleNamespace(registration_type='leave')

    class FakeDb:
        async def commit(self):
            calls.append(('commit', None))

    async def fake_get_invite_or_raise(db, invite_code):
        return invite

    async def fake_get_member_for_invite(db, owner_user_id, member_id):
        return member

    async def fake_get_effective_registration(db, invite_id, member_id, registration_type=None):
        return existing

    async def fake_cancel_effective_registration(db, invite_id, member_id, registration_type):
        calls.append(('cancel', invite_id, member_id, registration_type))
        return 1

    async def fake_create_registration(db, payload):
        calls.append(('create', payload))
        return SimpleNamespace(registration_id=1)

    monkeypatch.setattr(BattleRegistrationService, '_get_active_invite_or_raise', fake_get_invite_or_raise)
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_member_for_invite',
        fake_get_member_for_invite,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_effective_registration',
        fake_get_effective_registration,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.cancel_effective_registration',
        fake_cancel_effective_registration,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.create_registration',
        fake_create_registration,
    )

    result = await BattleRegistrationService.submit_public_registration_service(
        FakeDb(),
        'code001',
        SimpleNamespace(member_id=9, player_class='', secondary_class='', applicant_name='', applicant_contact='', remark=''),
    )

    assert calls[0] == ('cancel', 88, 9, 'leave')
    assert calls[1][0] == 'create'
    assert calls[1][1]['registration_type'] == 'signup'
    assert calls[2] == ('commit', None)
    assert result.message == '约战报名已提交，原请假申请已自动取消'


@pytest.mark.asyncio
async def test_public_leave_submission_auto_cancels_existing_signup(monkeypatch):
    calls = []
    invite = SimpleNamespace(invite_id=88, invite_code='code001', owner_user_id=101)
    member = SimpleNamespace(
        member_id=9,
        player_name='测试玩家',
        player_class='素问',
        secondary_class='',
        role_in_guild='成员',
    )
    existing = SimpleNamespace(registration_type='signup')

    class FakeDb:
        async def commit(self):
            calls.append(('commit', None))

    async def fake_get_invite_or_raise(db, invite_code):
        return invite

    async def fake_get_member_for_invite(db, owner_user_id, member_id):
        return member

    async def fake_get_effective_registration(db, invite_id, member_id, registration_type=None):
        return existing

    async def fake_cancel_effective_registration(db, invite_id, member_id, registration_type):
        calls.append(('cancel', invite_id, member_id, registration_type))
        return 1

    async def fake_create_registration(db, payload):
        calls.append(('create', payload))
        return SimpleNamespace(registration_id=1)

    monkeypatch.setattr(BattleRegistrationService, '_get_active_invite_or_raise', fake_get_invite_or_raise)
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_member_for_invite',
        fake_get_member_for_invite,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.get_effective_registration',
        fake_get_effective_registration,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.cancel_effective_registration',
        fake_cancel_effective_registration,
    )
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.BattleRegistrationDao.create_registration',
        fake_create_registration,
    )

    result = await BattleRegistrationService.submit_public_leave_service(
        FakeDb(),
        'code001',
        SimpleNamespace(member_id=9, remark='周四加班'),
    )

    assert calls[0] == ('cancel', 88, 9, 'signup')
    assert calls[1][0] == 'create'
    assert calls[1][1]['registration_type'] == 'leave'
    assert calls[2] == ('commit', None)
    assert result.message == '请假申请已提交，原约战报名已自动取消'


@pytest.mark.asyncio
async def test_leave_schedule_list_uses_active_invite_and_effective_statuses(monkeypatch):
    calls = []
    registration = SimpleNamespace(
        registration_id=2,
        invite_id=555,
        invite_code='active',
        registration_type='leave',
        guild_id=101,
        owner_user_id=101,
        member_id=12,
        player_name='请假玩家',
        player_class='铁衣',
        secondary_class='',
        role_in_guild='成员',
        applicant_name='',
        applicant_contact='',
        apply_time=datetime.now(),
        approval_status='0',
        approval_time=None,
        approval_by='',
        approval_comment='',
        remark='外出',
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

    async def fake_list_registrations(db, owner_user_id, status=None, invite_id=None, registration_type='signup', status_list=None):
        calls.append(('list', owner_user_id, status, invite_id, registration_type, tuple(status_list or [])))
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
    result = await BattleRegistrationService.list_leave_registrations_for_schedule_service(FakeDb(), current_user)

    assert ('list', 101, None, 555, 'leave', ('0', '1')) in calls
    assert result[0]['registration_type'] == 'leave'
    assert result[0]['member_id'] == 12

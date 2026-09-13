from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.dialects import mysql

from exceptions.exception import AuthException, PermissionException, ServiceException
from module_guild.dao.battle_registration_dao import BattleRegistrationDao
from module_guild.entity.vo.battle_registration_vo import (
    PublicBattleLeaveApplicationModel,
    PublicBattleRegistrationModel,
)
from module_guild.service.battle_registration_service import BattleRegistrationService

from .helpers import FakeDB


@pytest.fixture
def choice(monkeypatch):
    state = SimpleNamespace(
        db=FakeDB(),
        user=SimpleNamespace(user=SimpleNamespace(user_id=23), roles=['user']),
        invite=SimpleNamespace(
            invite_id=71,
            invite_code='invite-a',
            owner_user_id=101,
            status='0',
            expire_time=datetime.now() + timedelta(hours=1),
        ),
        member=SimpleNamespace(
            member_id=9,
            user_id=101,
            member_user_id=23,
            player_name='玩家甲',
            player_class='铁衣',
            secondary_class='素问',
            role_in_guild='成员',
        ),
        writes=[],
        cancellations=[],
        locks=[],
        invite_locks=[],
        existing=None,
    )

    async def active(db, code, *, for_update=False):
        assert code == 'invite-a'
        state.invite_locks.append(for_update)
        return state.invite

    async def read_member(db, owner_id, member_id):
        assert owner_id == 101 and member_id == 9
        return state.member

    async def lock_member(db, owner_id, member_id):
        state.locks.append((owner_id, member_id))
        return await read_member(db, owner_id, member_id)

    async def existing(db, invite_id, member_id, *, ensure_schema=True):
        assert not ensure_schema, 'Do not run lazy DDL inside the protected mutation'
        return state.existing

    async def cancel(db, invite_id, member_id, kind, *, ensure_schema=True):
        assert not ensure_schema, 'Do not run lazy DDL inside the protected mutation'
        state.cancellations.append(kind)

    async def create(db, data, *, ensure_schema=True):
        assert not ensure_schema, 'Do not run lazy DDL inside the protected mutation'
        state.writes.append(data)

    monkeypatch.setattr(BattleRegistrationService, '_get_active_invite_or_raise', active)
    monkeypatch.setattr(BattleRegistrationDao, 'get_member_for_invite', read_member)
    monkeypatch.setattr(BattleRegistrationDao, 'lock_member_for_invite', lock_member, raising=False)
    monkeypatch.setattr(BattleRegistrationDao, 'get_effective_registration', existing)
    monkeypatch.setattr(BattleRegistrationDao, 'cancel_effective_registration', cancel)
    monkeypatch.setattr(BattleRegistrationDao, 'create_registration', create)
    return state


async def submit(choice, kind, *, user=True):
    model = PublicBattleLeaveApplicationModel if kind == 'leave' else PublicBattleRegistrationModel
    method = getattr(
        BattleRegistrationService, f'submit_public_{"leave" if kind == "leave" else "registration"}_service'
    )
    kwargs = {'current_user': choice.user} if user else {}
    return await method(choice.db, 'invite-a', model(member_id=9, remark='测试'), **kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_service_never_allows_anonymous_mutation(choice, kind):
    with pytest.raises(AuthException):
        await submit(choice, kind, user=False)
    assert choice.invite_locks == choice.locks == choice.writes == choice.cancellations == []


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_personal_registration_records_real_account_and_uses_locks(choice, kind):
    result = await submit(choice, kind)
    assert result.is_success
    assert choice.invite_locks == [True]
    assert choice.locks == [(101, 9)]
    assert choice.writes[0]['applicant_user_id'] == 23
    assert choice.writes[0]['registration_type'] == kind
    assert choice.writes[0]['guild_id'] == 101
    assert choice.db.commits == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
@pytest.mark.parametrize('field,value', [('member_user_id', 24), ('member_user_id', 0), ('user_id', 202)])
async def test_other_account_unbound_or_wrong_guild_is_rejected(choice, kind, field, value):
    setattr(choice.member, field, value)
    with pytest.raises(PermissionException):
        await submit(choice, kind)
    assert choice.writes == choice.cancellations == []
    assert choice.db.commits == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_administrator_role_is_not_permission_to_impersonate_a_member(choice, kind):
    choice.user.roles = ['admin']
    choice.member.member_user_id = 24
    with pytest.raises(PermissionException):
        await submit(choice, kind)
    assert choice.writes == []


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_signup_and_leave_switch_only_the_same_member_in_one_transaction(choice, kind):
    old = 'signup' if kind == 'leave' else 'leave'
    choice.existing = SimpleNamespace(registration_type=old)
    await submit(choice, kind)
    assert choice.cancellations == [old]
    assert choice.db.commits == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_duplicate_does_not_cancel_or_rewrite_existing_record(choice, kind):
    choice.existing = SimpleNamespace(registration_type=kind)
    with pytest.raises(ServiceException):
        await submit(choice, kind)
    assert choice.cancellations == choice.writes == []


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_write_failure_rolls_back_the_previous_choice(choice, monkeypatch, kind):
    choice.existing = SimpleNamespace(registration_type='signup' if kind == 'leave' else 'leave')

    async def broken(db, data, **kwargs):
        raise RuntimeError('synthetic insert failure')

    monkeypatch.setattr(BattleRegistrationDao, 'create_registration', broken)
    with pytest.raises(RuntimeError, match='synthetic insert failure'):
        await submit(choice, kind)
    assert choice.db.rollbacks == 1 and choice.db.commits == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
@pytest.mark.parametrize('closed', [True, False])
async def test_invitation_validity_is_rechecked_under_the_lock(choice, kind, closed):
    if closed:
        choice.invite.status = '1'
    else:
        choice.invite.expire_time = datetime.now() - timedelta(seconds=1)
    with pytest.raises(ServiceException):
        await submit(choice, kind)
    assert choice.writes == choice.cancellations == []


@pytest.mark.asyncio
async def test_dao_member_lock_has_owner_and_active_filters():
    db = FakeDB()
    await BattleRegistrationDao.lock_member_for_invite(db, 101, 9)
    statement = db.statements[0]
    sql = str(statement.compile(dialect=mysql.dialect()))
    assert 'FOR UPDATE' in sql
    assert 'guild_member.user_id' in sql and 'guild_member.is_active' in sql and 'guild_member.member_id' in sql
    assert set(statement.compile().params.values()) == {101, 9, '1'}


@pytest.mark.asyncio
async def test_dao_invitation_lock_preserves_not_deleted_filter():
    db = FakeDB()
    await BattleRegistrationDao.lock_invite_by_code(db, 'invite-a')
    statement = db.statements[0]
    assert 'FOR UPDATE' in str(statement.compile(dialect=mysql.dialect()))
    assert set(statement.compile().params.values()) == {'invite-a', '0'}


@pytest.mark.asyncio
@pytest.mark.parametrize('profession', ['碎梦', '素问'])
async def test_signup_profession_is_derived_from_verified_member_choices(choice, profession):
    data = PublicBattleRegistrationModel(member_id=9, player_class=profession)
    if profession == '碎梦':
        with pytest.raises(PermissionException):
            await BattleRegistrationService.submit_public_registration_service(
                choice.db, 'invite-a', data, current_user=choice.user
            )
        assert choice.cancellations == choice.writes == []
    else:
        await BattleRegistrationService.submit_public_registration_service(
            choice.db, 'invite-a', data, current_user=choice.user
        )
        assert choice.writes[0]['player_class'] == profession

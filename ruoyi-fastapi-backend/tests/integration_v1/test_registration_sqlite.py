"""Real local transaction regression; this does not claim InnoDB concurrency proof."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import Integer, create_engine, event, select
from sqlalchemy.orm import Session

from config.get_db import get_db
from exceptions.handle import handle_exception
from module_guild.controller.battle_registration_controller import public_battle_registration_controller
from module_guild.entity.do.battle_registration_do import GuildBattleInvite, GuildBattleRegistration
from module_guild.entity.do.member_do import GuildMember
from module_guild.entity.vo.battle_registration_vo import (
    PublicBattleLeaveApplicationModel,
    PublicBattleRegistrationModel,
)
from module_guild.service.battle_registration_service import BattleRegistrationService


class LocalTransaction:
    def __init__(self, session):
        self.session = session
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return self.session.execute(statement)

    def add(self, row):
        self.session.add(row)

    async def flush(self):
        self.session.flush()

    async def commit(self):
        self.session.commit()

    async def rollback(self):
        self.session.rollback()


@pytest.fixture
def local_rows(monkeypatch):
    models = (GuildBattleInvite, GuildMember, GuildBattleRegistration)
    # SQLite needs INTEGER PRIMARY KEY for autoincrement; production metadata
    # stays BigInteger and is restored by monkeypatch after this test.
    for model in models:
        for column in model.__table__.primary_key.columns:
            monkeypatch.setattr(column, 'type', column.type.with_variant(Integer(), 'sqlite'))
    engine = create_engine('sqlite+pysqlite:///:memory:')
    GuildBattleInvite.metadata.create_all(engine, tables=[model.__table__ for model in models])
    session = Session(engine, expire_on_commit=False)
    invite = GuildBattleInvite(
        invite_id=71,
        invite_code='invite-a',
        owner_user_id=101,
        battle_name='本地测试',
        status='0',
        expire_time=datetime.now() + timedelta(hours=1),
        del_flag='0',
    )
    member = GuildMember(
        member_id=9,
        guild_id=101,
        user_id=101,
        member_user_id=23,
        player_name='玩家甲',
        player_class='铁衣',
        secondary_class='素问',
        is_active='1',
    )
    session.add_all([invite, member])
    session.commit()
    db = LocalTransaction(session)
    yield SimpleNamespace(
        session=session,
        db=db,
        invite=invite,
        member=member,
        user=SimpleNamespace(user=SimpleNamespace(user_id=23), roles=['user']),
    )
    session.close()
    engine.dispose()


async def submit(rows, kind):
    model = PublicBattleLeaveApplicationModel if kind == 'leave' else PublicBattleRegistrationModel
    method = getattr(
        BattleRegistrationService, f'submit_public_{"leave" if kind == "leave" else "registration"}_service'
    )
    return await method(rows.db, 'invite-a', model(member_id=9), current_user=rows.user)


@pytest.mark.asyncio
@pytest.mark.parametrize('first', ['leave', 'signup'])
async def test_real_transaction_preserves_history_and_only_one_effective_choice(local_rows, first):
    await submit(local_rows, first)
    second = 'signup' if first == 'leave' else 'leave'
    await submit(local_rows, second)
    records = local_rows.session.scalars(
        select(GuildBattleRegistration).order_by(GuildBattleRegistration.registration_id)
    ).all()
    assert len(records) == 2
    assert [(row.registration_type, row.del_flag, row.applicant_user_id) for row in records] == [
        (first, '1', 23),
        (second, '0', 23),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize('first', ['leave', 'signup'])
async def test_insert_failure_actually_restores_previous_database_row(local_rows, first):
    await submit(local_rows, first)
    second = 'signup' if first == 'leave' else 'leave'

    def reject_new_choice(session, flush_context, instances):
        if any(isinstance(row, GuildBattleRegistration) and row.registration_type == second for row in session.new):
            raise RuntimeError('synthetic failed new choice')

    event.listen(local_rows.session, 'before_flush', reject_new_choice)
    try:
        with pytest.raises(RuntimeError, match='synthetic failed new choice'):
            await submit(local_rows, second)
    finally:
        event.remove(local_rows.session, 'before_flush', reject_new_choice)
    records = local_rows.session.scalars(select(GuildBattleRegistration)).all()
    assert len(records) == 1 and records[0].registration_type == first and records[0].del_flag == '0'


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
@pytest.mark.parametrize('bound_account', [23, 24, 0])
@pytest.mark.parametrize('api_family', ['legacy', 'v1'])
async def test_actual_http_auth_and_business_service_use_the_same_account(
    auth_state, local_rows, kind, bound_account, api_family
):
    local_rows.member.member_user_id = bound_account
    local_rows.session.commit()
    app = FastAPI()
    app.state.redis = auth_state.redis
    handle_exception(app)
    if api_family == 'legacy':
        app.include_router(public_battle_registration_controller)
        path, data = f'/public/battle/invite-a/{kind}', {'member_id': 9}
    else:
        from module_integration.controller.api_v1_controller import api_v1_controller

        app.include_router(api_v1_controller)
        path, data = f'/api/v1/invitations/invite-a/{kind}', {'memberId': '9'}

    async def db():
        yield local_rows.db

    app.dependency_overrides[get_db] = db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
        result = await client.post(path, json=data, headers={'Authorization': f'Bearer {auth_state.token()}'})
    records = local_rows.session.scalars(select(GuildBattleRegistration)).all()
    if bound_account == 23:
        assert result.json()['code'] == 200 and len(records) == 1
        assert records[0].applicant_user_id == 23
    else:
        assert result.json()['code'] == 403 and records == []
    if api_family == 'v1':
        assert result.status_code == (200 if bound_account == 23 else 403)

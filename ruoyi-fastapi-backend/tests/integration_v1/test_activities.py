from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import MissingGreenlet

from module_guild.entity.do.member_do import GuildMember
from module_guild.entity.do.profession_do import GuildProfession
from module_guild.entity.do.battle_do import GuildBattle, GuildBattleRecord
from module_admin.entity.do.user_do import SysUser
from module_integration.activities.models import (
    Activity,
    Organization,
    OrganizationMember,
    ActivitySnapshot,
    Participation,
    MutationReceipt,
    ReportLink,
    ActivityLeaveLink,
    ActivityLeaveRecord,
)
from module_integration.activities.service import ActivityService
from module_integration.activities.schema import (
    CreateActivity,
    SaveLineup,
    ChangeActivity,
    SignupSeat,
    LeaveSeat,
    LinkReport,
    ImportActivityReport,
)
from module_integration.contract import ApiProblem
from .test_registration_sqlite import LocalTransaction


def actor(user_id, permissions=(), admin=False):
    return SimpleNamespace(
        user=SimpleNamespace(user_id=user_id, nick_name='测试组织', user_name='test', admin=admin),
        permissions=list(permissions),
        roles=['admin'] if admin else ['user'],
    )


@pytest.fixture
def rows():
    engine = create_engine('sqlite+pysqlite:///:memory:')
    models = [
        SysUser,
        GuildMember,
        GuildProfession,
        GuildBattle,
        GuildBattleRecord,
        Organization,
        OrganizationMember,
        Activity,
        ActivitySnapshot,
        Participation,
        MutationReceipt,
        ReportLink,
        ActivityLeaveLink,
        ActivityLeaveRecord,
    ]
    Organization.metadata.create_all(engine, tables=[m.__table__ for m in models])
    session = Session(engine, expire_on_commit=False)
    session.add_all(
        [
            SysUser(user_id=101, user_name='owner', nick_name='九肆', status='0', del_flag='0'),
            SysUser(user_id=23, user_name='member', nick_name='成员', status='0', del_flag='0'),
            SysUser(user_id=24, user_name='outsider', nick_name='外部', status='0', del_flag='0'),
            GuildProfession(profession_id=1, profession_name='铁衣', status='0'),
            GuildProfession(profession_id=2, profession_name='素问', status='0'),
            GuildMember(
                member_id=9,
                user_id=101,
                guild_id=101,
                member_user_id=23,
                player_name='玩家甲',
                player_class='铁衣',
                is_active='1',
                role_in_guild='成员',
            ),
            GuildMember(
                member_id=10,
                user_id=202,
                guild_id=202,
                member_user_id=24,
                player_name='玩家乙',
                player_class='素问',
                is_active='1',
                role_in_guild='成员',
            ),
            Organization(org_id='guild-101', org_type='guild', name='九肆', owner_user_id=101, source_owner_id=101),
        ]
    )
    session.commit()
    yield SimpleNamespace(
        session=session,
        db=LocalTransaction(session),
        owner=actor(101, ['guild:schedule:list'], admin=True),
        member=actor(23),
        outsider=actor(24),
    )
    session.close()
    engine.dispose()


async def create(rows, org='guild-101'):
    return await ActivityService.create(
        rows.db,
        rows.owner,
        CreateActivity(
            orgId=org,
            name='周末约战',
            startsAt=datetime.now() + timedelta(days=1),
            endsAt=datetime.now() + timedelta(days=1, hours=2),
        ),
    )


def lineup(player=None, required='铁衣'):
    return [
        {
            'id': 't1',
            'name': '进攻一团',
            'squads': [
                {
                    'id': 's1',
                    'name': '一队',
                    'seats': [
                        {
                            'position': i,
                            'requiredProfession': required if i == 1 else '',
                            'player': player if i == 1 else None,
                        }
                        for i in range(1, 7)
                    ],
                }
            ],
        }
    ]


async def save(rows, activity, teams=None, revision=0, key='save-one'):
    return await ActivityService.save(
        rows.db,
        rows.owner,
        activity['activityId'],
        SaveLineup(expectedRevision=revision, operationKey=key, teams=teams or lineup()),
    )


@pytest.mark.asyncio
async def test_private_access_and_read_does_not_create_data(rows):
    a = await create(rows)
    assert (await ActivityService.detail(rows.db, rows.member, a['activityId']))['snapshot'] is None
    with pytest.raises(ApiProblem) as e:
        await ActivityService.detail(rows.db, rows.outsider, a['activityId'])
    assert e.value.status == 404
    assert rows.session.scalar(select(ActivitySnapshot)) is None
    with pytest.raises(ApiProblem) as e:
        await ActivityService.save(
            rows.db, rows.member, a['activityId'], SaveLineup(expectedRevision=0, operationKey='deny', teams=lineup())
        )
    assert e.value.status == 403


@pytest.mark.asyncio
async def test_atomic_save_idempotency_conflict_and_immutable_versions(rows):
    a = await create(rows)
    first = await save(rows, a)
    assert first['revision'] == 1
    assert (await save(rows, a))['snapshotId'] == first['snapshotId']
    with pytest.raises(ApiProblem) as e:
        await save(rows, a, revision=0, key='stale')
    assert e.value.status == 409
    await save(rows, a, revision=1, key='second')
    snapshots = rows.session.scalars(select(ActivitySnapshot).order_by(ActivitySnapshot.version)).all()
    assert [s.version for s in snapshots] == [1, 2]
    assert (await ActivityService.detail(rows.db, rows.member, a['activityId']))['revision'] == 2


@pytest.mark.asyncio
async def test_database_failure_keeps_last_successful_snapshot(rows):
    a = await create(rows)
    first = await save(rows, a)

    def reject(session, *_):
        if any(isinstance(o, ActivitySnapshot) and o.version == 2 for o in session.new):
            raise RuntimeError('failed snapshot')

    event.listen(rows.session, 'before_flush', reject)
    try:
        with pytest.raises(RuntimeError):
            await save(rows, a, revision=1, key='failure')
    finally:
        event.remove(rows.session, 'before_flush', reject)
    detail = await ActivityService.detail(rows.db, rows.member, a['activityId'])
    assert detail['revision'] == 1 and detail['snapshot']['snapshotId'] == first['snapshotId']


@pytest.mark.asyncio
async def test_snapshot_validates_profession_scope_and_temporary_member(rows):
    a = await create(rows)
    with pytest.raises(ApiProblem):
        await save(rows, a, lineup({'memberId': '10'}, '素问'))
    with pytest.raises(ApiProblem):
        await save(rows, a, lineup({'memberId': '9'}, '素问'))
    with pytest.raises(ApiProblem):
        await save(rows, a, lineup({'memberId': '9', 'profession': '素问'}, '素问'))
    temp = {'temporaryId': 'temp_1', 'name': '临时替补', 'profession': '铁衣'}
    result = await save(rows, a, lineup(temp))
    assert result['revision'] == 1
    assert len(rows.session.scalars(select(GuildMember)).all()) == 2
    assert (await ActivityService.detail(rows.db, rows.member, a['activityId']))['snapshot']['teams'][0]['squads'][0][
        'seats'
    ][0]['player']['isTemporary']


@pytest.mark.asyncio
async def test_combined_position_notes_are_saved_in_snapshot(rows):
    activity = await create(rows)
    teams = lineup()
    teams[0]['squads'][0]['seats'][0]['notes'] = ['指挥', '保镖']
    await save(rows, activity, teams)
    detail = await ActivityService.detail(rows.db, rows.member, activity['activityId'])
    assert detail['snapshot']['teams'][0]['squads'][0]['seats'][0]['notes'] == ['指挥', '保镖']


@pytest.mark.asyncio
async def test_manager_can_reuse_latest_and_historical_saved_lineups_for_same_organization(rows):
    first_activity = await create(rows)
    await save(rows, first_activity, lineup({'memberId': '9'}))
    await save(rows, first_activity, lineup(), revision=1, key='historical-two')
    second_activity = await create(rows)

    templates = await ActivityService.lineup_templates(rows.db, rows.owner, 'guild-101')
    assert [item['version'] for item in templates[:2]] == [2, 1]
    assert templates[0]['activityId'] == first_activity['activityId']
    assert templates[0]['teams'][0]['name'] == '进攻一团'
    assert all(item['activityId'] != second_activity['activityId'] for item in templates)

    with pytest.raises(ApiProblem) as denied:
        await ActivityService.lineup_templates(rows.db, rows.member, 'guild-101')
    assert denied.value.status == 403


@pytest.mark.asyncio
async def test_publication_keeps_mine_and_outside_signup_checks_profile_and_profession(rows):
    a = await create(rows)
    await save(rows, a)
    assert (await ActivityService.list(rows.db, rows.outsider, 'public'))['total'] == 0
    await ActivityService.change(
        rows.db, rows.owner, a['activityId'], 'publish', ChangeActivity(expectedRevision=1, operationKey='publish')
    )
    assert (await ActivityService.list(rows.db, rows.member, 'mine'))['total'] == 1
    assert (await ActivityService.list(rows.db, rows.outsider, 'public'))['total'] == 1
    with pytest.raises(ApiProblem):
        await ActivityService.signup(
            rows.db,
            rows.outsider,
            a['activityId'],
            SignupSeat(expectedRevision=2, operationKey='wrong', memberId='10', squadId='s1', position=1),
        )
    with pytest.raises(ApiProblem):
        await ActivityService.signup(
            rows.db,
            rows.outsider,
            a['activityId'],
            SignupSeat(expectedRevision=2, operationKey='impersonate', memberId='9', squadId='s1', position=2),
        )
    await ActivityService.signup(
        rows.db,
        rows.outsider,
        a['activityId'],
        SignupSeat(expectedRevision=2, operationKey='join', memberId='10', squadId='s1', position=2),
    )
    d = await ActivityService.detail(rows.db, rows.outsider, a['activityId'])
    assert d['snapshot']['teams'][0]['squads'][0]['seats'][1]['player']['name'] == '玩家乙'
    await ActivityService.leave(
        rows.db, rows.outsider, a['activityId'], LeaveSeat(expectedRevision=3, operationKey='leave', memberId='10')
    )
    assert (await ActivityService.detail(rows.db, rows.outsider, a['activityId']))['snapshot']['teams'][0]['squads'][0][
        'seats'
    ][1]['player'] is None


@pytest.mark.asyncio
async def test_club_membership_and_history_without_csv(rows):
    org = await ActivityService.create_organization(rows.db, rows.owner, 'club', '测试俱乐部')
    await ActivityService.grant_member(rows.db, rows.owner, org['orgId'], '9', 'assistant')
    a = await create(rows, org['orgId'])
    await save(rows, a)
    assistant = await ActivityService.save(
        rows.db,
        rows.member,
        a['activityId'],
        SaveLineup(expectedRevision=1, operationKey='assistant', teams=lineup({'memberId': '9'})),
    )
    assert assistant['revision'] == 2
    await ActivityService.change(
        rows.db, rows.owner, a['activityId'], 'end', ChangeActivity(expectedRevision=2, operationKey='end')
    )
    h = await ActivityService.list(rows.db, rows.member, 'history')
    assert h['total'] == 1 and h['items'][0]['hasReport'] is False
    with pytest.raises(ApiProblem):
        await save(rows, a, revision=3, key='ended')


@pytest.mark.asyncio
async def test_activity_time_expiry_moves_to_history_and_freezes_lineup_without_manual_end(rows):
    activity = await create(rows)
    await save(rows, activity, lineup({'memberId': '9'}))
    stored = rows.session.get(Activity, activity['activityId'])
    stored.starts_at = datetime.now() - timedelta(hours=3)
    stored.ends_at = datetime.now() - timedelta(hours=1)
    rows.session.commit()

    assert (await ActivityService.list(rows.db, rows.member, 'mine'))['total'] == 0
    assert (await ActivityService.list(rows.db, rows.member, 'mine', participating_only=True))['total'] == 0
    history = await ActivityService.list(rows.db, rows.member, 'history')
    assert history['total'] == 1
    assert history['items'][0]['activityId'] == activity['activityId']
    assert history['items'][0]['state'] == 'ended'
    assert (await ActivityService.detail(rows.db, rows.member, activity['activityId']))['state'] == 'ended'

    with pytest.raises(ApiProblem) as error:
        await save(rows, activity, revision=1, key='expired-lineup')
    assert error.value.key == 'ACTIVITY_ENDED'


@pytest.mark.asyncio
async def test_only_super_admin_can_create_club(rows):
    manager = actor(23, ['guild:schedule:list'])
    with pytest.raises(ApiProblem) as error:
        await ActivityService.create_organization(rows.db, manager, 'club', '普通管理员俱乐部')
    assert error.value.status == 403
    assert error.value.key == 'SUPER_ADMIN_REQUIRED'


@pytest.mark.asyncio
async def test_personal_mine_can_filter_to_activities_the_account_participates_in(rows):
    activity = await create(rows)
    assert (await ActivityService.list(rows.db, rows.member, 'mine', participating_only=True))['total'] == 0
    await save(rows, activity, lineup({'memberId': '9'}))
    result = await ActivityService.list(rows.db, rows.member, 'mine', participating_only=True)
    assert result['total'] == 1
    assert result['items'][0]['activityId'] == activity['activityId']


@pytest.mark.asyncio
async def test_guild_activity_automatically_creates_a_leave_link(rows):
    activity = await create(rows)
    assert activity['leaveCode']
    assert activity['leavePath'] == f"/public/activity-leave/{activity['leaveCode']}"


@pytest.mark.asyncio
async def test_leave_link_searches_guild_members_and_leave_removes_an_arranged_player(rows):
    activity = await create(rows)
    await save(rows, activity, lineup({'memberId': '9'}))

    members = await ActivityService.leave_members_by_code(rows.db, activity['leaveCode'], '玩家')
    assert [(item['memberId'], item['name']) for item in members] == [('9', '玩家甲')]

    result = await ActivityService.leave_by_code(
        rows.db,
        activity['leaveCode'],
        member_id='9',
        remark='临时有事',
    )
    assert result['name'] == '玩家甲'
    assert result['remark'] == '临时有事'
    detail = await ActivityService.detail(rows.db, rows.owner, activity['activityId'])
    assert detail['snapshot']['teams'][0]['squads'][0]['seats'][0]['player'] is None
    assert detail['revision'] == 2

    leaves = await ActivityService.activity_leaves(rows.db, rows.owner, activity['activityId'])
    assert len(leaves) == 1
    assert leaves[0]['name'] == '玩家甲'
    assert leaves[0]['leftAt']


@pytest.mark.asyncio
async def test_leave_member_is_excluded_from_activity_candidates_even_without_an_account(rows):
    rows.session.get(GuildMember, 9).member_user_id = 0
    rows.session.commit()
    activity = await create(rows)
    await ActivityService.leave_by_code(rows.db, activity['leaveCode'], member_id='9', remark='')
    candidates = await ActivityService.profiles(rows.db, rows.owner, 'guild-101', activity['activityId'])
    assert all(item['memberId'] != '9' for item in candidates)


@pytest.mark.asyncio
async def test_http_contract_requires_jwt_and_same_snapshot_for_two_clients(auth_state, rows):
    import httpx
    from fastapi import FastAPI
    from config.get_db import get_db
    from module_integration.controller.activity_controller import activity_controller

    a = await create(rows)
    await save(rows, a)
    app = FastAPI()
    app.state.redis = auth_state.redis
    app.include_router(activity_controller)

    async def db():
        yield rows.db

    app.dependency_overrides[get_db] = db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
        url = '/api/v1/activities/' + a['activityId']
        assert (await client.get(url)).status_code == 401
        web = await client.get(url, headers={'Authorization': 'Bearer ' + auth_state.token()})
        mini = await client.get(url, headers={'Authorization': 'Bearer ' + auth_state.token()})
        assert web.status_code == 200 and web.json()['data'] == mini.json()['data']
        assert web.json()['data']['activityId'] == a['activityId']


@pytest.mark.asyncio
async def test_idempotency_key_cannot_be_reused_for_different_payload(rows):
    a = await create(rows)
    await save(rows, a)
    with pytest.raises(ApiProblem) as e:
        await save(rows, a, lineup(required='素问'))
    assert e.value.key == 'IDEMPOTENCY_CONFLICT'
    assert len(rows.session.scalars(select(ActivitySnapshot)).all()) == 1


@pytest.mark.asyncio
async def test_assistant_is_scoped_and_platform_admin_cannot_override_other_org(rows):
    a = await create(rows)
    rows.session.get(GuildMember, 9).role_in_guild = '助手'
    rows.session.commit()
    await ActivityService.save(
        rows.db,
        rows.member,
        a['activityId'],
        SaveLineup(expectedRevision=0, operationKey='assistant-guild', teams=lineup()),
    )
    other = actor(24, ['*:*:*'])
    with pytest.raises(ApiProblem) as e:
        await ActivityService.save(
            rows.db, other, a['activityId'], SaveLineup(expectedRevision=1, operationKey='cross-org', teams=lineup())
        )
    assert e.value.status == 403


@pytest.mark.asyncio
async def test_ended_lineup_freezes_public_signup_and_old_bound_participants_keep_history(rows):
    a = await create(rows)
    await save(rows, a, lineup({'memberId': '9'}))
    await ActivityService.change(
        rows.db, rows.owner, a['activityId'], 'publish', ChangeActivity(expectedRevision=1, operationKey='pub')
    )
    await ActivityService.change(
        rows.db, rows.owner, a['activityId'], 'end', ChangeActivity(expectedRevision=2, operationKey='finish')
    )
    rows.session.get(GuildMember, 9).is_active = '0'
    rows.session.commit()
    assert (await ActivityService.list(rows.db, rows.member, 'history'))['total'] == 1
    assert (await ActivityService.detail(rows.db, rows.member, a['activityId']))['snapshot']['teams'][0]['squads'][0][
        'seats'
    ][0]['player']['name'] == '玩家甲'
    with pytest.raises(ApiProblem):
        await ActivityService.signup(
            rows.db,
            rows.outsider,
            a['activityId'],
            SignupSeat(expectedRevision=3, operationKey='after-end', memberId='10', squadId='s1', position=2),
        )


@pytest.mark.asyncio
async def test_explicit_report_link_hides_private_file_and_rejects_nonparticipant(rows):
    a = await create(rows)
    await save(rows, a)
    await ActivityService.change(
        rows.db, rows.owner, a['activityId'], 'publish', ChangeActivity(expectedRevision=1, operationKey='pub')
    )
    rows.session.add(
        GuildBattle(
            battle_id=77,
            battle_name='旧 CSV',
            battle_date='2026-09-14',
            user_id=101,
            del_flag='0',
            csv_file_url='secret-path',
        )
    )
    rows.session.add(
        GuildBattleRecord(
            record_id=88, battle_id=77, player_name='玩家甲', player_class='铁衣', dmg_to_players=9007199254740993
        )
    )
    rows.session.commit()
    await ActivityService.link_report(
        rows.db, rows.owner, a['activityId'], LinkReport(expectedRevision=2, operationKey='link', battleId='77')
    )
    with pytest.raises(ApiProblem) as e:
        await ActivityService.report(rows.db, rows.outsider, '77')
    assert e.value.status == 404
    report = await ActivityService.report(rows.db, rows.member, '77')
    assert report['players'][0]['metrics']['dmg_to_players'] == '9007199254740993'
    assert 'secret-path' not in str(report)


@pytest.mark.asyncio
async def test_report_list_and_detail_never_expose_unlinked_legacy_reports(rows):
    activity = await create(rows)
    await save(rows, activity)
    await ActivityService.change(
        rows.db,
        rows.owner,
        activity['activityId'],
        'end',
        ChangeActivity(expectedRevision=1, operationKey='finish-for-reports'),
    )
    rows.session.add_all(
        [
            GuildBattle(battle_id=71, battle_name='已关联战报', battle_date='2026-09-15', user_id=101, del_flag='0'),
            GuildBattle(battle_id=72, battle_name='旧未关联战报', battle_date='2026-09-14', user_id=101, del_flag='0'),
            ReportLink(battle_id=71, activity_id=activity['activityId'], linked_by=101),
        ]
    )
    rows.session.commit()

    reports = await ActivityService.reports(rows.db, rows.owner)
    assert [item['reportId'] for item in reports['items']] == ['71']
    assert reports['items'][0]['association'] == '已关联活动'
    with pytest.raises(ApiProblem) as error:
        await ActivityService.report(rows.db, rows.owner, '72')
    assert error.value.status == 404


@pytest.mark.asyncio
async def test_manager_imports_csv_records_directly_into_activity(rows):
    a = await create(rows)
    payload = ImportActivityReport(
        expectedRevision=0,
        operationKey='import-csv-one',
        fileName='20260915_九肆_扶摇.csv',
        battleDate='2026-09-15',
        battleResult='胜利',
        opponentName='扶摇',
        records=[
            {
                'guild_name': '九肆',
                'player_name': '玩家甲',
                'player_class': '铁衣',
                'kills': 7,
                'qingquan_kills': 2,
                'assists': 19,
                'dmg_to_players': 9007199254740993,
            }
        ],
    )

    result = await ActivityService.import_report(rows.db, rows.owner, a['activityId'], payload)
    assert result['activityId'] == a['activityId']
    assert result['revision'] == 1
    assert result['importedPlayers'] == 1
    assert result['reportId'].isdecimal()
    assert rows.session.scalar(select(ReportLink)).activity_id == a['activityId']
    record = rows.session.scalar(select(GuildBattleRecord))
    assert record.player_name == '玩家甲'
    assert record.dmg_to_players == 9007199254740993
    detail = await ActivityService.detail(rows.db, rows.member, a['activityId'])
    assert detail['hasReport'] is True and result['reportId'] in detail['reportIds']


@pytest.mark.asyncio
async def test_activity_csv_import_is_manager_only_and_atomic(rows):
    a = await create(rows)
    payload = ImportActivityReport(
        expectedRevision=0,
        operationKey='import-csv-denied',
        fileName='battle.csv',
        battleDate='2026-09-15',
        records=[{'guild_name': '九肆', 'player_name': '玩家甲', 'player_class': '铁衣'}],
    )
    with pytest.raises(ApiProblem) as denied:
        await ActivityService.import_report(rows.db, rows.member, a['activityId'], payload)
    assert denied.value.status == 403
    assert rows.session.scalar(select(GuildBattle)) is None

    def reject_link(session, *_):
        if any(isinstance(item, ReportLink) for item in session.new):
            raise RuntimeError('link failed')

    event.listen(rows.session, 'before_flush', reject_link)
    try:
        with pytest.raises(RuntimeError):
            await ActivityService.import_report(rows.db, rows.owner, a['activityId'], payload)
    finally:
        event.remove(rows.session, 'before_flush', reject_link)
    assert rows.session.scalar(select(GuildBattle)) is None
    assert rows.session.scalar(select(GuildBattleRecord)) is None
    assert rows.session.scalar(select(ReportLink)) is None
    assert (await ActivityService.detail(rows.db, rows.owner, a['activityId']))['revision'] == 0


@pytest.mark.asyncio
async def test_two_sessions_compare_and_swap_prevents_stale_save(rows):
    a = await create(rows)
    await save(rows, a)
    other_session = Session(rows.session.get_bind(), expire_on_commit=False)
    try:
        db = LocalTransaction(other_session)
        await ActivityService.save(
            db,
            rows.owner,
            a['activityId'],
            SaveLineup(expectedRevision=1, operationKey='another-window', teams=lineup()),
        )
        with pytest.raises(ApiProblem) as e:
            await save(rows, a, revision=1, key='old-window')
        assert e.value.key == 'REVISION_CONFLICT'
        assert (await ActivityService.detail(rows.db, rows.member, a['activityId']))['revision'] == 2
    finally:
        other_session.close()


@pytest.mark.asyncio
async def test_disabled_feature_does_not_touch_database(auth_state, monkeypatch):
    import httpx
    from fastapi import FastAPI
    from module_integration.controller.activity_controller import activity_controller

    monkeypatch.setenv('NSH_ACTIVITIES_ENABLED', 'false')
    app = FastAPI()
    app.include_router(activity_controller)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
        response = await client.get('/api/v1/activities')
        assert response.status_code == 503 and response.json()['errorKey'] == 'CAPABILITY_DISABLED'


@pytest.mark.parametrize('positions', [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6, 6], [1, 1, 3, 4, 5, 6]])
def test_exactly_six_unique_positions(positions):
    from pydantic import ValidationError

    teams = lineup()
    teams[0]['squads'][0]['seats'] = [{'position': i} for i in positions]
    with pytest.raises(ValidationError):
        SaveLineup(expectedRevision=0, operationKey='bad', teams=teams)


@pytest.mark.asyncio
async def test_organization_category_is_filtered_before_pagination(rows):
    await create(rows)
    club = await ActivityService.create_organization(rows.db, rows.owner, 'club', '俱乐部')
    await create(rows, club['orgId'])
    result = await ActivityService.list(rows.db, rows.owner, 'mine', page_size=1, org_type='club')
    assert result['total'] == 1 and result['items'][0]['orgType'] == 'club'


@pytest.mark.asyncio
async def test_admin_save_cannot_silently_ignore_removal_of_public_signup(rows):
    a = await create(rows)
    await save(rows, a)
    await ActivityService.change(
        rows.db, rows.owner, a['activityId'], 'publish', ChangeActivity(expectedRevision=1, operationKey='pub')
    )
    await ActivityService.signup(
        rows.db,
        rows.outsider,
        a['activityId'],
        SignupSeat(expectedRevision=2, operationKey='join', memberId='10', squadId='s1', position=2),
    )
    with pytest.raises(ApiProblem) as e:
        await save(rows, a, revision=3, key='remove-active')
    assert e.value.key == 'SIGNUP_CONFLICT'
    assert (await ActivityService.detail(rows.db, rows.outsider, a['activityId']))['revision'] == 3


def emulate_async_expiration(rows):
    rows.session.expire_on_commit = True
    @event.listens_for(rows.session, 'do_orm_execute')
    def reject_implicit_reload(state):
        if state.is_column_load:
            raise MissingGreenlet('Async attributes cannot implicitly reload after commit')


@pytest.mark.asyncio
async def test_create_organization_returns_dto_without_post_commit_implicit_io(rows):
    emulate_async_expiration(rows)
    result = await ActivityService.create_organization(rows.db, rows.owner, 'club', '真实异步提交回归')
    assert result['name'] == '真实异步提交回归'


@pytest.mark.asyncio
async def test_create_activity_returns_detail_without_expired_id_access(rows):
    emulate_async_expiration(rows)
    result = await create(rows)
    assert result['name'] == '周末约战'
    assert result['revision'] == 0


@pytest.mark.asyncio
async def test_club_grant_returns_id_without_expired_member_access(rows):
    club = await ActivityService.create_organization(rows.db, rows.owner, 'club', '俱乐部')
    emulate_async_expiration(rows)
    result = await ActivityService.grant_member(rows.db, rows.owner, club['orgId'], '9', 'member')
    assert result['memberId'] == '9'


@pytest.mark.asyncio
async def test_activity_leave_returns_dto_without_post_commit_implicit_io(rows):
    activity = await create(rows)
    emulate_async_expiration(rows)
    result = await ActivityService.leave_by_code(
        rows.db,
        activity['leaveCode'],
        member_id='9',
        remark='临时有事',
    )
    assert result['activityId'] == activity['activityId']
    assert result['memberId'] == '9'
    assert result['name'] == '玩家甲'
    assert result['remark'] == '临时有事'
    assert result['revision'] == 1

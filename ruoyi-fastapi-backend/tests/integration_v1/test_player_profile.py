import pytest
from pydantic import ValidationError
from sqlalchemy import select, event
from module_guild.entity.do.member_do import GuildMember
from module_integration.contract import ApiProblem
from module_integration.player_profile import AccountPlayerProfile, PlayerProfileInput, PlayerProfileService
from .test_activities import rows, actor, create, save, lineup, emulate_async_expiration


def form(**changes):
    return PlayerProfileInput(**dict(dict(name='新名字', playerUid='000123', wechatId='wx-private', hasOrangeWeapon=True,
                                         profession='素问', secondaryProfession='铁衣', remark='备注'), **changes))


@pytest.fixture
def profiles(rows):
    AccountPlayerProfile.__table__.create(rows.session.get_bind())
    return rows


@pytest.mark.parametrize('change', [dict(name=' '), dict(name='长'*31), dict(playerUid=123), dict(playerUid='0'*65),
    dict(wechatId='x'*65), dict(remark='x'*501), dict(hasOrangeWeapon='true'), dict(accountId='24')])
def test_strict_profile_input(change):
    with pytest.raises(ValidationError):
        form(**change)


@pytest.mark.asyncio
async def test_unjoined_account_can_read_without_write_and_save_string_uid(profiles):
    r=profiles
    result=await PlayerProfileService.get(r.db, actor(777))
    assert result['name']=='' and result['hasOrangeWeapon'] is False
    assert r.session.scalar(select(AccountPlayerProfile)) is None
    result=await PlayerProfileService.save(r.db, actor(777), form())
    assert result['playerUid']=='000123' and result['hasOrangeWeapon'] is True
    assert (await PlayerProfileService.get(r.db, actor(777)))==result
    assert len(r.session.scalars(select(GuildMember)).all())==2


@pytest.mark.asyncio
async def test_prefill_sync_all_bound_records_but_keep_snapshot(profiles):
    r=profiles
    queries=[]
    def capture(_conn,_cursor,statement,*_):queries.append(statement)
    event.listen(r.session.get_bind(),'before_cursor_execute',capture)
    try:before=await PlayerProfileService.get(r.db,r.member)
    finally:event.remove(r.session.get_bind(),'before_cursor_execute',capture)
    assert any('guild_member' in q and 'LIMIT' in q for q in queries), 'latest member lookup must fetch one row only'
    assert before['name']=='玩家甲' and before['wechatId']==''
    r.session.add(GuildMember(member_id=12,user_id=202,guild_id=202,member_user_id=23,player_name='最新绑定',player_class='铁衣',is_active='1'))
    r.session.commit()
    assert (await PlayerProfileService.get(r.db,r.member))['name']=='最新绑定'
    a=await create(r)
    await save(r,a,lineup({'memberId':'9'}))
    await PlayerProfileService.save(r.db,r.member,form())
    for m in r.session.scalars(select(GuildMember).where(GuildMember.member_user_id==23)):
        assert m.player_name=='新名字' and m.player_class=='素问' and m.remark=='备注'
    from module_integration.activities.service import ActivityService
    d=await ActivityService.detail(r.db,r.member,a['activityId'])
    assert d['snapshot']['teams'][0]['squads'][0]['seats'][0]['player']['name']=='玩家甲'
    with pytest.raises(ApiProblem):
        await save(r,a,lineup({'memberId':'9'}),revision=1,key='new-invalid-profession')


@pytest.mark.asyncio
async def test_save_rolls_back_member_and_profile_together(profiles):
    r=profiles
    def reject(session,*_):
        if any(isinstance(x,AccountPlayerProfile) for x in session.new):
            raise RuntimeError('fail profile')
    event.listen(r.session,'before_flush',reject)
    try:
        with pytest.raises(RuntimeError):
            await PlayerProfileService.save(r.db,r.member,form())
    finally:
        event.remove(r.session,'before_flush',reject)
    assert r.session.get(GuildMember,9).player_name=='玩家甲'
    assert r.session.scalar(select(AccountPlayerProfile)) is None


@pytest.mark.asyncio
async def test_wechat_requires_real_same_guild_manager(profiles):
    r=profiles
    await PlayerProfileService.save(r.db,r.member,form())
    assert (await PlayerProfileService.managed_get(r.db,r.owner,'guild-101','23'))['wechatId']=='wx-private'
    for viewer in [r.member,actor(24,['*:*:*']),actor(888,['guild:member:list'])]:
        with pytest.raises(ApiProblem):
            await PlayerProfileService.managed_get(r.db,viewer,'guild-101','23')
    with pytest.raises(ApiProblem):
        await PlayerProfileService.managed_get(r.db,r.owner,'guild-101','24')
    from module_integration.activities.service import ActivityService
    club=await ActivityService.create_organization(r.db,r.owner,'club','俱乐部')
    with pytest.raises(ApiProblem):
        await PlayerProfileService.managed_get(r.db,r.owner,club['orgId'],'23')
    assert 'wx-private' not in str(await ActivityService.profiles(r.db,r.owner,'guild-101'))


@pytest.mark.asyncio
async def test_candidate_identity_metadata_is_scoped_and_not_written_into_snapshot(profiles):
    from module_integration.activities.service import ActivityService
    r=profiles
    candidates=await ActivityService.profiles(r.db,r.owner,'guild-101')
    assert candidates[0]['accountId']=='23'
    with pytest.raises(ApiProblem):await ActivityService.profiles(r.db,r.outsider,'guild-101')
    a=await create(r);await save(r,a,lineup({'memberId':'9'}))
    assert 'accountId' not in str((await ActivityService.detail(r.db,r.member,a['activityId']))['snapshot'])


@pytest.mark.asyncio
async def test_save_avoids_post_commit_expired_attribute_io(profiles):
    emulate_async_expiration(profiles)
    assert (await PlayerProfileService.save(profiles.db,profiles.member,form()))['playerUid']=='000123'


@pytest.mark.asyncio
async def test_existing_profile_commit_failure_restores_all_fields(profiles):
    r=profiles
    old=await PlayerProfileService.save(r.db,r.member,form())
    def reject(*_):raise RuntimeError('commit failure')
    event.listen(r.session,'before_commit',reject)
    try:
        with pytest.raises(RuntimeError):
            await PlayerProfileService.save(r.db,r.member,form(name='不能写入',wechatId='never-commit'))
    finally:
        event.remove(r.session,'before_commit',reject)
    assert await PlayerProfileService.get(r.db,r.member)==old
    assert r.session.get(GuildMember,9).player_name==old['name']


def test_wechat_is_masked_in_log_payload(monkeypatch):
    from config.env import LogConfig
    monkeypatch.setattr(LogConfig,'log_mask_enabled',True)
    from utils.log_util import LogSanitizer
    assert 'wx-private' not in str(LogSanitizer.sanitize_data({'wechatId':'wx-private','wechat_id':'wx-private'}))
    assert 'wx-private' not in LogSanitizer.sanitize_text('wechatId="wx-private"')


def test_style_read_preserves_explicit_white_custom_color():
    from types import SimpleNamespace
    from module_guild.service.class_color_service import ClassColorService
    saved={'九灵':SimpleNamespace(bg_color='#FFFFFF',text_color='#000000')}
    assert ClassColorService._resolve_color('九灵',saved,preserve_saved=True)==dict(class_name='九灵',bg_color='#FFFFFF',text_color='#000000')


@pytest.mark.parametrize('target',['ruoyi','nsh_activity_dev_20260913','',None])
def test_profile_migration_cannot_target_other_databases(target):
    import importlib.util
    from pathlib import Path
    file=Path(__file__).resolve().parents[2]/'tools/migrate_player_profile_dev.py'
    spec=importlib.util.spec_from_file_location('profile_migration',file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with pytest.raises(ValueError):module.migrate(target)


@pytest.mark.asyncio
async def test_http_me_profile_and_styles_are_authenticated_not_management_permission(auth_state,profiles,monkeypatch):
    import httpx
    from fastapi import FastAPI
    from config.get_db import get_db
    from module_integration.controller.player_profile_controller import player_profile_controller
    from module_guild.service.class_color_service import ClassColorService
    async def styles(db,current_user,**kwargs):
        assert current_user.user.user_id==23
        return [dict(class_name='铁衣',bg_color='#123456',text_color='#ffffff')]
    monkeypatch.setattr(ClassColorService,'get_colors_service',styles)
    app=FastAPI();app.state.redis=auth_state.redis;app.include_router(player_profile_controller)
    async def db():yield profiles.db
    app.dependency_overrides[get_db]=db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://isolated') as c:
        assert (await c.get('/api/v1/player-profile/me')).status_code==401
        headers={'Authorization':'Bearer '+auth_state.token()}
        result=await c.put('/api/v1/player-profile/me',headers=headers,json=form().model_dump(by_alias=True))
        assert result.status_code==200 and result.json()['data']['playerUid']=='000123'
        assert (await c.get('/api/v1/player-profile/me',headers=headers)).json()['data']==result.json()['data']
        style=(await c.get('/api/v1/profession-styles',headers=headers)).json()['data'][0]
        assert style==dict(profession='铁衣',backgroundColor='#123456',textColor='#ffffff')

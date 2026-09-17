"""Local fixture accounts and real-API smoke checks, exclusively in the new dev DB."""
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path
import os
import sys
import uuid
import bcrypt
import httpx
import pymysql
import redis
from dotenv import dotenv_values
from local_activity_dev import BACKEND, TARGET, validate_target

BASE = 'http://127.0.0.1:9101'
NAMES = {'manager': 'nsh_demo_manager', 'assistant': 'nsh_demo_assistant',
         'member': 'nsh_demo_member', 'guest': 'nsh_demo_guest'}
PROFESSIONS = ['铁衣', '素问', '血河', '神相', '九灵', '碎梦', '龙吟', '玄机', '潮光']


def demo_password():
    value = os.environ.get('NSH_DEMO_PASSWORD', '')
    if len(value) < 12:
        raise RuntimeError('Set NSH_DEMO_PASSWORD to a local-only password of at least 12 characters')
    return value


def api(client, method, path, data=None):
    response = client.request(method, '/api/v1' + path, json=data)
    body = response.json()
    if response.status_code != 200 or not body.get('success'):
        raise RuntimeError(f'{method} {path}: HTTP {response.status_code}, {body.get("errorKey")}, {body.get("msg")}')
    return body['data']


def open_login(kind, legacy=False):
    c = dotenv_values(BACKEND / '.env.dev')
    cache = redis.Redis(host=c['REDIS_HOST'], port=int(c['REDIS_PORT']),
                        password=c.get('REDIS_PASSWORD') or None, db=15)
    client = httpx.Client(base_url=BASE, timeout=20, trust_env=False)
    captcha = api(client, 'GET', '/auth/captcha')
    code = cache.get('captcha_codes:' + captcha.get('uuid', '')) if captcha.get('captchaEnabled') else b''
    data = {'userName': NAMES[kind], 'password': demo_password(),
            'code': code.decode() if code else '', 'uuid': captcha.get('uuid', '')}
    if legacy:
        response = client.post('/login', data={'username':data['userName'], **{k:v for k,v in data.items() if k!='userName'}})
        response.raise_for_status()
        token = response.json()['token']
    else:
        token = api(client, 'POST', '/auth/login', data)['accessToken']
    client.headers['Authorization'] = 'Bearer ' + token
    return client


@contextmanager
def login(kind, legacy=False):
    client = open_login(kind, legacy)
    try:
        yield client
    finally:
        client.close()


def install_fixtures():
    validate_target(TARGET)
    c = dotenv_values(BACKEND / '.env.dev')
    ids = {}
    with pymysql.connect(host=c['DB_HOST'], port=int(c['DB_PORT']), user=c['DB_USERNAME'],
                         password=c['DB_PASSWORD'], database=TARGET, charset='utf8mb4') as connection:
        with connection.cursor() as q:
            q.execute('SELECT COUNT(*) FROM sys_menu WHERE menu_id BETWEEN 47000 AND 47007')
            if q.fetchone()[0] == 0:
                sql = (BACKEND / 'sql/20260914_activity_information_menus.sql').read_text(encoding='utf-8')
                sql = '\n'.join(x for x in sql.splitlines() if not x.lstrip().startswith('--'))
                for statement in sql.split(';'):
                    if statement.strip():
                        q.execute(statement)
            for kind, name in NAMES.items():
                q.execute('SELECT user_id,create_by FROM sys_user WHERE user_name=%s', (name,))
                existing = q.fetchone()
                if existing:
                    if existing[1] != 'activity-dev':
                        raise ValueError('Existing non-fixture account cannot be changed')
                    ids[kind] = existing[0]
                    continue
                hashed = bcrypt.hashpw(demo_password().encode(), bcrypt.gensalt()).decode()
                q.execute("INSERT INTO sys_user(user_name,nick_name,password,status,del_flag,create_by,create_time,pwd_update_date) VALUES(%s,%s,%s,'0','0','activity-dev',NOW(),NOW())",
                          (name, {'manager':'演示帮会管理员','assistant':'演示助手','member':'演示帮会成员','guest':'演示外部玩家'}[kind], hashed))
                ids[kind] = q.lastrowid
                q.execute('INSERT INTO sys_user_role(user_id,role_id) VALUES(%s,%s)', (ids[kind], 2 if kind=='manager' else 100))
            q.execute("SELECT COUNT(*) FROM guild_member WHERE user_id=%s AND source_type='activity-demo'", (ids['manager'],))
            if q.fetchone()[0] == 0:
                for i in range(60):
                    bound = ids['manager'] if i==0 else ids['assistant'] if i==1 else ids['member'] if i==2 else 0
                    q.execute("INSERT INTO guild_member(guild_id,user_id,member_user_id,player_name,player_class,role_in_guild,is_active,source_type,join_time) VALUES(0,%s,%s,%s,%s,%s,'1','activity-demo',NOW())",
                              (ids['manager'], bound, f'示例玩家{i+1:02d}', PROFESSIONS[i%len(PROFESSIONS)], '助手' if i==1 else '管理员' if i==0 else '成员'))
                q.execute("INSERT INTO guild_member(guild_id,user_id,member_user_id,player_name,player_class,role_in_guild,is_active,source_type,join_time) VALUES(0,%s,%s,'示例外援','素问','成员','1','activity-demo',NOW())", (ids['guest'], ids['guest']))
        connection.commit()
    with login('manager') as manager:
        existing = api(manager, 'GET', '/activities?kind=mine&pageSize=100')['items']
        if existing:
            print('Fixture activities already exist; existing lineups are preserved.')
            return
        guild = api(manager, 'POST', '/organizations', {'orgType':'guild','name':'示例帮会 · 联赛编排'})
        club = api(manager, 'POST', '/organizations', {'orgType':'club','name':'示例俱乐部 · 六人练习'})
        players = api(manager, 'GET', '/activity-profiles?orgId='+guild['orgId'])
        with login('member') as member:
            own_players = api(member, 'GET', '/activity-profiles')
        for player in own_players:
            api(manager, 'POST', '/organizations/'+club['orgId']+'/members', {'memberId':player['memberId'],'role':'member'})
        start = (datetime.now()+timedelta(days=2)).replace(hour=20,minute=0,second=0,microsecond=0)
        specs = [('组织内部约战 · 可编辑阵容',guild,False,False), ('公开约战 · 职业抢凳子',guild,True,False),
                 ('俱乐部六人练习',club,False,False), ('历史约战 · 暂无CSV战报',guild,False,True)]
        for name, org, public, ended in specs:
            when = start-timedelta(days=5) if ended else start
            activity = api(manager,'POST','/activities',{'orgId':org['orgId'],'name':name,'startsAt':when.isoformat(),
                'endsAt':(when+timedelta(hours=2)).isoformat(),'remark':'独立开发库演示，可自由编辑；无虚构CSV统计。'})
            teams=[]; cursor=0
            for group_index, count in enumerate([3,3,4] if org==guild else [1]):
                squads=[]
                for squad_index in range(count):
                    seats=[]
                    for position in range(1,7):
                        player=None; required=''
                        if org==guild and cursor<48:
                            source=players[cursor];player={'memberId':source['memberId']}
                            required=source['profession'] if position==1 else ''
                        elif org==guild and cursor==48:
                            player={'temporaryId':'temp_demo_substitute','name':'当前活动临时替补','profession':'铁衣'}
                        elif position%2==0:
                            required='素问' if position==2 else '神相'
                        cursor+=1
                        seats.append({'position':position,'requiredProfession':required,'player':player})
                    squads.append({'id':f's_{group_index}_{squad_index}','name':f'{squad_index+1}队','seats':seats})
                teams.append({'id':f't_{group_index}','name':['进攻一团','进攻二团','防守团'][group_index],'squads':squads})
            change={'expectedRevision':activity['revision'],'operationKey':uuid.uuid4().hex,'teams':teams}
            result=api(manager,'PUT',f"/activities/{activity['activityId']}/lineup",change)
            for action in (['publish'] if public else [])+(['end'] if ended else []):
                result=api(manager,'POST',f"/activities/{activity['activityId']}/{action}",
                           {'expectedRevision':result['revision'],'operationKey':uuid.uuid4().hex})
    print('Created 4 fixture accounts, 60 guild candidates, one external player and 4 activities through real APIs.')


def verify():
    with login('manager', legacy=True) as web, login('manager') as mini, login('member') as member, login('guest') as guest:
        assert api(web,'GET','/auth/me')['userId'] == api(mini,'GET','/auth/me')['userId']
        mine=api(web,'GET','/activities?kind=mine&pageSize=100')['items']
        organization_activity=next(a for a in mine if not a['isPublic'] and a['orgType']=='guild' and a['state']=='open')
        path='/activities/'+organization_activity['activityId']
        a=api(web,'GET',path); b=api(mini,'GET',path); member_view=api(member,'GET',path)
        assert a['snapshot']['snapshotId']==b['snapshot']['snapshotId']==member_view['snapshot']['snapshotId']
        assert not member_view['canManage']
        assert guest.get('/api/v1'+path).status_code in (403,404)
        public=api(guest,'GET','/activities?kind=public')['items'];assert public
        public_path='/activities/'+public[0]['activityId']
        public_view=api(guest,'GET',public_path)
        own=api(guest,'GET','/activity-profiles')[0]
        vacant=[(s['id'],seat) for team in public_view['snapshot']['teams'] for s in team['squads'] for seat in s['seats'] if not seat['player']]
        wrong=next((s,seat) for s,seat in vacant if seat['requiredProfession'] and seat['requiredProfession']!=own['profession'])
        correct=next((s,seat) for s,seat in vacant if seat['requiredProfession']==own['profession'])
        request={'expectedRevision':public_view['revision'],'operationKey':uuid.uuid4().hex,
                 'memberId':own['memberId'],'squadId':wrong[0],'position':wrong[1]['position']}
        rejected=guest.post('/api/v1'+public_path+'/signup',json=request)
        assert rejected.status_code==422 and rejected.json()['errorKey']=='PROFESSION_MISMATCH'
        request.update(operationKey=uuid.uuid4().hex,squadId=correct[0],position=correct[1]['position'])
        joined=api(guest,'POST',public_path+'/signup',request)
        occupied=api(guest,'GET',public_path)
        assert occupied['emptySeats']==public_view['emptySeats']-1
        api(guest,'POST',public_path+'/leave',{'expectedRevision':joined['revision'],
            'operationKey':uuid.uuid4().hex,'memberId':own['memberId']})
        assert api(guest,'GET',public_path)['emptySeats']==public_view['emptySeats']
        assert api(web,'GET','/activities?kind=history')['items']
        print('LIVE VERIFIED: same account and saved snapshot; member read-only; outsider private access rejected; public/history readable; wrong profession signup rejected, matching outsider signup and leave succeeded.')
        for client in [web,mini,member,guest]:
            api(client,'POST','/auth/logout')


if __name__=='__main__':
    install_fixtures()
    verify()

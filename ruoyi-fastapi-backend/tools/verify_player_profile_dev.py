"""Real HTTP and membership/privacy checks, only fixture accounts in the approved dev DB."""
import uuid
from datetime import datetime
import bcrypt
import pymysql
from dotenv import dotenv_values
from local_activity_dev import BACKEND, TARGET
from seed_activity_dev import NAMES, PASSWORD, login, api


def prepare_unjoined_account():
    c=dotenv_values(BACKEND/'.env.dev')
    with pymysql.connect(host=c['DB_HOST'],port=int(c['DB_PORT']),user=c['DB_USERNAME'],password=c['DB_PASSWORD'],
                         database=TARGET,charset='utf8mb4',autocommit=False) as db:
        with db.cursor() as q:
            q.execute('SELECT DATABASE()');assert q.fetchone()[0]=='nsh_activity_dev_20260914'
            name='nsh_demo_unjoined'
            q.execute('SELECT user_id,create_by FROM sys_user WHERE user_name=%s',(name,));row=q.fetchone()
            if row:
                assert row[1]=='activity-dev','Fixture username belongs to a non-fixture account'
                account_id=row[0]
            else:
                q.execute("INSERT INTO sys_user (user_name,nick_name,password,status,del_flag,create_by,create_time) VALUES (%s,%s,%s,'0','0','activity-dev',%s)",
                          (name,'未入帮演示账号',bcrypt.hashpw(PASSWORD.encode(),bcrypt.gensalt()).decode(),datetime.now()))
                account_id=q.lastrowid
                q.execute('INSERT INTO sys_user_role (user_id,role_id) VALUES (%s,100)',(account_id,))
            q.execute("SELECT COUNT(*) FROM guild_member WHERE member_user_id=%s AND is_active='1'",(account_id,))
            assert q.fetchone()[0]==0,'This test account must not have any active guild membership'
        db.commit()
    NAMES['unjoined']=name


def verify():
    prepare_unjoined_account()
    with login('manager') as manager,login('assistant') as assistant,login('member') as member,login('guest') as guest,login('unjoined') as unjoined:
        me=api(member,'GET','/auth/me');own=api(member,'GET','/player-profile/me')
        orgs=api(manager,'GET','/organizations');guild=next(o for o in orgs if o['orgType']=='guild')
        activities=api(manager,'GET','/activities?kind=mine&pageSize=100')['items']
        snapshots={a['activityId']:api(manager,'GET','/activities/'+a['activityId'])['snapshot'] for a in activities}
        saved=api(member,'PUT','/player-profile/me',{**own,'playerUid':'00000003','wechatId':'demo-member-wechat','hasOrangeWeapon':True})
        assert saved['playerUid']=='00000003' and saved['hasOrangeWeapon'] is True
        path='/organizations/'+guild['orgId']+'/player-profiles/'+me['userId']
        assert api(manager,'GET',path)==saved and api(assistant,'GET',path)==saved
        assert member.get('/api/v1'+path).status_code==403
        assert guest.get('/api/v1'+path).status_code==403
        club=next(o for o in orgs if o['orgType']=='club')
        assert manager.get('/api/v1/organizations/'+club['orgId']+'/player-profiles/'+me['userId']).status_code==403
        public=api(guest,'GET','/activities?kind=public')['items']
        for activity in public:
            assert 'wechatId' not in str(api(guest,'GET','/activities/'+activity['activityId']))
        assert 'wechatId' not in str(api(manager,'GET','/activity-profiles?orgId='+guild['orgId']))
        for a in activities:
            assert api(manager,'GET','/activities/'+a['activityId'])['snapshot']==snapshots[a['activityId']]
        without_guild=api(unjoined,'PUT','/player-profile/me',dict(name='未入帮演示玩家',playerUid='000001',wechatId='demo-unjoined',hasOrangeWeapon=False,profession='',secondaryProfession='',remark='未入帮也可保存资料'))
        assert api(unjoined,'GET','/player-profile/me')==without_guild
        assert api(unjoined,'GET','/activity-profiles')==[]
        assert api(unjoined,'GET','/profession-styles')
        bad=member.put('/api/v1/player-profile/me',json={**saved,'hasOrangeWeapon':'true'})
        assert bad.status_code==422 and api(member,'GET','/player-profile/me')==saved
        for c in [manager,assistant,member,guest,unjoined]:api(c,'POST','/auth/logout')
    print('LIVE PROFILE PASSED: unjoined account; string UID/boolean persistence; manager and assistant scoped access; member/outsider/club rejected; public privacy; snapshots unchanged; invalid input preserves saved state.')

if __name__=='__main__':verify()

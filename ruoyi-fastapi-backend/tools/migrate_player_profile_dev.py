"""Explicit, additive migration for the single approved independent database."""
from pathlib import Path
import pymysql
from dotenv import dotenv_values

TARGET = 'nsh_activity_dev_20260914'
BACKEND = Path(__file__).resolve().parents[1]

def migrate(target=TARGET):
    if target != TARGET:
        raise ValueError('Only nsh_activity_dev_20260914 is authorized')
    c = dotenv_values(BACKEND / '.env.dev')
    with pymysql.connect(host=c['DB_HOST'], port=int(c['DB_PORT']), user=c['DB_USERNAME'],
        password=c['DB_PASSWORD'], database=target, charset='utf8mb4', autocommit=True) as db:
        with db.cursor() as q:
            q.execute('SELECT DATABASE()')
            if q.fetchone()[0] != TARGET:
                raise ValueError('Database boundary mismatch')
            sql=(BACKEND/'sql/20260914_player_profile_mysql.sql').read_text(encoding='utf-8')
            q.execute(sql)
            q.execute("UPDATE sys_menu SET menu_name='个人中心' WHERE menu_id=3003 AND (component='personal/profileEdit/index' OR path='profile-edit')")
            # Self-only profile UI, no guild/club management permissions added.
            q.execute("INSERT IGNORE INTO sys_role_menu (role_id,menu_id) SELECT r.role_id,m.menu_id FROM sys_role r JOIN sys_menu m ON m.menu_id IN (3000,3003) WHERE r.status='0'")
    print('Added account profile table in '+TARGET+'; original database untouched.')

if __name__ == '__main__':
    migrate()

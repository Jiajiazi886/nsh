"""Read-only metadata/count audit of the single approved development database.

Never outputs passwords, player names, UIDs, WeChat IDs or business row contents.
"""
import json
from pathlib import Path
import re
import pymysql
from dotenv import dotenv_values

TARGET = 'nsh_activity_dev_20260914'
BACKEND = Path(__file__).resolve().parents[1]

def connect(target):
    if target != TARGET:
        raise ValueError('Only nsh_activity_dev_20260914 is authorized')
    c = dotenv_values(BACKEND / '.env.dev')
    return pymysql.connect(host=c['DB_HOST'],port=int(c['DB_PORT']),user=c['DB_USERNAME'],
        password=c['DB_PASSWORD'],database=target,charset='utf8mb4',autocommit=False,
        connect_timeout=5,read_timeout=20,cursorclass=pymysql.cursors.DictCursor)

def audit(target=TARGET):
    with connect(target) as db:
        with db.cursor() as q:
            q.execute('SELECT DATABASE() AS name')
            if q.fetchone()['name'] != TARGET:
                raise ValueError('Database boundary mismatch')
            q.execute('START TRANSACTION READ ONLY')
            q.execute("SELECT TABLE_NAME AS name,TABLE_COMMENT AS comment,DATA_LENGTH AS dataBytes,INDEX_LENGTH AS indexBytes FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME",(TARGET,))
            tables=q.fetchall()
            for table in tables:
                if not re.fullmatch(r'[A-Za-z0-9_]+',table['name']):
                    raise ValueError('Unsafe table identifier')
                q.execute('SELECT COUNT(*) AS count FROM `'+table['name']+'`')
                table['rows']=q.fetchone()['count']
                q.execute('SHOW INDEX FROM `'+table['name']+'`')
                indexes={}
                for row in q.fetchall():
                    indexes.setdefault(row['Key_name'],[]).append((row['Seq_in_index'],row['Column_name']))
                table['indexes']={k:[v[1] for v in sorted(values)] for k,values in indexes.items()}
            q.execute('SELECT TABLE_NAME AS source,REFERENCED_TABLE_NAME AS target FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=%s AND REFERENCED_TABLE_NAME IS NOT NULL',(TARGET,))
            dependencies=q.fetchall()
            q.execute('SELECT TRIGGER_NAME AS name,EVENT_OBJECT_TABLE AS target FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s',(TARGET,))
            triggers=q.fetchall()
            q.execute('EXPLAIN SELECT member_id FROM guild_member WHERE member_user_id=100001 AND is_active=%s ORDER BY member_id DESC LIMIT 1',('1',))
            profile_plan=q.fetchall()
            db.rollback()
    return dict(database=TARGET,tableCount=len(tables),tables=tables,foreignKeys=dependencies,triggers=triggers,profileQueryPlan=profile_plan)

if __name__ == '__main__':
    print(json.dumps(audit(),ensure_ascii=True,default=str))

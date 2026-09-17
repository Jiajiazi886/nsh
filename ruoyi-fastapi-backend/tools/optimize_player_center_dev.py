"""Idempotent, additive indexes only; never drops tables/columns/data or modifies ruoyi."""
from audit_activity_dev_database import TARGET,connect

INDEXES = {
    'ix_guild_member_account_active_id': ['member_user_id','is_active','member_id'],
    'ix_guild_member_owner_active_account': ['user_id','is_active','member_user_id'],
}

def has_prefix(indexes,columns):
    return any(existing[:len(columns)]==columns for existing in indexes.values())

def migrate(target=TARGET):
    if target != TARGET:
        raise ValueError('Only nsh_activity_dev_20260914 is authorized')
    created=[]
    with connect(target) as db:
        with db.cursor() as q:
            q.execute('SELECT DATABASE() AS name')
            if q.fetchone()['name']!=TARGET:
                raise ValueError('Database boundary mismatch')
            q.execute('SHOW INDEX FROM guild_member')
            indexes={}
            for row in q.fetchall():
                indexes.setdefault(row['Key_name'],[]).append((row['Seq_in_index'],row['Column_name']))
            indexes={k:[v[1] for v in sorted(values)] for k,values in indexes.items()}
            for name,columns in INDEXES.items():
                if has_prefix(indexes,columns):
                    continue
                if name in indexes:
                    raise ValueError('Existing index name has different columns: '+name)
                # Identifiers come solely from the fixed source-controlled allowlist above.
                q.execute('ALTER TABLE guild_member ADD INDEX `'+name+'` ('+','.join('`'+c+'`' for c in columns)+')')
                indexes[name]=columns
                created.append(name)
            db.commit()
    return created

if __name__ == '__main__':
    print('Additive indexes in '+TARGET+': '+str(migrate())+'; no tables or records deleted.')

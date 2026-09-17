"""Remove two proven-unused empty guild tables from the approved development DB only.

The migration refuses every other database, validates both candidate row counts
before the first DROP, and records completion for idempotent reruns. Recovery DDL
is stored in sql/20260916_obsolete_guild_tables_recovery.sql.
"""

from audit_activity_dev_database import TARGET, connect


TABLES = ('guild_info', 'guild_review')
VERSION = '20260916_remove_obsolete_guild_tables'


def removable_tables(counts):
    unexpected = set(counts) - set(TABLES)
    if unexpected:
        raise ValueError('Unexpected table in cleanup plan: ' + ', '.join(sorted(unexpected)))
    result = []
    for table in TABLES:
        count = counts.get(table)
        if count is None:
            continue
        if int(count) != 0:
            raise ValueError(f'{table} is not empty; cleanup aborted')
        result.append(table)
    return result


def migrate(target=TARGET):
    if target != TARGET:
        raise ValueError('Only nsh_activity_dev_20260914 is authorized')
    dropped = []
    with connect(target) as db:
        with db.cursor() as q:
            q.execute('SELECT DATABASE() AS name')
            if q.fetchone()['name'] != TARGET:
                raise ValueError('Database boundary mismatch')
            q.execute(
                'SELECT TABLE_NAME AS name FROM information_schema.TABLES '
                'WHERE TABLE_SCHEMA=%s AND TABLE_TYPE=%s AND TABLE_NAME IN (%s,%s)',
                (TARGET, 'BASE TABLE', *TABLES),
            )
            present = {row['name'] for row in q.fetchall()}
            counts = {table: None for table in TABLES}
            for table in TABLES:
                if table in present:
                    q.execute(f'SELECT COUNT(*) AS count FROM `{table}`')
                    counts[table] = q.fetchone()['count']
            candidates = removable_tables(counts)

            q.execute(
                'CREATE TABLE IF NOT EXISTS app_schema_migration ('
                'version varchar(128) NOT NULL PRIMARY KEY,'
                "description varchar(255) NOT NULL DEFAULT '',"
                'applied_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP) '
                "ENGINE=InnoDB COMMENT='应用数据库迁移记录'"
            )
            q.execute('SELECT 1 AS found FROM app_schema_migration WHERE version=%s', (VERSION,))
            applied = q.fetchone() is not None
            if applied:
                if candidates:
                    raise ValueError('Cleanup migration is recorded but obsolete tables still exist')
                db.rollback()
                return []

            for table in candidates:
                q.execute(f'DROP TABLE `{table}`')
                dropped.append(table)
            q.execute(
                'INSERT INTO app_schema_migration (version,description) VALUES (%s,%s)',
                (VERSION, 'Remove empty guild_info and guild_review tables after reference audit'),
            )
            db.commit()
    return dropped


if __name__ == '__main__':
    print('Dropped from ' + TARGET + ': ' + str(migrate()))


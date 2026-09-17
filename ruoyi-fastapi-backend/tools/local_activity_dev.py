"""Explicit local runtime. Never migrates ruoyi or starts copied background jobs."""
import argparse
import os
from pathlib import Path
import re
import sys

BACKEND = Path(__file__).resolve().parents[1]
TARGET = 'nsh_activity_dev_20260914'


def validate_target(name):
    if not re.fullmatch(r'nsh_activity_dev_[0-9]{8}', name):
        raise ValueError('Only an explicitly named independent development database is allowed')
    return name


def runtime_overrides():
    return {
        'APP_ENV': 'dev', 'APP_HOST': '127.0.0.1', 'APP_PORT': '9101',
        'APP_RELOAD': 'false', 'APP_WORKERS': '1', 'APP_IP_LOCATION_QUERY': 'false',
        'APP_NAME': '联赛助手 · 新版开发环境', 'APP_SAME_TIME_LOGIN': 'true',
        'DB_DATABASE': validate_target(TARGET), 'DB_ECHO': 'false',
        'REDIS_DATABASE': '15', 'NSH_ACTIVITIES_ENABLED': 'true',
        'LOG_MASK_ENABLED': 'true', 'LOG_FILE_BASE_DIR': 'logs/activity-dev',
        'TRANSPORT_CRYPTO_ENABLED': 'false', 'TRANSPORT_CRYPTO_MODE': 'off',
    }


def prepare():
    import pymysql
    import redis
    from dotenv import dotenv_values
    c = dotenv_values(BACKEND / '.env.dev')
    target = validate_target(TARGET)
    source = c['DB_DATABASE']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', source) or source == target:
        raise ValueError('Invalid source database')
    connection = dict(host=c['DB_HOST'], port=int(c['DB_PORT']), user=c['DB_USERNAME'],
                      password=c['DB_PASSWORD'], charset='utf8mb4', connect_timeout=5)
    cache = redis.Redis(host=c['REDIS_HOST'], port=int(c['REDIS_PORT']),
                        password=c.get('REDIS_PASSWORD') or None, db=15, socket_connect_timeout=5)
    if cache.dbsize():
        raise ValueError('Redis DB15 is not empty; no keys have been changed')
    with pymysql.connect(**connection, autocommit=True) as destination:
        with destination.cursor() as out:
            out.execute('SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s', (target,))
            if out.fetchone():
                raise ValueError('Development database already exists; refusing to overwrite or recopy it')
            out.execute(f'CREATE DATABASE `{target}` CHARACTER SET utf8mb4')
            out.execute(f'USE `{target}`')
            out.execute('SET SESSION FOREIGN_KEY_CHECKS=0')
            with pymysql.connect(**connection, database=source, autocommit=False) as original:
                with original.cursor() as query:
                    query.execute('SET TRANSACTION READ ONLY')
                    query.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
                    query.execute('SHOW FULL TABLES WHERE Table_type=%s', ('BASE TABLE',))
                    tables = [row[0] for row in query.fetchall()]
                    copied = 0
                    for table in tables:
                        if not re.fullmatch(r'[A-Za-z0-9_]+', table):
                            raise ValueError('Unsupported table identifier')
                        out.execute(f'CREATE TABLE `{target}`.`{table}` LIKE `{source}`.`{table}`')
                        # Operational logs and scheduled jobs are not needed for UI verification.
                        if table in {'sys_oper_log', 'sys_logininfor', 'sys_job_log', 'apscheduler_jobs'}:
                            continue
                        query.execute(f'SHOW FULL COLUMNS FROM `{table}`')
                        columns = [row[0] for row in query.fetchall() if 'GENERATED' not in row[6].upper()]
                        names = ','.join('`' + column + '`' for column in columns)
                        query.execute(f'SELECT {names} FROM `{table}`')
                        statement = f'INSERT INTO `{target}`.`{table}` ({names}) VALUES ({",".join(["%s"] * len(columns))})'
                        while True:
                            rows = query.fetchmany(500)
                            if not rows:
                                break
                            out.executemany(statement, rows)
                            copied += len(rows)
                    original.rollback()
            if 'sys_job' in tables:
                out.execute("UPDATE sys_job SET status='1'")
            sql = (BACKEND / 'sql/20260914_activity_information_mysql.sql').read_text(encoding='utf-8')
            sql = '\n'.join(line for line in sql.splitlines() if not line.lstrip().startswith('--'))
            for statement in sql.split(';'):
                if statement.strip():
                    out.execute(statement)
            out.execute('SET SESSION FOREIGN_KEY_CHECKS=1')
            out.execute('SELECT COUNT(*) FROM sys_user')
            accounts = out.fetchone()[0]
    print(f'Prepared {target}: {len(tables)} original tables, {copied} rows, {accounts} accounts, 9 activity tables.')
    print('Source was read-only. Redis DB15 was checked, not cleared. No passwords or tokens were exported.')


def serve():
    import asyncio
    from contextlib import asynccontextmanager
    from dotenv import dotenv_values
    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    for key, value in dotenv_values(BACKEND / '.env.dev').items():
        if value is not None:
            os.environ[key] = value
    os.environ.update(runtime_overrides())
    from config.get_db import close_async_engine, init_create_table
    from config.get_redis import RedisUtil
    from module_admin.service.log_service import LogAggregatorService
    from server import create_app
    import uvicorn

    @asynccontextmanager
    async def local_lifespan(app):
        app.state.redis = await RedisUtil.create_redis_pool(log_enabled=False)
        task = None
        try:
            await init_create_table()
            await RedisUtil.check_redis_connection(app.state.redis, log_enabled=False)
            await RedisUtil.init_sys_dict(app.state.redis)
            await RedisUtil.init_sys_config(app.state.redis)
            task = asyncio.create_task(LogAggregatorService.consume_stream(app.state.redis))
            yield
        finally:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await RedisUtil.close_redis_pool(app)
            await close_async_engine()

    app = create_app()
    app.router.lifespan_context = local_lifespan
    uvicorn.run(app, host='127.0.0.1', port=9101, root_path='/dev-api', access_log=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'serve'])
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    else:
        serve()

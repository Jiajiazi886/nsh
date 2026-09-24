from fastapi import FastAPI
from redis import asyncio as aioredis
from redis.exceptions import AuthenticationError, RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from config.env import RedisConfig
from utils.log_util import logger


class RedisUtil:
    """
    Redis相关方法
    """

    @classmethod
    async def create_redis_pool(cls, log_enabled: bool = True, log_start_enabled: bool | None = None) -> aioredis.Redis:
        """
        应用启动时初始化redis连接

        :param log_enabled: 是否输出日志
        :param log_start_enabled: 是否输出开始连接日志
        :return: Redis连接对象
        """
        redis = await aioredis.from_url(
            url=f'redis://{RedisConfig.redis_host}',
            port=RedisConfig.redis_port,
            username=RedisConfig.redis_username,
            password=RedisConfig.redis_password,
            db=RedisConfig.redis_database,
            encoding='utf-8',
            decode_responses=True,
        )
        if log_start_enabled is None:
            log_start_enabled = log_enabled
        if log_enabled or log_start_enabled:
            await cls.check_redis_connection(redis, log_enabled=log_enabled, log_start_enabled=log_start_enabled)
        return redis

    @classmethod
    async def check_redis_connection(
        cls, redis: aioredis.Redis, log_enabled: bool = True, log_start_enabled: bool | None = None
    ) -> None:
        """
        检查redis连接状态

        :param redis: redis对象
        :param log_enabled: 是否输出日志
        :param log_start_enabled: 是否输出开始连接日志
        :return: None
        """
        if log_start_enabled is None:
            log_start_enabled = log_enabled
        if log_start_enabled:
            logger.info('🔎 开始连接redis...')
        try:
            connection = await redis.ping()
            if not log_enabled:
                return
            if connection:
                logger.info('✅️ redis连接成功')
            else:
                logger.error('❌️ redis连接失败')
        except AuthenticationError as e:
            if log_enabled:
                logger.error(f'❌️ redis用户名或密码错误，详细错误信息：{e}')
        except RedisTimeoutError as e:
            if log_enabled:
                logger.error(f'❌️ redis连接超时，详细错误信息：{e}')
        except RedisError as e:
            if log_enabled:
                logger.error(f'❌️ redis连接错误，详细错误信息：{e}')

    @classmethod
    async def close_redis_pool(cls, app: FastAPI) -> None:
        """
        应用关闭时关闭redis连接

        :param app: fastapi对象
        :return:
        """
        await app.state.redis.close()
        logger.info('✅️ 关闭redis连接成功')

    @classmethod
    async def cleanup_removed_legacy_keys(cls, redis: aioredis.Redis) -> int:
        """删除已经下线的字典、参数和数据库审计日志缓存键。"""
        keys: set[str] = set()
        for pattern in ('sys_dict:*', 'sys_config:*', 'log:stream', 'log:dedup:*'):
            async for key in redis.scan_iter(match=pattern, count=200):
                keys.add(key)
        if keys:
            await redis.delete(*keys)
            logger.info(f'已清理{len(keys)}个旧字典、参数或审计日志Redis键')
        return len(keys)

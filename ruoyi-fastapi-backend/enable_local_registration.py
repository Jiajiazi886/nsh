import asyncio

from sqlalchemy import text

from common.enums import RedisInitKeyConfig
from config.database import AsyncSessionLocal
from config.get_redis import RedisUtil

REGISTER_CONFIG_KEY = 'sys.account.registerUser'


async def enable_local_registration() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                "UPDATE sys_config "
                "SET config_value = 'true', update_by = 'startup', update_time = NOW() "
                "WHERE config_key = :config_key"
            ),
            {'config_key': REGISTER_CONFIG_KEY},
        )
        if result.rowcount != 1:
            raise RuntimeError(f'Missing required system config: {REGISTER_CONFIG_KEY}')
        await session.commit()

    redis = await RedisUtil.create_redis_pool(log_enabled=False)
    try:
        await redis.set(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{REGISTER_CONFIG_KEY}', 'true')
    finally:
        await redis.aclose()

    print('Local self-registration enabled in MySQL and Redis.')


if __name__ == '__main__':
    asyncio.run(enable_local_registration())

from datetime import datetime, timedelta

from sqlalchemy import select

from config.database import AsyncSessionLocal
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.config_do import SysConfig
from utils.log_util import logger


REGISTER_CLEANUP_CONFIG_KEY = 'sys.account.cleanupInactiveRegisteredUsers'


async def cleanup_inactive_registered_users() -> None:
    """
    Clean self-registered users who never logged in within 24 hours.
    """
    async with AsyncSessionLocal() as session:
        config_value = (
            await session.execute(
                select(SysConfig.config_value).where(SysConfig.config_key == REGISTER_CLEANUP_CONFIG_KEY)
            )
        ).scalar_one_or_none()
        if config_value != 'true':
            logger.info('注册用户24小时未登录自动清理未开启，跳过执行')
            return

        cutoff_time = datetime.now() - timedelta(hours=24)
        deleted_count = await UserDao.cleanup_inactive_registered_users(session, cutoff_time)
        await session.commit()
        logger.info(f'注册用户24小时未登录自动清理完成，删除账号数：{deleted_count}')

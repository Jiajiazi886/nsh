from datetime import datetime, timedelta

from config.database import AsyncSessionLocal
from config.env import AccountConfig
from module_admin.dao.user_dao import UserDao
from utils.log_util import logger


async def cleanup_inactive_registered_users() -> None:
    """
    Clean self-registered users who never logged in within 24 hours.
    """
    if not AccountConfig.account_cleanup_inactive_registered_users:
        logger.info('注册用户24小时未登录自动清理未开启，跳过执行')
        return
    async with AsyncSessionLocal() as session:
        cutoff_time = datetime.now() - timedelta(hours=24)
        deleted_count = await UserDao.cleanup_inactive_registered_users(session, cutoff_time)
        await session.commit()
        logger.info(f'注册用户24小时未登录自动清理完成，删除账号数：{deleted_count}')

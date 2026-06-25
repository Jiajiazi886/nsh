from config.database import AsyncSessionLocal
from module_admin.service.user_service import UserService
from utils.log_util import logger


async def expire_user_vip() -> None:
    """
    定时清理已过期VIP授权。
    """
    async with AsyncSessionLocal() as session:
        expired_count = await UserService.expire_vip_users_services(session)
        logger.info(f'VIP过期清理完成，处理用户数：{expired_count}')

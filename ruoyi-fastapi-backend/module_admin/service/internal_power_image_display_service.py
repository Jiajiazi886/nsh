from datetime import datetime

from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from common.enums import RedisInitKeyConfig
from common.vo import CrudResponseModel
from module_admin.dao.config_dao import ConfigDao
from module_admin.entity.vo.config_vo import ConfigModel
from module_admin.entity.vo.internal_power_image_display_vo import InternalPowerImageDisplayStatusModel


class InternalPowerImageDisplayService:
    """
    内功图片显示开关服务层。
    """

    CONFIG_KEY = 'sys.internalPower.imageDisplayEnabled'
    DEFAULT_VALUE = 'true'

    @classmethod
    async def get_status_services(
        cls, query_db: AsyncSession, redis: aioredis.Redis | None = None
    ) -> InternalPowerImageDisplayStatusModel:
        config = await ConfigDao.get_config_detail_by_info(query_db, ConfigModel(configKey=cls.CONFIG_KEY))
        value = config.config_value if config else cls.DEFAULT_VALUE
        if redis is not None:
            await redis.set(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{cls.CONFIG_KEY}', value)
        return InternalPowerImageDisplayStatusModel(enabled=cls.__is_enabled(value))

    @classmethod
    async def save_status_services(
        cls,
        query_db: AsyncSession,
        redis: aioredis.Redis,
        enabled: bool,
        update_by: str = 'admin',
    ) -> CrudResponseModel:
        value = 'true' if enabled else 'false'
        now = datetime.now()
        config = await ConfigDao.get_config_detail_by_info(query_db, ConfigModel(configKey=cls.CONFIG_KEY))
        if config:
            await ConfigDao.edit_config_dao(
                query_db,
                {
                    'config_id': config.config_id,
                    'config_name': '内功图片显示开关',
                    'config_key': cls.CONFIG_KEY,
                    'config_value': value,
                    'config_type': 'Y',
                    'update_by': update_by,
                    'update_time': now,
                    'remark': '全局控制网页是否显示内功图片，关闭后所有用户页面不渲染内功图片',
                },
            )
        else:
            await ConfigDao.add_config_dao(
                query_db,
                ConfigModel(
                    configName='内功图片显示开关',
                    configKey=cls.CONFIG_KEY,
                    configValue=value,
                    configType='Y',
                    createBy=update_by,
                    createTime=now,
                    updateBy=update_by,
                    updateTime=now,
                    remark='全局控制网页是否显示内功图片，关闭后所有用户页面不渲染内功图片',
                ),
            )
        await query_db.commit()
        await redis.set(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{cls.CONFIG_KEY}', value)
        return CrudResponseModel(is_success=True, message='保存成功')

    @staticmethod
    def __is_enabled(value: str | bytes | None) -> bool:
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='ignore')
        return str(value if value is not None else InternalPowerImageDisplayService.DEFAULT_VALUE).lower() in (
            '1',
            'true',
            'yes',
            'on',
        )

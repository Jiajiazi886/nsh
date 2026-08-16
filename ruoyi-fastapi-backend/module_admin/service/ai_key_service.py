from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from config.env import MimoConfig
from exceptions.exception import PermissionException
from module_admin.entity.vo.ai_key_vo import InternalPowerAiKeyModel, InternalPowerAiKeyUpdateModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.user_service import UserService
from module_ai.entity.do.ai_model_do import AiModels
from utils.crypto_util import CryptoUtil


class AiKeyService:
    """仅维护个人内功图片识别使用的 Mimo API Key。"""

    INTERNAL_POWER_MODEL_CODE = '__internal_power_mimo__'
    INTERNAL_POWER_PROVIDER = 'Mimo'

    @staticmethod
    def ensure_admin(current_user: CurrentUserModel) -> None:
        if not UserService.is_admin_role(current_user):
            raise PermissionException(message='只有管理员可以使用AIKey管理')

    @classmethod
    async def get_internal_power_key_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> InternalPowerAiKeyModel:
        cls.ensure_admin(current_user)
        record = await cls._get_internal_power_record(query_db)
        return InternalPowerAiKeyModel(
            api_key_configured=bool(record and record.api_key),
            update_by=(record.update_by if record else '') or '',
            update_time=record.update_time if record else None,
        )

    @classmethod
    async def update_internal_power_key_services(
        cls,
        query_db: AsyncSession,
        payload: InternalPowerAiKeyUpdateModel,
        current_user: CurrentUserModel,
    ) -> CrudResponseModel:
        cls.ensure_admin(current_user)
        record = await cls._get_internal_power_record(query_db)
        now = datetime.now()
        user_name = current_user.user.user_name

        if record is None:
            record = AiModels(
                model_code=cls.INTERNAL_POWER_MODEL_CODE,
                model_name='内功图片识别',
                provider=cls.INTERNAL_POWER_PROVIDER,
                model_sort=0,
                base_url=MimoConfig.mimo_base_url,
                model_type='chat',
                max_tokens=MimoConfig.mimo_max_completion_tokens,
                support_images='Y',
                status='0',
                create_by=user_name,
                create_time=now,
            )
            query_db.add(record)

        record.api_key = None if payload.clear_api_key else CryptoUtil.encrypt((payload.api_key or '').strip())
        record.update_by = user_name
        record.update_time = now
        try:
            await query_db.commit()
            message = 'AI图片识别 API Key 已清除' if payload.clear_api_key else 'AI图片识别 API Key 已保存'
            return CrudResponseModel(is_success=True, message=message)
        except Exception:
            await query_db.rollback()
            raise

    @classmethod
    async def get_internal_power_api_key(cls, query_db: AsyncSession) -> str:
        """供内功识别服务读取密钥；调用方不得将返回值写入响应或日志。"""
        record = await cls._get_internal_power_record(query_db)
        return CryptoUtil.decrypt(record.api_key) if record and record.api_key else ''

    @classmethod
    async def _get_internal_power_record(cls, query_db: AsyncSession) -> AiModels | None:
        return (
            await query_db.execute(
                select(AiModels).where(
                    AiModels.model_code == cls.INTERNAL_POWER_MODEL_CODE,
                    AiModels.provider == cls.INTERNAL_POWER_PROVIDER,
                )
            )
        ).scalars().first()

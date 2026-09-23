from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from common.vo import CrudResponseModel
from config.env import MimoConfig
from exceptions.exception import PermissionException, ServiceException
from module_admin.entity.vo.ai_key_vo import (
    AiConnectionModel,
    AiConnectionProbeModel,
    AiConnectionSaveModel,
    InternalPowerAiKeyModel,
    InternalPowerAiKeyUpdateModel,
)
from module_admin.service.user_service import UserService
from module_ai.entity.do.ai_model_do import AiModels
from utils.crypto_util import CryptoUtil

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from module_admin.entity.vo.user_vo import CurrentUserModel


@dataclass(frozen=True)
class ActiveAiConnection:
    """后端内部使用的完整连接；绝不能直接写入响应或日志。"""

    id: int | None
    name: str
    provider: str
    base_url: str
    api_key: str
    protocol: str
    model: str
    max_tokens: int
    temperature: float | None
    support_images: bool


class AiKeyService:
    """管理多个 AI 连接，并为全系统提供唯一当前运行时连接。"""

    INTERNAL_POWER_MODEL_CODE = '__internal_power_mimo__'
    INTERNAL_POWER_PROVIDER = 'Mimo'
    ACTIVE_STATUS = '0'
    STANDBY_STATUS = '1'

    @staticmethod
    def ensure_admin(current_user: CurrentUserModel) -> None:
        if not UserService.is_admin_role(current_user):
            raise PermissionException(message='只有管理员可以使用AIKey管理')

    @classmethod
    async def list_connections_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> list[AiConnectionModel]:
        cls.ensure_admin(current_user)
        records = await cls._get_connection_records(query_db)
        return [cls._public_from_record(record) for record in records]

    @classmethod
    async def create_connection_services(
        cls,
        query_db: AsyncSession,
        payload: AiConnectionSaveModel,
        current_user: CurrentUserModel,
    ) -> CrudResponseModel:
        cls.ensure_admin(current_user)
        if not payload.api_key:
            raise ServiceException(message='新建连接必须填写 API Key')
        records = await cls._get_connection_records(query_db, for_update=True)
        now = datetime.now()
        record = AiModels(
            model_code=payload.model,
            model_name=payload.name,
            provider=payload.provider,
            model_sort=max((item.model_sort or 0 for item in records), default=0) + 1,
            api_key=CryptoUtil.encrypt(payload.api_key),
            base_url=payload.base_url,
            model_type=payload.protocol,
            max_tokens=payload.max_tokens,
            temperature=payload.temperature,
            support_reasoning='N',
            support_images='Y' if payload.support_images else 'N',
            status=cls.ACTIVE_STATUS if not records else cls.STANDBY_STATUS,
            create_by=current_user.user.user_name,
            create_time=now,
            update_by=current_user.user.user_name,
            update_time=now,
            remark=payload.remark,
        )
        query_db.add(record)
        await cls._commit(query_db)
        return CrudResponseModel(is_success=True, message='AI 连接已创建')

    @classmethod
    async def update_connection_services(
        cls,
        query_db: AsyncSession,
        connection_id: int,
        payload: AiConnectionSaveModel,
        current_user: CurrentUserModel,
    ) -> CrudResponseModel:
        cls.ensure_admin(current_user)
        record = await cls._get_connection_record(query_db, connection_id, for_update=True)
        if record is None:
            raise ServiceException(message='AI 连接不存在')
        if not record.api_key and not payload.api_key:
            raise ServiceException(message='该连接尚未配置 API Key')
        record.model_name = payload.name
        record.provider = payload.provider
        record.base_url = payload.base_url
        record.model_type = payload.protocol
        record.model_code = payload.model
        record.max_tokens = payload.max_tokens
        record.temperature = payload.temperature
        record.support_images = 'Y' if payload.support_images else 'N'
        record.remark = payload.remark
        if payload.api_key:
            record.api_key = CryptoUtil.encrypt(payload.api_key)
        record.update_by = current_user.user.user_name
        record.update_time = datetime.now()
        await cls._commit(query_db)
        return CrudResponseModel(is_success=True, message='AI 连接已保存')

    @classmethod
    async def activate_connection_services(
        cls,
        query_db: AsyncSession,
        connection_id: int,
        current_user: CurrentUserModel,
    ) -> CrudResponseModel:
        cls.ensure_admin(current_user)
        records = await cls._get_connection_records(query_db, for_update=True)
        target = next((record for record in records if int(record.model_id) == int(connection_id)), None)
        if target is None:
            raise ServiceException(message='AI 连接不存在')
        if not target.api_key:
            raise ServiceException(message='该连接未配置 API Key，无法设为当前')
        now = datetime.now()
        user_name = current_user.user.user_name
        for record in records:
            record.status = cls.ACTIVE_STATUS if record is target else cls.STANDBY_STATUS
            record.update_by = user_name
            record.update_time = now
        await cls._commit(query_db)
        return CrudResponseModel(is_success=True, message=f'已切换到 {cls._display_name(target)}')

    @classmethod
    async def delete_connection_services(
        cls,
        query_db: AsyncSession,
        connection_id: int,
        current_user: CurrentUserModel,
    ) -> CrudResponseModel:
        cls.ensure_admin(current_user)
        record = await cls._get_connection_record(query_db, connection_id, for_update=True)
        if record is None:
            raise ServiceException(message='AI 连接不存在')
        if record.status == cls.ACTIVE_STATUS:
            raise ServiceException(message='当前使用的连接不能删除，请先切换到其他连接')
        await query_db.delete(record)
        await cls._commit(query_db)
        return CrudResponseModel(is_success=True, message='AI 连接已删除')

    @classmethod
    async def get_active_connection(cls, query_db: AsyncSession) -> ActiveAiConnection | None:
        records = await cls._get_connection_records(query_db)
        record = next((item for item in records if item.status == cls.ACTIVE_STATUS), None)
        return cls._runtime_from_record(record) if record else None

    @classmethod
    async def resolve_probe_connection(
        cls,
        query_db: AsyncSession,
        payload: AiConnectionProbeModel,
        *,
        protocol: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ActiveAiConnection:
        runtime = None
        if payload.connection_id is not None:
            record = await cls._get_connection_record(query_db, payload.connection_id)
            if record is None:
                raise ServiceException(message='AI 连接不存在')
            runtime = cls._runtime_from_record(record)
        if runtime is None:
            runtime = ActiveAiConnection(
                id=None,
                name='未保存连接',
                provider='Custom',
                base_url=payload.base_url or '',
                api_key=payload.api_key or '',
                protocol=protocol or 'chat_completions',
                model=model or '',
                max_tokens=max_tokens or 2048,
                temperature=temperature,
                support_images=True,
            )
        return replace(
            runtime,
            base_url=payload.base_url or runtime.base_url,
            api_key=payload.api_key or runtime.api_key,
            protocol=protocol or runtime.protocol,
            model=(model or runtime.model).strip(),
            max_tokens=max_tokens or runtime.max_tokens,
            temperature=temperature if temperature is not None else runtime.temperature,
        )

    @classmethod
    async def get_internal_power_key_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> InternalPowerAiKeyModel:
        cls.ensure_admin(current_user)
        records = await cls._get_connection_records(query_db)
        record = next((item for item in records if item.status == cls.ACTIVE_STATUS), None)
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
        """旧接口兼容层：更新当前连接的密钥。"""
        cls.ensure_admin(current_user)
        records = await cls._get_connection_records(query_db, for_update=True)
        record = next((item for item in records if item.status == cls.ACTIVE_STATUS), None)
        now = datetime.now()
        user_name = current_user.user.user_name
        if record is None:
            record = AiModels(
                model_code=MimoConfig.mimo_model,
                model_name='内功图片识别',
                provider=cls.INTERNAL_POWER_PROVIDER,
                model_sort=1,
                base_url=MimoConfig.mimo_base_url,
                model_type='chat_completions',
                max_tokens=MimoConfig.mimo_max_completion_tokens,
                support_images='Y',
                status=cls.ACTIVE_STATUS,
                create_by=user_name,
                create_time=now,
            )
            query_db.add(record)
        record.api_key = None if payload.clear_api_key else CryptoUtil.encrypt((payload.api_key or '').strip())
        record.update_by = user_name
        record.update_time = now
        await cls._commit(query_db)
        message = 'AI图片识别 API Key 已清除' if payload.clear_api_key else 'AI图片识别 API Key 已保存'
        return CrudResponseModel(is_success=True, message=message)

    @classmethod
    async def get_internal_power_api_key(cls, query_db: AsyncSession) -> str:
        runtime = await cls.get_active_connection(query_db)
        return runtime.api_key if runtime else ''

    @classmethod
    def _public_from_record(cls, record: AiModels) -> AiConnectionModel:
        return AiConnectionModel(
            id=int(record.model_id),
            name=cls._display_name(record),
            provider=record.provider or 'Custom',
            base_url=(record.base_url or '').rstrip('/'),
            protocol=cls._normalize_protocol(record.model_type),
            model=cls._model_code(record),
            api_key_configured=bool(record.api_key),
            max_tokens=int(record.max_tokens or MimoConfig.mimo_max_completion_tokens or 2048),
            temperature=record.temperature,
            support_images=record.support_images == 'Y',
            active=record.status == cls.ACTIVE_STATUS,
            remark=record.remark or '',
            update_by=record.update_by or '',
            update_time=record.update_time,
        )

    @classmethod
    def _runtime_from_record(cls, record: AiModels) -> ActiveAiConnection:
        return ActiveAiConnection(
            id=int(record.model_id),
            name=cls._display_name(record),
            provider=record.provider or 'Custom',
            base_url=(record.base_url or '').rstrip('/'),
            api_key=CryptoUtil.decrypt(record.api_key) if record.api_key else '',
            protocol=cls._normalize_protocol(record.model_type),
            model=cls._model_code(record),
            max_tokens=int(record.max_tokens or MimoConfig.mimo_max_completion_tokens or 2048),
            temperature=record.temperature,
            support_images=record.support_images == 'Y',
        )

    @classmethod
    def _model_code(cls, record: AiModels) -> str:
        return MimoConfig.mimo_model if record.model_code == cls.INTERNAL_POWER_MODEL_CODE else (record.model_code or '').strip()

    @staticmethod
    def _normalize_protocol(value: str | None) -> str:
        return 'responses' if value == 'responses' else 'chat_completions'

    @staticmethod
    def _display_name(record: AiModels) -> str:
        return (record.model_name or record.model_code or '未命名连接').strip()

    @staticmethod
    async def _commit(query_db: AsyncSession) -> None:
        try:
            await query_db.commit()
        except Exception:
            await query_db.rollback()
            raise

    @classmethod
    async def _get_connection_records(
        cls, query_db: AsyncSession, *, for_update: bool = False
    ) -> list[AiModels]:
        statement = select(AiModels).order_by(AiModels.model_sort.asc(), AiModels.model_id.asc())
        if for_update:
            statement = statement.with_for_update()
        return list((await query_db.execute(statement)).scalars().all())

    @classmethod
    async def _get_connection_record(
        cls, query_db: AsyncSession, connection_id: int, *, for_update: bool = False
    ) -> AiModels | None:
        statement = select(AiModels).where(AiModels.model_id == connection_id)
        if for_update:
            statement = statement.with_for_update()
        return (await query_db.execute(statement)).scalars().first()

    @classmethod
    async def _get_internal_power_record(cls, query_db: AsyncSession) -> AiModels | None:
        """仅用于旧代码兼容与数据迁移。"""
        return (
            await query_db.execute(
                select(AiModels).where(
                    AiModels.model_code == cls.INTERNAL_POWER_MODEL_CODE,
                    AiModels.provider == cls.INTERNAL_POWER_PROVIDER,
                )
            )
        ).scalars().first()

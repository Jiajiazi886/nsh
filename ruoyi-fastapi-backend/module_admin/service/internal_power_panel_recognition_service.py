import base64
import json
from datetime import datetime
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.dao.internal_power_panel_recognition_history_dao import InternalPowerPanelRecognitionHistoryDao
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.internal_power_panel_setting_do import PersonalInternalPowerPanelRecognitionHistory
from module_admin.entity.vo.internal_power_panel_setting_vo import (
    PanelRecognitionHistoryListModel,
    PanelRecognitionHistoryModel,
    PanelRecognitionResultModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_mimo_service import InternalPowerMimoService
from module_admin.service.user_service import UserService

PANEL_RECOGNITION_FIELDS = [
    '攻击',
    '破防',
    '会心',
    '会心伤害',
    '流派克制',
    '流派克制百分比',
    '防御',
    '会心抗性',
    '会心防御',
    '流派抵御',
    '流派抵御百分比',
]

PANEL_RECOGNITION_PROMPT = """
你是《逆水寒手游》玩家面板截图识别助手。请只根据图片内容抽取玩家面板数值，并严格返回一个JSON对象。
必须包含这些中文字段：攻击、破防、会心、会心伤害、流派克制、流派克制百分比、防御、会心抗性、会心防御、流派抵御、流派抵御百分比。
数值只保留数字，不要带单位或百分号；百分比字段也输出数字，例如5.1表示5.1%。
无法识别的字段填null。不要输出解释、Markdown或JSON之外的任何文本。
示例：
{"攻击":1665,"破防":1529,"会心":1301,"会心伤害":142.0,"流派克制":301,"流派克制百分比":5.1,"防御":2710,"会心抗性":911,"会心防御":0,"流派抵御":486,"流派抵御百分比":1.2}
""".strip()


class InternalPowerPanelRecognitionService:
    """
    个人玩家面板AI识别服务层
    """

    @classmethod
    async def recognize_image_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, file: UploadFile
    ) -> PanelRecognitionResultModel:
        user_id = int(current_user.user.user_id)
        user_name = current_user.user.user_name
        user = (await UserDao.get_user_detail_by_id(query_db, user_id)).get('user_basic_info')
        if user is None:
            raise ServiceException(message='用户不存在')
        is_unlimited = UserService.is_admin_role(current_user)
        is_effective_vip = UserService.is_effective_vip(user)
        current_vip_count = max(0, int(getattr(user, 'vip_ai_image_recognition_count', 0) or 0))
        usable_vip_count = current_vip_count if is_effective_vip else 0
        current_normal_count = max(0, int(getattr(user, 'ai_image_recognition_count', 0) or 0))
        available_count = usable_vip_count + current_normal_count
        if not is_unlimited and available_count < 1:
            raise ServiceException(message='AI识图次数不足，当前剩余0次')

        file_name = file.filename or 'panel-image'
        mime_type = file.content_type or 'image/png'
        if not mime_type.startswith('image/'):
            raise ServiceException(message='请上传图片文件')
        try:
            image_bytes = await file.read()
        except Exception as exc:
            raise ServiceException(message=f'图片读取失败：{exc}') from exc
        if not image_bytes:
            raise ServiceException(message='图片内容为空')

        history = await cls.__create_history(query_db, user_id, file_name, mime_type, image_bytes)
        history_record_id = int(history.record_id)
        await InternalPowerPanelRecognitionHistoryDao.trim_by_user_id(query_db, user_id)
        await query_db.commit()

        mimo_result = await InternalPowerMimoService.recognize_image_json(
            image_bytes,
            mime_type,
            PANEL_RECOGNITION_PROMPT,
        )
        if mimo_result.parsed is None:
            await cls.__update_history(
                query_db,
                history_record_id,
                user_id,
                'failed',
                None,
                mimo_result.raw_text,
                mimo_result.error or '识别失败',
            )
            await query_db.commit()
            return PanelRecognitionResultModel(
                success=False,
                recordId=history_record_id,
                parsed=None,
                rawText=mimo_result.raw_text,
                error=mimo_result.error or '识别失败',
                remainingVipAiImageRecognitionCount=current_vip_count,
                remainingAiImageRecognitionCount=current_normal_count,
            )

        parsed, validation_error = cls.normalize_panel_json(mimo_result.parsed)
        if validation_error:
            await cls.__update_history(
                query_db,
                history_record_id,
                user_id,
                'failed',
                mimo_result.parsed,
                mimo_result.raw_text,
                validation_error,
            )
            await query_db.commit()
            return PanelRecognitionResultModel(
                success=False,
                recordId=history_record_id,
                parsed=mimo_result.parsed,
                rawText=mimo_result.raw_text,
                error=validation_error,
                remainingVipAiImageRecognitionCount=current_vip_count,
                remainingAiImageRecognitionCount=current_normal_count,
            )

        consumed_vip_count = 0
        consumed_normal_count = 0
        remaining_vip_count = current_vip_count
        remaining_normal_count = current_normal_count
        if not is_unlimited:
            consumed_vip_count = min(usable_vip_count, 1)
            consumed_normal_count = 1 - consumed_vip_count
            deducted = await UserDao.decrement_ai_recognition_counts(
                query_db,
                user_id,
                consumed_vip_count,
                consumed_normal_count,
                user_name,
            )
            if not deducted:
                await cls.__update_history(
                    query_db,
                    history_record_id,
                    user_id,
                    'failed',
                    parsed,
                    mimo_result.raw_text,
                    'AI识图次数不足，未扣次',
                )
                await query_db.commit()
                return PanelRecognitionResultModel(
                    success=False,
                    recordId=history_record_id,
                    parsed=parsed,
                    rawText=mimo_result.raw_text,
                    error='AI识图次数不足，未扣次',
                    remainingVipAiImageRecognitionCount=current_vip_count,
                    remainingAiImageRecognitionCount=current_normal_count,
                )
            remaining_vip_count = max(0, current_vip_count - consumed_vip_count)
            remaining_normal_count = max(0, current_normal_count - consumed_normal_count)

        await cls.__update_history(query_db, history_record_id, user_id, 'recognized', parsed, mimo_result.raw_text, '')
        await query_db.commit()
        return PanelRecognitionResultModel(
            success=True,
            recordId=history_record_id,
            parsed=parsed,
            rawText=mimo_result.raw_text,
            error='',
            consumedCount=0 if is_unlimited else 1,
            consumedVipCount=0 if is_unlimited else consumed_vip_count,
            consumedNormalCount=0 if is_unlimited else consumed_normal_count,
            remainingVipAiImageRecognitionCount=remaining_vip_count,
            remainingAiImageRecognitionCount=remaining_normal_count,
        )

    @classmethod
    async def get_history_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> PanelRecognitionHistoryListModel:
        user_id = int(current_user.user.user_id)
        user = (await UserDao.get_user_detail_by_id(query_db, user_id)).get('user_basic_info')
        visible_limit = 10 if UserService.is_admin_role(current_user) or UserService.is_effective_vip(user) else 5
        rows = await InternalPowerPanelRecognitionHistoryDao.list_by_user_id(query_db, user_id, visible_limit)
        return PanelRecognitionHistoryListModel(
            rows=[cls.__to_history_model(row) for row in rows],
            visibleLimit=visible_limit,
            maxHistoryCount=InternalPowerPanelRecognitionHistoryDao.MAX_HISTORY_COUNT,
        )

    @classmethod
    async def clear_history_services(cls, query_db: AsyncSession, current_user: CurrentUserModel) -> CrudResponseModel:
        await InternalPowerPanelRecognitionHistoryDao.clear_by_user_id(query_db, int(current_user.user.user_id))
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='清空成功')

    @classmethod
    def normalize_panel_json(cls, parsed: dict[str, Any]) -> tuple[dict[str, float | int | None], str]:
        if not isinstance(parsed, dict):
            return {}, '识别结果必须是JSON对象'
        missing = [field for field in PANEL_RECOGNITION_FIELDS if field not in parsed]
        if missing:
            return {}, f'识别结果缺少字段：{"、".join(missing)}'
        normalized: dict[str, float | int | None] = {}
        for field in PANEL_RECOGNITION_FIELDS:
            value = parsed.get(field)
            if value is None or value == '':
                normalized[field] = None
                continue
            number = cls.__to_number(value)
            if number is None:
                return {}, f'{field}不是有效数字'
            normalized[field] = int(number) if float(number).is_integer() else number
        return normalized, ''

    @classmethod
    async def __create_history(
        cls,
        query_db: AsyncSession,
        user_id: int,
        file_name: str,
        mime_type: str,
        image_bytes: bytes,
    ) -> PersonalInternalPowerPanelRecognitionHistory:
        return await InternalPowerPanelRecognitionHistoryDao.add(
            query_db,
            PersonalInternalPowerPanelRecognitionHistory(
                user_id=user_id,
                file_name=file_name,
                mime_type=mime_type,
                image_base64=base64.b64encode(image_bytes).decode('ascii'),
                status='recognizing',
                create_time=datetime.now(),
                update_time=datetime.now(),
            ),
        )

    @classmethod
    async def __update_history(
        cls,
        query_db: AsyncSession,
        record_id: int,
        user_id: int,
        status: str,
        parsed: dict[str, Any] | None,
        raw_text: str,
        error: str,
    ) -> None:
        await InternalPowerPanelRecognitionHistoryDao.update(
            query_db,
            record_id,
            user_id,
            {
                'status': status,
                'parsed_json': cls.__json_dumps(parsed) if parsed is not None else '',
                'raw_text': raw_text or '',
                'error': error or '',
                'update_time': datetime.now(),
            },
        )

    @classmethod
    def __to_history_model(
        cls, row: PersonalInternalPowerPanelRecognitionHistory
    ) -> PanelRecognitionHistoryModel:
        return PanelRecognitionHistoryModel(
            recordId=row.record_id,
            fileName=row.file_name or '',
            imageBase64=row.image_base64 or '',
            mimeType=row.mime_type or 'image/png',
            status=row.status or '',
            parsed=cls.__json_loads(row.parsed_json),
            rawText=row.raw_text or '',
            error=row.error or '',
            createTime=row.create_time,
        )

    @staticmethod
    def __to_number(value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace('%', '').replace(',', '').replace('，', '')
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def __json_dumps(value: Any) -> str:
        return json.dumps(value or {}, ensure_ascii=False, separators=(',', ':'))

    @staticmethod
    def __json_loads(value: str | None) -> dict[str, Any] | None:
        if not value:
            return None
        try:
            loaded = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        return loaded if isinstance(loaded, dict) else None

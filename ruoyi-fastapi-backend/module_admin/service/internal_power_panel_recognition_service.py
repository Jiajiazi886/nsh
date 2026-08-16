import base64
import json
from collections.abc import Callable
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
from module_admin.service.ai_recognition_quota_service import AiRecognitionQuotaService
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

DEFENSE_PANEL_RECOGNITION_FIELDS = [
    '气血',
    '防御',
    '会心抗性',
    '流派抵御',
    '流派抵御百分比',
]

INTERNAL_POWER_BENEFIT_RECOGNITION_FIELDS = [
    '耐力',
    '根骨',
    '身法',
    '内功防御',
    '外功防御',
    '防御',
    '气血上限',
    '抗会心',
    '抗内功会心',
    '抗外功会心',
    '流派抵御',
]

PANEL_RECOGNITION_PROMPT = """
你是《逆水寒手游》玩家面板截图识别助手。请只根据图片内容抽取玩家面板数值，并严格返回一个JSON对象。
必须包含这些中文字段：攻击、破防、会心、会心伤害、流派克制、流派克制百分比、防御、会心抗性、会心防御、流派抵御、流派抵御百分比。
数值只保留数字，不要带单位或百分号；百分比字段也输出数字，例如5.1表示5.1%。
无法识别的字段填null。不要输出解释、Markdown或JSON之外的任何文本。
示例：
{"攻击":1665,"破防":1529,"会心":1301,"会心伤害":142.0,"流派克制":301,"流派克制百分比":5.1,"防御":2710,"会心抗性":911,"会心防御":0,"流派抵御":486,"流派抵御百分比":1.2}
""".strip()

DEFENSE_PANEL_RECOGNITION_PROMPT = """
你是《逆水寒手游》防御属性面板截图识别助手。只识别角色属性面板中的以下五项，并且只返回一个合法JSON对象：
气血、防御、会心抗性、流派抵御、流派抵御百分比。
气血只读取“当前气血/最大气血”斜杠右侧的最大气血；不要读取当前气血。
流派抵御必须按“数值/百分比”拆分。不要把会心防御、首领抵御、技能减免、伤害减免或其他属性写入结果。
字段名称、顺序和类型必须严格如下：
{"气血":91310,"防御":4071,"会心抗性":1130,"流派抵御":391,"流派抵御百分比":"0.0%"}
前四项必须为整数；流派抵御百分比必须为保留百分号的字符串。看不清的字段填null。不要输出解释、Markdown或额外字段。
""".strip()

INTERNAL_POWER_BENEFIT_RECOGNITION_PROMPT = """
你是《逆水寒手游》内功词条总体收益截图识别助手。只识别防御向词条，并且只返回一个合法JSON对象。
字段名称、顺序和类型必须严格如下：
{"耐力":16,"根骨":21,"身法":10,"内功防御":63,"外功防御":29,"防御":182,"气血上限":14207,"抗会心":241,"抗内功会心":407,"抗外功会心":253,"流派抵御":"3.2%"}
前十项必须为整数；流派抵御必须为保留百分号的字符串。只识别防御向词条区域，不要输出攻击、首领抵御、灵韵或任何其他字段。看不清的字段填null。不要输出解释、Markdown或额外字段。
""".strip()


class InternalPowerPanelRecognitionService:
    """
    个人玩家面板AI识别服务层
    """

    @classmethod
    async def recognize_image_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, file: UploadFile
    ) -> PanelRecognitionResultModel:
        return await cls.__recognize_image_services(
            query_db,
            current_user,
            file,
            PANEL_RECOGNITION_PROMPT,
            cls.normalize_panel_json,
        )

    @classmethod
    async def recognize_defense_image_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, file: UploadFile
    ) -> PanelRecognitionResultModel:
        """防守计算器专用识别，使用与内功识别完全相同的统一 Mimo API Key。"""
        return await cls.__recognize_image_services(
            query_db,
            current_user,
            file,
            DEFENSE_PANEL_RECOGNITION_PROMPT,
            cls.normalize_defense_panel_json,
        )

    @classmethod
    async def recognize_internal_power_benefit_image_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, file: UploadFile
    ) -> PanelRecognitionResultModel:
        """内功防御词条识别，统一使用系统管理维护的 Mimo API Key。"""
        return await cls.__recognize_image_services(
            query_db,
            current_user,
            file,
            INTERNAL_POWER_BENEFIT_RECOGNITION_PROMPT,
            cls.normalize_internal_power_benefit_json,
        )

    @classmethod
    async def __recognize_image_services(
        cls,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        file: UploadFile,
        prompt: str,
        normalizer: Callable[[dict[str, Any]], tuple[dict[str, Any], str]],
    ) -> PanelRecognitionResultModel:
        requested_user_id = int(current_user.user.user_id)
        user_name = current_user.user.user_name

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

        quota_snapshot = await AiRecognitionQuotaService.require_quota(query_db, current_user, 1)
        user_id = quota_snapshot.user_id
        if user_id != requested_user_id:
            raise ServiceException(message='用户身份不一致')
        is_unlimited = quota_snapshot.unlimited
        current_vip_count = quota_snapshot.vip_count
        current_normal_count = quota_snapshot.normal_count

        history = await cls.__create_history(query_db, user_id, file_name, mime_type, image_bytes)
        history_record_id = int(history.record_id)
        await InternalPowerPanelRecognitionHistoryDao.trim_by_user_id(query_db, user_id)
        await query_db.commit()

        mimo_result = await InternalPowerMimoService.recognize_image_json(
            image_bytes,
            mime_type,
            prompt,
            query_db=query_db,
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

        parsed, validation_error = normalizer(mimo_result.parsed)
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
            consumption = await AiRecognitionQuotaService.consume_successes(
                query_db,
                quota_snapshot,
                1,
                user_name,
            )
            if not consumption.success:
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
            consumed_vip_count = consumption.vip_count
            consumed_normal_count = consumption.normal_count
            remaining_vip_count = consumption.remaining_vip_count
            remaining_normal_count = consumption.remaining_normal_count

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
    def normalize_defense_panel_json(cls, parsed: dict[str, Any]) -> tuple[dict[str, int | str | None], str]:
        if not isinstance(parsed, dict):
            return {}, '识别结果必须是JSON对象'
        missing = [field for field in DEFENSE_PANEL_RECOGNITION_FIELDS if field not in parsed]
        if missing:
            return {}, f'识别结果缺少字段：{"、".join(missing)}'

        normalized: dict[str, int | str | None] = {}
        for field in DEFENSE_PANEL_RECOGNITION_FIELDS[:-1]:
            value = parsed.get(field)
            if value is None or value == '':
                normalized[field] = None
                continue
            number = cls.__to_number(value)
            if number is None or not float(number).is_integer() or number < 0:
                return {}, f'{field}不是有效整数'
            normalized[field] = int(number)

        percent_value = parsed.get('流派抵御百分比')
        if percent_value is None or percent_value == '':
            normalized['流派抵御百分比'] = None
            return normalized, ''
        percent_number = cls.__to_number(percent_value)
        if percent_number is None or percent_number < 0:
            return {}, '流派抵御百分比不是有效百分比'
        percent_text = str(percent_value).strip().replace('%', '').replace(',', '').replace('，', '')
        if '.' not in percent_text:
            percent_text = f'{int(percent_number)}.0'
        normalized['流派抵御百分比'] = f'{percent_text}%'
        return normalized, ''

    @classmethod
    def normalize_internal_power_benefit_json(cls, parsed: dict[str, Any]) -> tuple[dict[str, int | str | None], str]:
        if not isinstance(parsed, dict):
            return {}, '识别结果必须是JSON对象'
        missing = [field for field in INTERNAL_POWER_BENEFIT_RECOGNITION_FIELDS if field not in parsed]
        if missing:
            return {}, f'识别结果缺少字段：{"、".join(missing)}'

        normalized: dict[str, int | str | None] = {}
        for field in INTERNAL_POWER_BENEFIT_RECOGNITION_FIELDS[:-1]:
            value = parsed.get(field)
            if value is None or value == '':
                normalized[field] = None
                continue
            number = cls.__to_number(value)
            if number is None or not float(number).is_integer() or number < 0:
                return {}, f'{field}不是有效整数'
            normalized[field] = int(number)

        percent_value = parsed.get('流派抵御')
        if percent_value is None or percent_value == '':
            normalized['流派抵御'] = None
            return normalized, ''
        percent_number = cls.__to_number(percent_value)
        if percent_number is None or percent_number < 0:
            return {}, '流派抵御不是有效百分比'
        percent_text = str(percent_value).strip().replace('%', '').replace(',', '').replace('，', '')
        if '.' not in percent_text:
            percent_text = f'{int(percent_number)}.0'
        normalized['流派抵御'] = f'{percent_text}%'
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

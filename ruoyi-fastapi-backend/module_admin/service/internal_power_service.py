import base64
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.constants.internal_power_entries import DEFAULT_INTERNAL_POWER_ENTRIES
from module_admin.dao.internal_power_dao import InternalPowerDao
from module_admin.dao.internal_power_entry_conversion_dao import InternalPowerEntryConversionDao
from module_admin.dao.internal_power_recognition_history_dao import InternalPowerRecognitionHistoryDao
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.internal_power_do import PersonalInternalPower, PersonalInternalPowerRecognitionHistory
from module_admin.entity.vo.internal_power_vo import (
    InternalPowerImportModel,
    InternalPowerListModel,
    InternalPowerModel,
    InternalPowerQuotaModel,
    InternalPowerRecognitionHistoryItemModel,
    InternalPowerRecognitionHistoryListModel,
    InternalPowerRecognitionSavedModel,
    InternalPowerRecognizeResultModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.ai_recognition_quota_service import AiRecognitionQuotaService
from module_admin.service.internal_power_entry_service import InternalPowerEntryService
from module_admin.service.internal_power_mimo_service import InternalPowerMimoService
from module_admin.service.internal_power_preset_service import InternalPowerPresetService
from module_admin.service.user_service import UserService


@dataclass
class InternalPowerEntryStats:
    entry_attack_power: float = 0
    entry_attack_percent: float = 0


class InternalPowerService:
    RECOGNITION_STALE_MINUTES = 10

    """
    个人内功服务层
    """

    @classmethod
    async def get_list_services(cls, query_db: AsyncSession, current_user: CurrentUserModel) -> InternalPowerListModel:
        user_id = current_user.user.user_id
        rows = await InternalPowerDao.list_by_user_id(query_db, user_id)
        conversion_values, unit_percent, entry_limits = await cls.__get_conversion_context(query_db, user_id)
        return InternalPowerListModel(
            powers=[
                cls.__to_model(
                    row,
                    conversion_values=conversion_values,
                    unit_percent=unit_percent,
                    entry_limits=entry_limits,
                )
                for row in rows
            ],
            quota=await cls.__build_quota(query_db, current_user, len(rows)),
        )

    @classmethod
    async def add_power_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, power: InternalPowerModel
    ) -> InternalPowerModel:
        await cls.__assert_can_add(query_db, current_user)
        await cls.__assert_valid_entries(query_db, power.entries)
        now = datetime.now()
        db_power = PersonalInternalPower(
            user_id=current_user.user.user_id,
            name=power.name,
            category=power.category or '',
            category_trait=power.category_trait or '',
            bonus_percent=float(power.bonus_percent or 0),
            lingyun_enabled='1' if power.lingyun_enabled else '0',
            lingyun_bonus_percent=float(power.lingyun_bonus_percent or 0),
            entries_json=cls.__json_dumps(power.entries),
            elements_json=cls.__json_dumps(cls.__model_dump(power.elements)),
            remark=power.remark or '',
            create_time=now,
            update_time=now,
        )
        await InternalPowerDao.add(query_db, db_power)
        conversion_values, unit_percent, entry_limits = await cls.__get_conversion_context(
            query_db, current_user.user.user_id
        )
        result = cls.__to_model(
            db_power,
            conversion_values=conversion_values,
            unit_percent=unit_percent,
            entry_limits=entry_limits,
        )
        await query_db.commit()
        return result

    @classmethod
    async def edit_power_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, power_id: int, power: InternalPowerModel
    ) -> InternalPowerModel:
        existing = await InternalPowerDao.get_by_id(query_db, power_id, current_user.user.user_id)
        if existing is None:
            raise ServiceException(message='内功不存在')
        await cls.__assert_valid_entries(query_db, power.entries)
        values = {
            'name': power.name,
            'category': power.category or '',
            'category_trait': power.category_trait or '',
            'bonus_percent': float(power.bonus_percent or 0),
            'lingyun_enabled': '1' if power.lingyun_enabled else '0',
            'lingyun_bonus_percent': float(power.lingyun_bonus_percent or 0),
            'entries_json': cls.__json_dumps(power.entries),
            'elements_json': cls.__json_dumps(cls.__model_dump(power.elements)),
            'remark': power.remark or '',
            'update_time': datetime.now(),
        }
        await InternalPowerDao.update(query_db, power_id, current_user.user.user_id, values)
        await query_db.commit()
        updated = await InternalPowerDao.get_by_id(query_db, power_id, current_user.user.user_id)
        conversion_values, unit_percent, entry_limits = await cls.__get_conversion_context(
            query_db, current_user.user.user_id
        )
        return cls.__to_model(
            updated,
            conversion_values=conversion_values,
            unit_percent=unit_percent,
            entry_limits=entry_limits,
        )

    @classmethod
    async def delete_power_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, power_id: int
    ) -> CrudResponseModel:
        existing = await InternalPowerDao.get_by_id(query_db, power_id, current_user.user.user_id)
        if existing is None:
            raise ServiceException(message='内功不存在')
        await InternalPowerDao.delete(query_db, power_id, current_user.user.user_id)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def import_local_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, import_data: InternalPowerImportModel
    ) -> InternalPowerListModel:
        for power in import_data.powers:
            await cls.__assert_valid_entries(query_db, power.entries)
        now = datetime.now()
        for power in import_data.powers:
            db_power = PersonalInternalPower(
                user_id=current_user.user.user_id,
                name=power.name,
                category=power.category or '',
                category_trait=power.category_trait or '',
                bonus_percent=float(power.bonus_percent or 0),
                lingyun_enabled='1' if power.lingyun_enabled else '0',
                lingyun_bonus_percent=float(power.lingyun_bonus_percent or 0),
                entries_json=cls.__json_dumps(power.entries),
                elements_json=cls.__json_dumps(cls.__model_dump(power.elements)),
                remark=power.remark or '',
                create_time=now,
                update_time=now,
            )
            await InternalPowerDao.add(query_db, db_power)
        await query_db.commit()
        return await cls.get_list_services(query_db, current_user)

    @classmethod
    async def recognize_images_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, files: list[Any], prompt: str
    ) -> InternalPowerRecognizeResultModel:
        current_user_name = current_user.user.user_name
        image_count = len(files or [])
        if image_count <= 0:
            raise ServiceException(message='请至少上传一张图片')
        quota_snapshot = await AiRecognitionQuotaService.require_quota(query_db, current_user, image_count)
        target_user_id = quota_snapshot.user_id
        is_unlimited_recognition = quota_snapshot.unlimited
        current_vip_count = quota_snapshot.vip_count
        current_normal_count = quota_snapshot.normal_count
        presets = await InternalPowerPresetService.get_personal_enabled_presets_service(query_db)
        preset_map: dict[str, list[dict[str, Any]]] = {}
        for preset in presets:
            preset_map.setdefault(preset.name, []).append(cls.__preset_candidate_to_dict(preset))
        valid_entry_names = {item['entry_name'] for item in DEFAULT_INTERNAL_POWER_ENTRIES}
        items = []
        success_count = 0
        success_history_ids: list[int] = []
        for file in files:
            file_name = file.filename or 'image'
            content_type = file.content_type or 'image/png'
            history_record_id = 0
            history_user_id = target_user_id
            try:
                image_bytes = await file.read()
            except Exception as exc:
                item = cls.__recognize_item(file_name, False, None, '', f'图片读取失败：{exc}', [])
                history = await cls.__create_recognition_history(
                    query_db, target_user_id, file_name, b'', content_type, 'failed'
                )
                history_record_id = int(history.record_id)
                history_user_id = int(history.user_id)
                await cls.__update_recognition_history(query_db, history_record_id, history_user_id, item)
                await query_db.commit()
                items.append({**item, 'recordId': history_record_id})
                continue
            history = await cls.__create_recognition_history(
                query_db, target_user_id, file_name, image_bytes, content_type, 'recognizing'
            )
            history_record_id = int(history.record_id)
            history_user_id = int(history.user_id)
            await InternalPowerRecognitionHistoryDao.trim_by_user_id(query_db, target_user_id)
            await query_db.commit()
            mimo_result = await InternalPowerMimoService.recognize_image(
                image_bytes,
                content_type,
                prompt,
                query_db=query_db,
            )
            if mimo_result.parsed is None:
                item = cls.__recognize_item(file_name, False, None, mimo_result.raw_text, mimo_result.error, [])
                await cls.__update_recognition_history(query_db, history_record_id, history_user_id, item)
                await query_db.commit()
                items.append({**item, 'recordId': history_record_id})
                continue
            invalid_entry = cls.__find_invalid_recognized_entry(mimo_result.parsed, valid_entry_names)
            if invalid_entry:
                item = cls.__recognize_item(file_name, False, mimo_result.parsed, mimo_result.raw_text, invalid_entry, [])
                await cls.__update_recognition_history(query_db, history_record_id, history_user_id, item)
                await query_db.commit()
                items.append({**item, 'recordId': history_record_id})
                continue
            power_name = cls.__extract_recognized_power_name(mimo_result.parsed)
            if power_name:
                mimo_result.parsed['内功名'] = power_name
            candidates = cls.__resolve_recognition_candidates(
                preset_map.get(power_name, []),
                mimo_result.parsed,
            )
            if not candidates:
                item = cls.__recognize_item(
                    file_name,
                    False,
                    mimo_result.parsed,
                    mimo_result.raw_text,
                    '识别到的内功名没有匹配到启用预设',
                    [],
                )
                await cls.__update_recognition_history(query_db, history_record_id, history_user_id, item)
                await query_db.commit()
                items.append({**item, 'recordId': history_record_id})
                continue
            success_count += 1
            needs_preset_selection = len(candidates) > 1
            item = cls.__recognize_item(
                file_name,
                True,
                mimo_result.parsed,
                mimo_result.raw_text,
                '',
                candidates,
                needs_preset_selection=needs_preset_selection,
                preset_selection_message='该内功存在多个元素，请选择元素后再新增' if needs_preset_selection else '',
            )
            await cls.__update_recognition_history(query_db, history_record_id, history_user_id, item)
            await query_db.commit()
            success_history_ids.append(history_record_id)
            items.append({**item, 'recordId': history_record_id})
        consumed_vip_count = 0
        consumed_normal_count = 0
        remaining_vip_count = current_vip_count
        remaining_normal_count = current_normal_count
        if success_count > 0 and not is_unlimited_recognition:
            consumption = await AiRecognitionQuotaService.consume_successes(
                query_db,
                quota_snapshot,
                success_count,
                current_user_name,
            )
            if consumption.success:
                consumed_vip_count = consumption.vip_count
                consumed_normal_count = consumption.normal_count
                remaining_vip_count = consumption.remaining_vip_count
                remaining_normal_count = consumption.remaining_normal_count
                await query_db.commit()
            else:
                success_count = 0
                consumed_vip_count = 0
                consumed_normal_count = 0
                items = [
                    cls.__recognize_item(
                        item.get('fileName') or 'image',
                        False,
                        item.get('parsed') or {},
                        item.get('rawText') or '',
                        'AI识图次数不足，未扣次',
                        [],
                    )
                    | {'recordId': item.get('recordId')}
                    if item.get('success')
                    else item
                    for item in items
                ]
                for record_id in success_history_ids:
                    await InternalPowerRecognitionHistoryDao.update(
                        query_db,
                        record_id,
                        target_user_id,
                        {
                            'status': 'failed',
                            'error': 'AI识图次数不足，未扣次',
                            'preset_candidates_json': '[]',
                        },
                    )
                await query_db.commit()
        return InternalPowerRecognizeResultModel(
            result={'items': items},
            consumedCount=0 if is_unlimited_recognition else success_count,
            consumedVipCount=0 if is_unlimited_recognition else consumed_vip_count,
            consumedNormalCount=0 if is_unlimited_recognition else consumed_normal_count,
            remainingVipAiImageRecognitionCount=remaining_vip_count,
            remainingAiImageRecognitionCount=remaining_normal_count,
        )

    @classmethod
    async def get_recognition_history_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, page_num: int = 1, page_size: int = 10
    ) -> InternalPowerRecognitionHistoryListModel:
        page_result = await InternalPowerRecognitionHistoryDao.list_by_user_id(
            query_db, current_user.user.user_id, page_num, page_size
        )
        rows = page_result.rows if hasattr(page_result, 'rows') else page_result
        total = page_result.total if hasattr(page_result, 'total') else len(rows)
        page_num_value = page_result.page_num if hasattr(page_result, 'page_num') else page_num
        page_size_value = page_result.page_size if hasattr(page_result, 'page_size') else page_size
        has_next = page_result.has_next if hasattr(page_result, 'has_next') else False
        if await cls.__mark_stale_recognition_history_failed(query_db, rows):
            await query_db.commit()
            page_result = await InternalPowerRecognitionHistoryDao.list_by_user_id(
                query_db, current_user.user.user_id, page_num, page_size
            )
            rows = page_result.rows if hasattr(page_result, 'rows') else page_result
            total = page_result.total if hasattr(page_result, 'total') else len(rows)
            page_num_value = page_result.page_num if hasattr(page_result, 'page_num') else page_num
            page_size_value = page_result.page_size if hasattr(page_result, 'page_size') else page_size
            has_next = page_result.has_next if hasattr(page_result, 'has_next') else False
        return InternalPowerRecognitionHistoryListModel(
            items=[cls.__history_to_model(row) for row in rows],
            total=total,
            pageNum=page_num_value,
            pageSize=page_size_value,
            hasNext=has_next,
        )

    @classmethod
    async def clear_recognition_history_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> CrudResponseModel:
        await InternalPowerRecognitionHistoryDao.clear_by_user_id(query_db, current_user.user.user_id)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='识别记录已清空')

    @classmethod
    async def mark_recognition_history_saved_services(
        cls,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        record_id: int,
        payload: InternalPowerRecognitionSavedModel,
    ) -> CrudResponseModel:
        await InternalPowerRecognitionHistoryDao.update(
            query_db,
            record_id,
            current_user.user.user_id,
            {'status': 'saved', 'saved_power_id': payload.saved_power_id},
        )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='识别记录已更新')

    @staticmethod
    def __recognize_item(
        file_name: str,
        success: bool,
        parsed: dict[str, Any] | None,
        raw_text: str,
        error: str,
        preset_candidates: list[dict[str, Any]],
        needs_preset_selection: bool = False,
        preset_selection_message: str = '',
    ) -> dict[str, Any]:
        return {
            'fileName': file_name,
            'success': success,
            'parsed': parsed or {},
            'rawText': raw_text or '',
            'error': error or '',
            'presetCandidates': preset_candidates,
            'needsPresetSelection': needs_preset_selection,
            'presetSelectionMessage': preset_selection_message,
        }

    @classmethod
    async def __create_recognition_history(
        cls,
        query_db: AsyncSession,
        user_id: int,
        file_name: str,
        image_bytes: bytes,
        mime_type: str,
        status: str,
    ) -> PersonalInternalPowerRecognitionHistory:
        now = datetime.now()
        image_base64 = base64.b64encode(image_bytes).decode('ascii') if image_bytes else ''
        return await InternalPowerRecognitionHistoryDao.add(
            query_db,
            {
                'user_id': user_id,
                'file_name': file_name or 'image',
                'image_base64': image_base64,
                'mime_type': mime_type or 'image/png',
                'status': status,
                'parsed_json': '{}',
                'raw_text': '',
                'error': '',
                'preset_candidates_json': '[]',
                'create_time': now,
                'update_time': now,
            },
        )

    @classmethod
    async def __update_recognition_history(
        cls, query_db: AsyncSession, record_id: int, user_id: int, item: dict[str, Any]
    ) -> None:
        await InternalPowerRecognitionHistoryDao.update(
            query_db,
            record_id,
            user_id,
            {
                'status': 'recognized' if item.get('success') else 'failed',
                'parsed_json': cls.__json_dumps(item.get('parsed') or {}),
                'raw_text': item.get('rawText') or '',
                'error': item.get('error') or '',
                'preset_candidates_json': cls.__json_dumps(item.get('presetCandidates') or []),
            },
        )

    @classmethod
    async def __mark_stale_recognition_history_failed(
        cls, query_db: AsyncSession, rows: list[PersonalInternalPowerRecognitionHistory]
    ) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(minutes=cls.RECOGNITION_STALE_MINUTES)
        changed = False
        for history in rows:
            if (history.status or '') != 'recognizing':
                continue
            last_update = history.update_time or history.create_time
            if last_update and last_update > cutoff:
                continue
            await InternalPowerRecognitionHistoryDao.update(
                query_db,
                history.record_id,
                history.user_id,
                {
                    'status': 'failed',
                    'error': f'识别任务已中断或超时，超过{cls.RECOGNITION_STALE_MINUTES}分钟没有更新，请重新上传识别',
                    'preset_candidates_json': '[]',
                },
            )
            changed = True
        return changed

    @classmethod
    def __history_to_model(
        cls, history: PersonalInternalPowerRecognitionHistory
    ) -> InternalPowerRecognitionHistoryItemModel:
        preset_candidates = cls.__json_loads(history.preset_candidates_json, [])
        needs_preset_selection = (
            (history.status or '') == 'recognized'
            and not history.saved_power_id
            and len(preset_candidates) > 1
        )
        return InternalPowerRecognitionHistoryItemModel(
            recordId=history.record_id,
            fileName=history.file_name or '',
            imageBase64=history.image_base64 or '',
            mimeType=history.mime_type or 'image/png',
            status=history.status or 'recognizing',
            parsed=cls.__json_loads(history.parsed_json, {}),
            rawText=history.raw_text or '',
            error=history.error or '',
            presetCandidates=preset_candidates,
            needsPresetSelection=needs_preset_selection,
            presetSelectionMessage='该内功存在多个元素，请选择元素后再新增' if needs_preset_selection else '',
            savedPowerId=history.saved_power_id,
            createTime=history.create_time,
            updateTime=history.update_time,
        )

    @staticmethod
    def __find_invalid_recognized_entry(parsed: dict[str, Any], valid_entry_names: set[str]) -> str:
        entries = parsed.get('属性加成') or []
        for entry in entries:
            entry_name = str((entry or {}).get('词条') or '').strip()
            if entry_name not in valid_entry_names:
                return f'识别到白名单外词条：{entry_name or "空词条"}'
        return ''

    @classmethod
    def __extract_recognized_power_name(cls, parsed: dict[str, Any]) -> str:
        return cls.__normalize_recognized_power_name(parsed.get('内功名') or parsed.get('name'))

    @staticmethod
    def __normalize_recognized_power_name(value: Any) -> str:
        text = str(value or '').strip()
        if not text:
            return ''
        text = text.replace('·试用', '').replace('・试用', '').replace('试用', '').strip()
        rare_aliases = {
            '日月两仪': '稀有-日月两仪',
            '稀有-日月两仪': '稀有-日月两仪',
            '不动明王': '稀有-不动明王',
            '稀有-不动明王': '稀有-不动明王',
            '绝电惊沙': '稀有-绝电惊沙',
            '稀有-绝电惊沙': '稀有-绝电惊沙',
            '承影锋烁': '稀有-承影锋烁',
            '稀有-承影锋烁': '稀有-承影锋烁',
            '灼星贯日': '稀有-灼星贯日',
            '稀有-灼星贯日': '稀有-灼星贯日',
        }
        return rare_aliases.get(text, text)

    @classmethod
    def __resolve_recognition_candidates(
        cls, candidates: list[dict[str, Any]], parsed: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if len(candidates) <= 1:
            return candidates
        element_key = cls.__extract_recognized_element_key(parsed)
        if not element_key:
            return candidates
        matched_candidates = [
            candidate for candidate in candidates if str(candidate.get('elementKey') or '') == element_key
        ]
        return matched_candidates if len(matched_candidates) == 1 else candidates

    @classmethod
    def __extract_recognized_element_key(cls, parsed: dict[str, Any]) -> str:
        for field_name in ('元素', '五行', 'element'):
            element_key = cls.__normalize_recognized_element_key(parsed.get(field_name))
            if element_key:
                return element_key
        return ''

    @staticmethod
    def __normalize_recognized_element_key(value: Any) -> str:
        text = str(value or '').strip().lower()
        if not text:
            return ''
        compact_text = ''.join(text.split())
        element_aliases = {
            'metal': 'metal',
            'gold': 'metal',
            'jin': 'metal',
            '金': 'metal',
            'wood': 'wood',
            'mu': 'wood',
            '木': 'wood',
            'water': 'water',
            'shui': 'water',
            '水': 'water',
            'fire': 'fire',
            'huo': 'fire',
            '火': 'fire',
            'earth': 'earth',
            'soil': 'earth',
            'tu': 'earth',
            '土': 'earth',
            'mixed': 'mixed',
            'all': 'mixed',
            '金木水火土': 'mixed',
            '五行': 'mixed',
            '全元素': 'mixed',
        }
        return element_aliases.get(compact_text, '')

    @classmethod
    def __preset_candidate_to_dict(cls, preset: Any) -> dict[str, Any]:
        return {
            'presetId': preset.preset_id,
            'name': preset.name,
            'displayName': preset.display_name,
            'elementKey': preset.element_key,
            'elements': cls.__model_dump(preset.elements),
            'bonusPercent': preset.bonus_percent,
            'lingyunBonusPercent': getattr(preset, 'lingyun_bonus_percent', 0) or 0,
            'bonusType': preset.bonus_type or '',
            'bonusDesc': preset.bonus_desc or '',
            'imageUrl': preset.image_url or '',
            'entries': cls.__model_dump(preset.entries),
        }

    @classmethod
    async def __assert_can_add(cls, query_db: AsyncSession, current_user: CurrentUserModel) -> None:
        quota = await cls.__build_quota(query_db, current_user)
        if quota.unlimited:
            return
        if quota.max_count is not None and quota.count >= quota.max_count:
            raise ServiceException(message='已超过当前内功上限，请删除后再新增或联系管理员调整上限')

    @classmethod
    async def __assert_valid_entries(cls, query_db: AsyncSession, entries: list[Any]) -> None:
        if not entries:
            return
        entry_limits = await cls.__get_entry_limit_map(query_db)
        invalid_names = []
        invalid_values = []
        for entry in entries:
            entry_data = cls.__model_dump(entry)
            entry_name = str((entry_data or {}).get('name') or '').strip()
            if not entry_name:
                continue
            limit = entry_limits.get(entry_name)
            if limit is None:
                invalid_names.append(entry_name)
                continue
            entry_value = cls.__parse_entry_value((entry_data or {}).get('value'))
            if entry_value is None or entry_value < 0 or entry_value > float(limit['limit_value']):
                invalid_values.append(f'{entry_name}不能超过{limit["limit_text"]}')
        if invalid_names:
            raise ServiceException(message=f'内功词条只能选择系统内置启用词条：{", ".join(sorted(set(invalid_names)))}')
        if invalid_values:
            raise ServiceException(message='；'.join(invalid_values))

    @classmethod
    async def __build_quota(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, count: int | None = None
    ) -> InternalPowerQuotaModel:
        user = (await UserDao.get_user_detail_by_id(query_db, current_user.user.user_id)).get('user_basic_info')
        current_count = count if count is not None else await InternalPowerDao.count_by_user_id(query_db, user.user_id)
        is_admin = UserService.is_admin_role(current_user)
        is_effective_vip = UserService.is_effective_vip(user)
        unlimited = is_admin or is_effective_vip
        max_count = None if unlimited else max(20, int(user.max_internal_power_count or 20))
        return InternalPowerQuotaModel(
            count=current_count,
            maxCount=max_count,
            unlimited=unlimited,
            isVip='1' if is_effective_vip else '0',
            vipExpireTime=user.vip_expire_time,
        )

    @classmethod
    def __to_model(
        cls,
        power: PersonalInternalPower | None,
        conversion_values: dict[str, float] | None = None,
        unit_percent: float = 0,
        entry_limits: dict[str, dict[str, Any]] | None = None,
    ) -> InternalPowerModel:
        if power is None:
            raise ServiceException(message='内功不存在')
        entries = cls.__json_loads(power.entries_json, [])
        entry_stats = cls.calculate_entry_stats(entries, conversion_values or {}, unit_percent, entry_limits or {})
        bonus_percent = float(power.bonus_percent or 0)
        lingyun_enabled = str(getattr(power, 'lingyun_enabled', '0') or '0') == '1'
        lingyun_bonus_percent = float(getattr(power, 'lingyun_bonus_percent', 0) or 0)
        active_lingyun_bonus = lingyun_bonus_percent if lingyun_enabled else 0
        return InternalPowerModel(
            id=str(power.power_id),
            powerId=power.power_id,
            userId=power.user_id,
            name=power.name,
            category=power.category or '',
            categoryTrait=power.category_trait or '',
            bonusPercent=bonus_percent,
            lingyunEnabled=lingyun_enabled,
            lingyunBonusPercent=lingyun_bonus_percent,
            entryAttackPower=entry_stats.entry_attack_power,
            entryAttackPercent=entry_stats.entry_attack_percent,
            totalBonusPercent=round(bonus_percent + entry_stats.entry_attack_percent + active_lingyun_bonus, 5),
            entries=entries,
            elements=cls.__json_loads(power.elements_json, {}),
            remark=power.remark or '',
            updatedAt=power.update_time,
        )

    @classmethod
    async def __get_conversion_context(
        cls, query_db: AsyncSession, user_id: int
    ) -> tuple[dict[str, float], float, dict[str, dict[str, Any]]]:
        setting = await InternalPowerEntryConversionDao.get_setting(query_db, user_id)
        values = await InternalPowerEntryConversionDao.list_values(query_db, user_id)
        entry_limits = await cls.__get_entry_limit_map(query_db)
        conversion_values = {
            value.entry_name: float(value.attack_power or 0)
            for value in values
            if value.entry_name in entry_limits
        }
        return conversion_values, float(setting.unit_percent if setting else 0), entry_limits

    @classmethod
    def calculate_entry_stats(
        cls,
        entries: list[Any],
        conversion_values: dict[str, float],
        unit_percent: float,
        entry_limits: dict[str, dict[str, Any]],
    ) -> InternalPowerEntryStats:
        total_attack_power = 0.0
        total_attack_percent = 0.0
        for entry in entries or []:
            entry_data = cls.__model_dump(entry)
            entry_name = str((entry_data or {}).get('name') or '').strip()
            limit = entry_limits.get(entry_name)
            if limit is None:
                continue
            entry_value = cls.__parse_entry_value((entry_data or {}).get('value'))
            if entry_value is None or entry_value < 0:
                continue
            limit_value = float(limit['limit_value'] or 0)
            if limit_value <= 0 or entry_value > limit_value:
                continue
            configured_attack_power = float(conversion_values.get(entry_name, 0) or 0)
            entry_attack_power = round(entry_value / limit_value * configured_attack_power, 5)
            total_attack_power += entry_attack_power
            total_attack_percent += round(entry_attack_power * float(unit_percent or 0), 5)
        return InternalPowerEntryStats(
            entry_attack_power=round(total_attack_power, 5),
            entry_attack_percent=round(total_attack_percent, 5),
        )

    @classmethod
    async def __get_entry_limit_map(cls, query_db: AsyncSession) -> dict[str, dict[str, Any]]:
        entries = await InternalPowerEntryService.get_personal_enabled_entries_service(query_db)
        return {
            entry.entry_name: {
                'limit_text': entry.limit_text or '',
                'limit_value': float(entry.limit_value or 0),
                'value_type': entry.value_type or 'number',
            }
            for entry in entries
        }

    @staticmethod
    def __parse_entry_value(value: Any) -> float | None:
        if value is None:
            return None
        try:
            text = str(value).strip().replace('%', '')
            if not text:
                return None
            return float(text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def __model_dump(value: Any) -> Any:
        if hasattr(value, 'model_dump'):
            return value.model_dump()
        if isinstance(value, list):
            return [InternalPowerService.__model_dump(item) for item in value]
        if isinstance(value, tuple):
            return [InternalPowerService.__model_dump(item) for item in value]
        if isinstance(value, dict):
            return {key: InternalPowerService.__model_dump(item) for key, item in value.items()}
        return value

    @classmethod
    def __json_dumps(cls, value: Any) -> str:
        return json.dumps(cls.__model_dump(value), ensure_ascii=False)

    @staticmethod
    def __json_loads(value: str | None, default: Any) -> Any:
        if not value:
            return default
        try:
            return json.loads(value)
        except Exception:
            return default

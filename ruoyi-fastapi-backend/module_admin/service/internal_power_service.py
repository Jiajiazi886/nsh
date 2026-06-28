import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.constants.internal_power_entry_limits import INTERNAL_POWER_ENTRY_LIMIT_MAP
from module_admin.dao.internal_power_dao import InternalPowerDao
from module_admin.dao.internal_power_entry_conversion_dao import InternalPowerEntryConversionDao
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.internal_power_do import PersonalInternalPower
from module_admin.entity.vo.internal_power_vo import (
    InternalPowerImportModel,
    InternalPowerListModel,
    InternalPowerModel,
    InternalPowerQuotaModel,
    InternalPowerRecognizeResultModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.user_service import UserService


@dataclass
class InternalPowerEntryStats:
    entry_attack_power: float = 0
    entry_attack_percent: float = 0


class InternalPowerService:
    """
    个人内功服务层
    """

    @classmethod
    async def get_list_services(cls, query_db: AsyncSession, current_user: CurrentUserModel) -> InternalPowerListModel:
        user_id = current_user.user.user_id
        rows = await InternalPowerDao.list_by_user_id(query_db, user_id)
        conversion_values, unit_percent = await cls.__get_conversion_context(query_db, user_id)
        return InternalPowerListModel(
            powers=[
                cls.__to_model(row, conversion_values=conversion_values, unit_percent=unit_percent)
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
            entries_json=cls.__json_dumps(power.entries),
            elements_json=cls.__json_dumps(cls.__model_dump(power.elements)),
            remark=power.remark or '',
            create_time=now,
            update_time=now,
        )
        await InternalPowerDao.add(query_db, db_power)
        conversion_values, unit_percent = await cls.__get_conversion_context(query_db, current_user.user.user_id)
        result = cls.__to_model(db_power, conversion_values=conversion_values, unit_percent=unit_percent)
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
            'entries_json': cls.__json_dumps(power.entries),
            'elements_json': cls.__json_dumps(cls.__model_dump(power.elements)),
            'remark': power.remark or '',
            'update_time': datetime.now(),
        }
        await InternalPowerDao.update(query_db, power_id, current_user.user.user_id, values)
        await query_db.commit()
        updated = await InternalPowerDao.get_by_id(query_db, power_id, current_user.user.user_id)
        conversion_values, unit_percent = await cls.__get_conversion_context(query_db, current_user.user.user_id)
        return cls.__to_model(updated, conversion_values=conversion_values, unit_percent=unit_percent)

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
        cls, query_db: AsyncSession, current_user: CurrentUserModel, image_count: int
    ) -> InternalPowerRecognizeResultModel:
        if image_count <= 0:
            raise ServiceException(message='请至少上传一张图片')
        user = (await UserDao.get_user_detail_by_id(query_db, current_user.user.user_id)).get('user_basic_info')
        if user is None:
            raise ServiceException(message='用户不存在')
        current_count = max(0, int(user.ai_image_recognition_count or 0))
        if current_count < image_count:
            raise ServiceException(message=f'AI识图次数不足，当前剩余{current_count}次')
        remaining_count = current_count - image_count
        await UserDao.edit_user_dao(
            query_db,
            {
                'user_id': user.user_id,
                'ai_image_recognition_count': remaining_count,
                'update_by': current_user.user.user_name,
                'update_time': datetime.now(),
            },
        )
        await query_db.commit()
        return InternalPowerRecognizeResultModel(
            result={},
            consumedCount=image_count,
            remainingAiImageRecognitionCount=remaining_count,
        )

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
        invalid_names = []
        invalid_values = []
        for entry in entries:
            entry_data = cls.__model_dump(entry)
            entry_name = str((entry_data or {}).get('name') or '').strip()
            if not entry_name:
                continue
            limit = INTERNAL_POWER_ENTRY_LIMIT_MAP.get(entry_name)
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
    ) -> InternalPowerModel:
        if power is None:
            raise ServiceException(message='内功不存在')
        entries = cls.__json_loads(power.entries_json, [])
        entry_stats = cls.calculate_entry_stats(entries, conversion_values or {}, unit_percent)
        bonus_percent = float(power.bonus_percent or 0)
        return InternalPowerModel(
            id=str(power.power_id),
            powerId=power.power_id,
            userId=power.user_id,
            name=power.name,
            category=power.category or '',
            categoryTrait=power.category_trait or '',
            bonusPercent=bonus_percent,
            entryAttackPower=entry_stats.entry_attack_power,
            entryAttackPercent=entry_stats.entry_attack_percent,
            totalBonusPercent=round(bonus_percent + entry_stats.entry_attack_percent, 5),
            entries=entries,
            elements=cls.__json_loads(power.elements_json, {}),
            remark=power.remark or '',
            updatedAt=power.update_time,
        )

    @classmethod
    async def __get_conversion_context(cls, query_db: AsyncSession, user_id: int) -> tuple[dict[str, float], float]:
        setting = await InternalPowerEntryConversionDao.get_setting(query_db, user_id)
        values = await InternalPowerEntryConversionDao.list_values(query_db, user_id)
        conversion_values = {
            value.entry_name: float(value.attack_power or 0)
            for value in values
            if value.entry_name in INTERNAL_POWER_ENTRY_LIMIT_MAP
        }
        return conversion_values, float(setting.unit_percent if setting else 0)

    @classmethod
    def calculate_entry_stats(
        cls,
        entries: list[Any],
        conversion_values: dict[str, float],
        unit_percent: float,
    ) -> InternalPowerEntryStats:
        total_attack_power = 0.0
        total_attack_percent = 0.0
        for entry in entries or []:
            entry_data = cls.__model_dump(entry)
            entry_name = str((entry_data or {}).get('name') or '').strip()
            limit = INTERNAL_POWER_ENTRY_LIMIT_MAP.get(entry_name)
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

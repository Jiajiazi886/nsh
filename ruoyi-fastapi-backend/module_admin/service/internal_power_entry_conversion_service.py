from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.constants.internal_power_entry_limits import INTERNAL_POWER_ENTRY_LIMITS
from module_admin.dao.internal_power_entry_conversion_dao import InternalPowerEntryConversionDao
from module_admin.entity.do.internal_power_entry_conversion_do import (
    PersonalInternalPowerEntrySetting,
    PersonalInternalPowerEntryValue,
)
from module_admin.entity.vo.internal_power_entry_conversion_vo import (
    InternalPowerEntryConversionModel,
    InternalPowerEntryConversionRowModel,
    InternalPowerEntryConversionSaveModel,
)
from module_admin.entity.vo.internal_power_entry_vo import InternalPowerEntryConfigModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_entry_service import InternalPowerEntryService


class InternalPowerEntryConversionService:
    """
    个人内功词条换算服务层
    """

    @classmethod
    async def get_conversion_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> InternalPowerEntryConversionModel:
        user_id = current_user.user.user_id
        setting = await InternalPowerEntryConversionDao.get_setting(query_db, user_id)
        values = await InternalPowerEntryConversionDao.list_values(query_db, user_id)
        system_entries = await cls.__get_system_entries(query_db)
        return cls.__build_model(setting, values, system_entries)

    @classmethod
    async def save_conversion_services(
        cls,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        payload: InternalPowerEntryConversionSaveModel,
    ) -> InternalPowerEntryConversionModel:
        user_id = current_user.user.user_id
        unit_percent = cls.calculate_unit_percent(payload.base_attack_power, payload.base_percent)
        now = datetime.now()
        incoming = {entry.entry_name: entry for entry in payload.entries}
        system_entries = await cls.__get_system_entries(query_db)
        cls.__assert_known_entries(incoming, {entry.entry_name for entry in system_entries})
        db_values = []
        for system_entry in system_entries:
            entry = incoming.get(system_entry.entry_name)
            attack_power = float(entry.attack_power if entry else 0)
            db_values.append(
                PersonalInternalPowerEntryValue(
                    user_id=user_id,
                    entry_name=system_entry.entry_name,
                    entry_value=0,
                    attack_power=attack_power,
                    create_time=now,
                    update_time=now,
                )
            )
        setting = PersonalInternalPowerEntrySetting(
            user_id=user_id,
            base_attack_power=float(payload.base_attack_power or 0),
            base_percent=float(payload.base_percent or 0),
            unit_percent=unit_percent,
            create_time=now,
            update_time=now,
        )
        await InternalPowerEntryConversionDao.upsert_setting(query_db, setting)
        await InternalPowerEntryConversionDao.replace_values(query_db, user_id, db_values)
        await query_db.commit()
        return cls.__build_model(setting, db_values, system_entries)

    @staticmethod
    def calculate_unit_percent(base_attack_power: float, base_percent: float) -> float:
        base_attack_power = float(base_attack_power or 0)
        base_percent = float(base_percent or 0)
        if base_attack_power <= 0:
            if base_percent > 0:
                raise ServiceException(message='基准进攻能力必须大于0')
            return 0
        return round(base_percent / base_attack_power, 5)

    @classmethod
    def __build_model(
        cls,
        setting: PersonalInternalPowerEntrySetting | None,
        values: list[PersonalInternalPowerEntryValue],
        system_entries: list[InternalPowerEntryConfigModel],
    ) -> InternalPowerEntryConversionModel:
        unit_percent = float(setting.unit_percent if setting else 0)
        value_map = {value.entry_name: value for value in values}
        entries = []
        for system_entry in system_entries:
            value = value_map.get(system_entry.entry_name)
            attack_power = float(value.attack_power if value else 0)
            entries.append(
                InternalPowerEntryConversionRowModel(
                    entryName=system_entry.entry_name,
                    limitText=system_entry.limit_text or '',
                    limitValue=float(system_entry.limit_value or 0),
                    valueType=system_entry.value_type or 'number',
                    entryValue=0,
                    attackPower=attack_power,
                    attackPercent=round(attack_power * unit_percent, 5),
                )
            )
        return InternalPowerEntryConversionModel(
            baseAttackPower=float(setting.base_attack_power if setting else 0),
            basePercent=float(setting.base_percent if setting else 0),
            unitPercent=unit_percent,
            entries=entries,
            updateTime=setting.update_time if setting else None,
        )

    @staticmethod
    async def __get_system_entries(query_db: AsyncSession) -> list[InternalPowerEntryConfigModel]:
        if hasattr(query_db, 'run_sync'):
            return await InternalPowerEntryService.get_personal_enabled_entries_service(query_db)
        return [
            InternalPowerEntryConfigModel(
                entryName=item['entry_name'],
                limitText=item.get('limit_text') or '',
                limitValue=float(item.get('limit_value') or 0),
                valueType=item.get('value_type') or 'number',
                attackPower=float(item.get('attack_power') or 0),
                status='0',
            )
            for item in INTERNAL_POWER_ENTRY_LIMITS
        ]

    @staticmethod
    def __assert_known_entries(entries: dict[str, InternalPowerEntryConversionRowModel], enabled_entry_names: set[str]) -> None:
        invalid_names = [name for name in entries if name not in enabled_entry_names]
        if invalid_names:
            raise ServiceException(message=f'不支持的内功词条：{", ".join(invalid_names)}')

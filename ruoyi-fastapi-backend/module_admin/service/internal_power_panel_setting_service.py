import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.internal_power_panel_setting_dao import InternalPowerPanelSettingDao
from module_admin.entity.do.internal_power_panel_setting_do import PersonalInternalPowerPanelSetting
from module_admin.entity.vo.internal_power_panel_setting_vo import (
    AttackPanelModel,
    InternalPowerPanelSettingModel,
    TargetPanelModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel

DEFAULT_TARGET_PANEL = TargetPanelModel().model_dump()
DEFAULT_ATTACK_PANEL = AttackPanelModel().model_dump()


class InternalPowerPanelSettingService:
    """
    个人内功PVP收益面板设置服务层
    """

    @classmethod
    async def get_setting_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> InternalPowerPanelSettingModel:
        user_id = current_user.user.user_id
        setting = await InternalPowerPanelSettingDao.get_setting(query_db, user_id)
        if setting is None:
            return InternalPowerPanelSettingModel()
        return cls.__build_model(setting)

    @classmethod
    async def save_setting_services(
        cls,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        payload: InternalPowerPanelSettingModel,
    ) -> InternalPowerPanelSettingModel:
        user_id = current_user.user.user_id
        now = datetime.now()
        setting = PersonalInternalPowerPanelSetting(
            user_id=user_id,
            target_panel_json=cls.__json_dumps(payload.target_panel.model_dump()),
            attack_panel_json=cls.__json_dumps(payload.attack_panel.model_dump()),
            create_time=now,
            update_time=now,
        )
        await InternalPowerPanelSettingDao.upsert_setting(query_db, setting)
        await query_db.commit()
        return cls.__build_model(setting)

    @classmethod
    def __build_model(cls, setting: PersonalInternalPowerPanelSetting) -> InternalPowerPanelSettingModel:
        return InternalPowerPanelSettingModel(
            targetPanel=TargetPanelModel(**cls.__json_loads(setting.target_panel_json, DEFAULT_TARGET_PANEL)),
            attackPanel=AttackPanelModel(**cls.__json_loads(setting.attack_panel_json, DEFAULT_ATTACK_PANEL)),
            updateTime=setting.update_time,
        )

    @staticmethod
    def __json_dumps(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def __json_loads(value: str | None, default: dict[str, Any]) -> dict[str, Any]:
        if not value:
            return dict(default)
        try:
            loaded = json.loads(value)
            return loaded if isinstance(loaded, dict) else dict(default)
        except (TypeError, ValueError, json.JSONDecodeError):
            return dict(default)

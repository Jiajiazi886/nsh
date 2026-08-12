import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.dao.personal_defense_calculator_dao import PersonalDefenseCalculatorDao
from module_admin.entity.do.personal_defense_calculator_do import (
    PersonalDefenseCalculatorSetting,
    PersonalPvpAttackPanel,
)
from module_admin.entity.vo.personal_defense_calculator_vo import (
    DefenseCalculatorDefenderModel,
    DefenseCalculatorSettingModel,
    PersonalPvpAttackPanelModel,
    PersonalPvpAttackPanelPayload,
)
from module_admin.entity.vo.user_vo import CurrentUserModel


class PersonalDefenseCalculatorService:
    @classmethod
    async def list_panels_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> list[PersonalPvpAttackPanelModel]:
        panels = await PersonalDefenseCalculatorDao.list_panels(query_db, current_user.user.user_id)
        return [cls._panel_to_model(panel) for panel in panels]

    @classmethod
    async def add_panel_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, payload: PersonalPvpAttackPanelPayload
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        sequence_no = await PersonalDefenseCalculatorDao.get_next_sequence_no(query_db, user_id)
        now = datetime.now()
        panel = PersonalPvpAttackPanel(
            user_id=user_id,
            sequence_no=sequence_no,
            panel_name=f'攻击方面板 {sequence_no}',
            panel_json=cls._json_dumps(payload.model_dump()),
            create_time=now,
            update_time=now,
        )
        await PersonalDefenseCalculatorDao.add_panel(query_db, panel)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='攻击方面板已新增', result=cls._panel_to_model(panel).model_dump(by_alias=True))

    @classmethod
    async def update_panel_services(
        cls,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        panel_id: int,
        payload: PersonalPvpAttackPanelPayload,
    ) -> CrudResponseModel:
        panel = await cls._require_panel(query_db, current_user.user.user_id, panel_id)
        await PersonalDefenseCalculatorDao.update_panel(query_db, panel.panel_id, cls._json_dumps(payload.model_dump()))
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='攻击方面板已保存')

    @classmethod
    async def delete_panel_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, panel_id: int
    ) -> CrudResponseModel:
        panel = await cls._require_panel(query_db, current_user.user.user_id, panel_id)
        await PersonalDefenseCalculatorDao.delete_panel(query_db, panel.panel_id)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='攻击方面板已删除')

    @classmethod
    async def get_setting_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel
    ) -> DefenseCalculatorSettingModel:
        setting = await PersonalDefenseCalculatorDao.get_setting(query_db, current_user.user.user_id)
        if setting is None:
            return DefenseCalculatorSettingModel()
        stored = cls._json_loads(setting.defender_json)
        is_versioned = isinstance(stored.get('defender'), dict)
        defender = stored.get('defender', stored)
        selected_power_ids = stored.get('selectedInternalPowerIds', []) if is_versioned else []
        selected_power_ids = await PersonalDefenseCalculatorDao.filter_owned_internal_power_ids(
            query_db, current_user.user.user_id, cls._normalize_ids(selected_power_ids)
        )
        return DefenseCalculatorSettingModel(
            defender=DefenseCalculatorDefenderModel(**defender),
            selectedPanelSource=setting.selected_panel_source if setting.selected_panel_source in {'system', 'personal'} else 'system',
            selectedPanelId=setting.selected_panel_id or 0,
            professionId=stored.get('professionId', 0) if is_versioned else 0,
            professionName=stored.get('professionName', '') if is_versioned else '',
            professionOverrides=stored.get('professionOverrides', {}) if is_versioned else {},
            selectedInternalPowerIds=selected_power_ids,
            recommendationInputs=stored.get('recommendationInputs', {}) if is_versioned else {},
            updateTime=setting.update_time,
        )

    @classmethod
    async def save_setting_services(
        cls,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        payload: DefenseCalculatorSettingModel,
    ) -> DefenseCalculatorSettingModel:
        user_id = current_user.user.user_id
        if payload.selected_panel_source == 'personal' and payload.selected_panel_id:
            await cls._require_panel(query_db, user_id, payload.selected_panel_id)
        payload.selected_internal_power_ids = await PersonalDefenseCalculatorDao.filter_owned_internal_power_ids(
            query_db, user_id, cls._normalize_ids(payload.selected_internal_power_ids)
        )
        now = datetime.now()
        stored = {
            'version': 2,
            'defender': payload.defender.model_dump(),
            'professionId': payload.profession_id,
            'professionName': payload.profession_name,
            'professionOverrides': {
                key: value.model_dump() for key, value in payload.profession_overrides.items()
            },
            'selectedInternalPowerIds': payload.selected_internal_power_ids,
            'recommendationInputs': payload.recommendation_inputs,
        }
        setting = PersonalDefenseCalculatorSetting(
            user_id=user_id,
            defender_json=cls._json_dumps(stored),
            selected_panel_source=payload.selected_panel_source,
            selected_panel_id=payload.selected_panel_id,
            create_time=now,
            update_time=now,
        )
        await PersonalDefenseCalculatorDao.upsert_setting(query_db, setting)
        await query_db.commit()
        return await cls.get_setting_services(query_db, current_user)

    @classmethod
    async def _require_panel(cls, db: AsyncSession, user_id: int, panel_id: int) -> PersonalPvpAttackPanel:
        panel = await PersonalDefenseCalculatorDao.get_panel(db, user_id, panel_id)
        if panel is None:
            raise ServiceException(message='攻击方面板不存在或无权操作')
        return panel

    @classmethod
    def _panel_to_model(cls, panel: PersonalPvpAttackPanel) -> PersonalPvpAttackPanelModel:
        return PersonalPvpAttackPanelModel(
            panelId=panel.panel_id,
            sequenceNo=panel.sequence_no,
            panelName=panel.panel_name,
            createTime=panel.create_time,
            updateTime=panel.update_time,
            **cls._json_loads(panel.panel_json),
        )

    @staticmethod
    def _json_dumps(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _json_loads(value: str | None) -> dict[str, Any]:
        try:
            result = json.loads(value or '{}')
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return result if isinstance(result, dict) else {}

    @staticmethod
    def _normalize_ids(values: Any) -> list[int]:
        result = []
        for value in values if isinstance(values, list) else []:
            try:
                normalized = int(value)
            except (TypeError, ValueError):
                continue
            if normalized > 0 and normalized not in result:
                result.append(normalized)
            if len(result) == 6:
                break
        return result

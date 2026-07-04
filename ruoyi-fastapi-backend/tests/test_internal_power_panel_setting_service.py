import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from module_admin.entity.vo.internal_power_panel_setting_vo import (
    AttackPanelModel,
    InternalPowerPanelSettingModel,
)
from module_admin.service.internal_power_panel_setting_service import (
    DEFAULT_ATTACK_PANEL,
    DEFAULT_TARGET_PANEL,
    InternalPowerPanelSettingService,
)


class FakeDb:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True


def make_user(user_id):
    return SimpleNamespace(user=SimpleNamespace(user_id=user_id))


@pytest.mark.asyncio
async def test_get_panel_setting_returns_defaults_when_missing(monkeypatch):
    async def fake_get_setting(db, user_id):
        return None

    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_setting_service.InternalPowerPanelSettingDao.get_setting',
        fake_get_setting,
    )

    result = await InternalPowerPanelSettingService.get_setting_services(FakeDb(), make_user(100))

    assert result.target_panel.model_dump() == DEFAULT_TARGET_PANEL
    assert result.attack_panel.model_dump() == DEFAULT_ATTACK_PANEL
    assert result.update_time is None


@pytest.mark.asyncio
async def test_save_panel_setting_keeps_users_isolated(monkeypatch):
    saved = {}

    async def fake_upsert_setting(db, setting):
        saved[setting.user_id] = setting

    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_setting_service.InternalPowerPanelSettingDao.upsert_setting',
        fake_upsert_setting,
    )

    payload = InternalPowerPanelSettingModel()
    payload.attack_panel.attack = 1888

    db = FakeDb()
    await InternalPowerPanelSettingService.save_setting_services(db, make_user(1), payload)
    await InternalPowerPanelSettingService.save_setting_services(db, make_user(2), payload)

    assert set(saved) == {1, 2}
    assert saved[1].user_id == 1
    assert saved[2].user_id == 2
    assert json.loads(saved[1].attack_panel_json)['attack'] == 1888
    assert db.committed is True


def test_panel_setting_rejects_negative_numbers():
    with pytest.raises(ValidationError):
        AttackPanelModel(attack=-1)

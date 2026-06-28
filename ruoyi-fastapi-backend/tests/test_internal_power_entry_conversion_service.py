from types import SimpleNamespace

import pytest

from module_admin.constants.internal_power_entry_limits import INTERNAL_POWER_ENTRY_LIMITS
from module_admin.entity.vo.internal_power_entry_conversion_vo import (
    InternalPowerEntryConversionRowModel,
    InternalPowerEntryConversionSaveModel,
)
from module_admin.service.internal_power_entry_conversion_service import InternalPowerEntryConversionService


class FakeDb:
    async def commit(self):
        return None


def make_user(user_id):
    return SimpleNamespace(user=SimpleNamespace(user_id=user_id))


def test_internal_power_entry_limits_exclude_lingyun():
    names = [item['entry_name'] for item in INTERNAL_POWER_ENTRY_LIMITS]

    assert len(names) == 21
    assert '灵韵' not in names
    assert names[:3] == ['攻击', '力量/气海', '赛年伤害/治疗提高']


def test_unit_percent_rounds_to_five_decimals():
    unit_percent = InternalPowerEntryConversionService.calculate_unit_percent(477, 7.4)

    assert unit_percent == 0.01551
    assert round(365 * unit_percent, 5) == 5.66115


@pytest.mark.asyncio
async def test_save_conversion_keeps_user_values_isolated(monkeypatch):
    saved = {}

    async def fake_upsert_setting(db, setting):
        saved.setdefault(setting.user_id, {})['setting'] = setting

    async def fake_replace_values(db, user_id, values):
        saved.setdefault(user_id, {})['values'] = values

    monkeypatch.setattr(
        'module_admin.service.internal_power_entry_conversion_service.InternalPowerEntryConversionDao.upsert_setting',
        fake_upsert_setting,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_entry_conversion_service.InternalPowerEntryConversionDao.replace_values',
        fake_replace_values,
    )

    payload = InternalPowerEntryConversionSaveModel(
        baseAttackPower=477,
        basePercent=7.4,
        entries=[
            InternalPowerEntryConversionRowModel(
                entryName='攻击',
                limitText='33',
                limitValue=33,
                valueType='number',
                entryValue=33,
                attackPower=225,
                attackPercent=0,
            )
        ],
    )

    await InternalPowerEntryConversionService.save_conversion_services(FakeDb(), make_user(1), payload)
    await InternalPowerEntryConversionService.save_conversion_services(FakeDb(), make_user(2), payload)

    assert set(saved) == {1, 2}
    assert saved[1]['setting'].unit_percent == 0.01551
    assert saved[2]['setting'].unit_percent == 0.01551
    assert saved[1]['values'][0].user_id == 1
    assert saved[2]['values'][0].user_id == 2


@pytest.mark.asyncio
async def test_save_conversion_ignores_legacy_entry_value_and_allows_zero_attack_power(monkeypatch):
    saved = {}

    async def fake_upsert_setting(db, setting):
        return None

    async def fake_replace_values(db, user_id, values):
        saved[user_id] = values

    monkeypatch.setattr(
        'module_admin.service.internal_power_entry_conversion_service.InternalPowerEntryConversionDao.upsert_setting',
        fake_upsert_setting,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_entry_conversion_service.InternalPowerEntryConversionDao.replace_values',
        fake_replace_values,
    )
    payload = InternalPowerEntryConversionSaveModel(
        baseAttackPower=477,
        basePercent=7.4,
        entries=[
            InternalPowerEntryConversionRowModel(
                entryName='攻击',
                limitText='33',
                limitValue=33,
                valueType='number',
                entryValue=999,
                attackPower=0,
                attackPercent=0,
            )
        ],
    )

    await InternalPowerEntryConversionService.save_conversion_services(FakeDb(), make_user(1), payload)

    attack_row = next(item for item in saved[1] if item.entry_name == '攻击')
    assert attack_row.entry_value == 0
    assert attack_row.attack_power == 0

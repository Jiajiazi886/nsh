import asyncio
from types import SimpleNamespace

from exceptions.exception import ServiceException
from module_admin.entity.vo.personal_defense_calculator_vo import (
    DefenseCalculatorSettingModel,
    PersonalPvpAttackPanelPayload,
    ProfessionBonusOverrideModel,
)
from module_admin.service.personal_defense_calculator_service import PersonalDefenseCalculatorService


def make_user(user_id: int):
    return SimpleNamespace(user=SimpleNamespace(user_id=user_id))


class FakeDb:
    def __init__(self):
        self.commit_count = 0

    async def commit(self):
        self.commit_count += 1


def test_add_personal_panel_generates_user_sequence_name(monkeypatch):
    db = FakeDb()
    converted_before_commit = {'value': False}

    async def fake_get_next_sequence_no(cls, db_arg, user_id):
        assert user_id == 8
        return 3

    async def fake_add_panel(cls, db_arg, panel):
        panel.panel_id = 91
        return panel

    original_to_model = PersonalDefenseCalculatorService._panel_to_model.__func__

    def fake_to_model(cls, panel):
        assert db.commit_count == 0, '新增返回数据必须在 commit 前构造，避免 ORM 对象过期后触发隐式 IO'
        converted_before_commit['value'] = True
        return original_to_model(cls, panel)

    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.get_next_sequence_no',
        classmethod(fake_get_next_sequence_no),
    )
    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.add_panel',
        classmethod(fake_add_panel),
    )
    monkeypatch.setattr(PersonalDefenseCalculatorService, '_panel_to_model', classmethod(fake_to_model))

    result = asyncio.run(PersonalDefenseCalculatorService.add_panel_services(
        db, make_user(8), PersonalPvpAttackPanelPayload(attack=2300)
    ))

    assert db.commit_count == 1
    assert converted_before_commit['value'] is True
    assert result.result['panelName'] == '攻击方面板 3'
    assert result.result['sequenceNo'] == 3
    assert result.result['attack'] == 2300


def test_personal_panel_lookup_is_scoped_to_current_user(monkeypatch):
    captured = {}

    async def fake_get_panel(cls, db_arg, user_id, panel_id):
        captured.update(user_id=user_id, panel_id=panel_id)
        return None

    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.get_panel',
        classmethod(fake_get_panel),
    )

    try:
        asyncio.run(PersonalDefenseCalculatorService._require_panel(FakeDb(), 12, 88))
    except ServiceException:
        pass
    else:
        raise AssertionError('跨用户查询必须被拒绝')

    assert captured == {'user_id': 12, 'panel_id': 88}


def test_personal_selection_must_belong_to_current_user(monkeypatch):
    db = FakeDb()
    captured = {}

    async def fake_require_panel(cls, db_arg, user_id, panel_id):
        captured.update(user_id=user_id, panel_id=panel_id)
        return SimpleNamespace(panel_id=panel_id)

    async def fake_upsert_setting(cls, db_arg, setting):
        captured['setting'] = setting

    async def fake_get_setting_services(cls, db_arg, current_user):
        return DefenseCalculatorSettingModel(selectedPanelSource='personal', selectedPanelId=17)

    monkeypatch.setattr(PersonalDefenseCalculatorService, '_require_panel', classmethod(fake_require_panel))
    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.upsert_setting',
        classmethod(fake_upsert_setting),
    )
    monkeypatch.setattr(PersonalDefenseCalculatorService, 'get_setting_services', classmethod(fake_get_setting_services))

    result = asyncio.run(PersonalDefenseCalculatorService.save_setting_services(
        db,
        make_user(4),
        DefenseCalculatorSettingModel(selectedPanelSource='personal', selectedPanelId=17),
    ))

    assert db.commit_count == 1
    assert captured['user_id'] == 4
    assert captured['panel_id'] == 17
    assert captured['setting'].selected_panel_source == 'personal'
    assert result.selected_panel_id == 17


def test_setting_round_trip_keeps_profession_and_internal_power_selection(monkeypatch):
    db = FakeDb()
    captured = {}

    async def fake_upsert_setting(cls, db_arg, setting):
        captured['setting'] = setting

    async def fake_get_setting(cls, db_arg, user_id):
        return captured['setting']

    async def fake_filter_power_ids(cls, db_arg, user_id, power_ids):
        assert user_id == 4
        assert power_ids == [11, 12]
        return [11, 12]

    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.upsert_setting',
        classmethod(fake_upsert_setting),
    )
    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.get_setting',
        classmethod(fake_get_setting),
    )
    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.filter_owned_internal_power_ids',
        classmethod(fake_filter_power_ids),
    )

    payload = DefenseCalculatorSettingModel(
        professionId=9,
        professionName='铁衣',
        professionOverrides={
            '9': ProfessionBonusOverrideModel(defenseBonusPct=25, hpBonusPct=45),
        },
        selectedInternalPowerIds=[11, 12],
        recommendationInputs={'defense': 10, 'hp': 1000},
        afterDefenderOverride={'defense': 3200, 'hp': 110000},
        afterDefenderAutoBaseline={'defense': 3000, 'hp': 108000},
    )
    result = asyncio.run(PersonalDefenseCalculatorService.save_setting_services(db, make_user(4), payload))

    assert db.commit_count == 1
    assert result.profession_id == 9
    assert result.profession_name == '铁衣'
    assert result.selected_internal_power_ids == [11, 12]
    assert result.profession_overrides['9'].defense_bonus_pct == 25
    assert result.recommendation_inputs['hp'] == 1000
    assert result.after_defender_override.defense == 3200
    assert result.after_defender_auto_baseline.defense == 3000


def test_legacy_flat_defender_setting_is_still_readable(monkeypatch):
    legacy = SimpleNamespace(
        defender_json='{"defense": 3333, "hp": 88888}',
        selected_panel_source='system',
        selected_panel_id=0,
        update_time=None,
    )

    async def fake_get_setting(cls, db_arg, user_id):
        return legacy

    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.get_setting',
        classmethod(fake_get_setting),
    )

    result = asyncio.run(PersonalDefenseCalculatorService.get_setting_services(FakeDb(), make_user(4)))
    assert result.defender.defense == 3333
    assert result.defender.hp == 88888
    assert result.profession_id == 0


def test_setting_round_trip_keeps_manual_after_defender(monkeypatch):
    db = FakeDb()
    captured = {}

    async def fake_upsert_setting(cls, db_arg, setting):
        captured['setting'] = setting

    async def fake_get_setting(cls, db_arg, user_id):
        return captured['setting']

    async def fake_filter_power_ids(cls, db_arg, user_id, power_ids):
        return []

    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.upsert_setting',
        classmethod(fake_upsert_setting),
    )
    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.get_setting',
        classmethod(fake_get_setting),
    )
    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.filter_owned_internal_power_ids',
        classmethod(fake_filter_power_ids),
    )

    payload = DefenseCalculatorSettingModel(
        afterDefenderOverride={
            'defense': 3200,
            'hp': 120000,
            'internalReduction': 1.5,
            'otherReduction': 2.25,
        },
        afterDefenderAutoBaseline={'defense': 3000, 'hp': 115000},
    )
    result = asyncio.run(PersonalDefenseCalculatorService.save_setting_services(db, make_user(4), payload))

    stored = PersonalDefenseCalculatorService._json_loads(captured['setting'].defender_json)
    assert stored['version'] == 3
    assert stored['afterDefenderOverride']['defense'] == 3200
    assert stored['afterDefenderOverride']['internal_reduction'] == 1.5
    assert result.after_defender_override.other_reduction == 2.25
    assert result.after_defender_auto_baseline.defense == 3000

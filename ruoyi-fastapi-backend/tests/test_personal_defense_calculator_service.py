import asyncio
from types import SimpleNamespace

from exceptions.exception import ServiceException
from module_admin.entity.vo.personal_defense_calculator_vo import (
    DefenseCalculatorSettingModel,
    PersonalPvpAttackPanelPayload,
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

    async def fake_get_next_sequence_no(cls, db_arg, user_id):
        assert user_id == 8
        return 3

    async def fake_add_panel(cls, db_arg, panel):
        panel.panel_id = 91
        return panel

    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.get_next_sequence_no',
        classmethod(fake_get_next_sequence_no),
    )
    monkeypatch.setattr(
        'module_admin.service.personal_defense_calculator_service.PersonalDefenseCalculatorDao.add_panel',
        classmethod(fake_add_panel),
    )

    result = asyncio.run(PersonalDefenseCalculatorService.add_panel_services(
        db, make_user(8), PersonalPvpAttackPanelPayload(attack=2300)
    ))

    assert db.commit_count == 1
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

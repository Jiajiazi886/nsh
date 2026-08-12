import asyncio
from types import SimpleNamespace

from module_admin.entity.vo.pvp_defense_profession_bonus_vo import ProfessionBonusUpdateModel
from module_admin.service.pvp_defense_profession_bonus_service import PvpDefenseProfessionBonusService


class FakeDb:
    def __init__(self):
        self.commit_count = 0

    async def commit(self):
        self.commit_count += 1


def test_list_fills_ironclad_defaults_and_zero_for_other_professions(monkeypatch):
    async def fake_professions(db):
        return [
            SimpleNamespace(profession_id=9, profession_name='铁衣', order_num=1),
            SimpleNamespace(profession_id=7, profession_name='素问', order_num=2),
        ]

    async def fake_bonuses(cls, db):
        return []

    monkeypatch.setattr(
        'module_admin.service.pvp_defense_profession_bonus_service.ProfessionDao.get_enabled_profession_list',
        fake_professions,
    )
    monkeypatch.setattr(
        'module_admin.service.pvp_defense_profession_bonus_service.PvpDefenseProfessionBonusDao.list_all',
        classmethod(fake_bonuses),
    )

    result = asyncio.run(PvpDefenseProfessionBonusService.list_services(FakeDb()))
    assert result[0].profession_name == '铁衣'
    assert result[0].defense_bonus_pct == 20
    assert result[0].hp_bonus_pct == 40
    assert result[1].defense_bonus_pct == 0
    assert result[1].hp_bonus_pct == 0


def test_update_upserts_bonus(monkeypatch):
    db = FakeDb()
    captured = {}

    async def fake_profession(db_arg, profession_id):
        return SimpleNamespace(profession_id=profession_id, profession_name='铁衣')

    async def fake_upsert(cls, db_arg, bonus):
        captured['bonus'] = bonus

    monkeypatch.setattr(
        'module_admin.service.pvp_defense_profession_bonus_service.ProfessionDao.get_profession_detail_by_id',
        fake_profession,
    )
    monkeypatch.setattr(
        'module_admin.service.pvp_defense_profession_bonus_service.PvpDefenseProfessionBonusDao.upsert',
        classmethod(fake_upsert),
    )

    asyncio.run(PvpDefenseProfessionBonusService.update_services(
        db,
        9,
        ProfessionBonusUpdateModel(defenseBonusPct=20, hpBonusPct=40),
        'admin',
    ))
    assert db.commit_count == 1
    assert captured['bonus'].defense_bonus_pct == 20
    assert captured['bonus'].hp_bonus_pct == 40

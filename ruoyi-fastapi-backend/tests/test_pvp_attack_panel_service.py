import asyncio

from module_admin.entity.vo.pvp_attack_panel_vo import PvpAttackPanelModel
from module_admin.service.pvp_attack_panel_service import PvpAttackPanelService


class ExpiringPanel:
    def __init__(self, db, **values):
        self._db = db
        self._panel_id = None
        self.__dict__.update(values)

    @property
    def panel_id(self):
        if self._db.committed:
            raise RuntimeError('simulated MissingGreenlet: expired ORM attribute read after commit')
        return self._panel_id

    @panel_id.setter
    def panel_id(self, value):
        self._panel_id = value


class ExpiringDb:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True


def test_add_system_panel_does_not_read_expired_orm_after_commit(monkeypatch):
    db = ExpiringDb()

    def fake_panel_factory(**values):
        return ExpiringPanel(db, **values)

    async def fake_add(cls, db_arg, panel):
        panel.panel_id = 73
        return panel

    monkeypatch.setattr(
        'module_admin.service.pvp_attack_panel_service.SystemPvpAttackPanel',
        fake_panel_factory,
    )
    monkeypatch.setattr(
        'module_admin.service.pvp_attack_panel_service.PvpAttackPanelDao.add',
        classmethod(fake_add),
    )

    result = asyncio.run(
        PvpAttackPanelService.add_services(
            db,
            PvpAttackPanelModel(panelName='联赛标准面板', attack=2200),
            'admin',
        )
    )

    assert db.committed is True
    assert result.result == {'panelId': 73}

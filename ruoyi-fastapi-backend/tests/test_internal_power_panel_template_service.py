import json
from types import SimpleNamespace

import pytest

from module_admin.entity.vo.internal_power_panel_setting_vo import (
    AttackPanelModel,
    InternalPowerPanelTemplateModel,
    TargetPanelModel,
)
from module_admin.service.internal_power_panel_template_service import InternalPowerPanelTemplateService


class FakeDb:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_add_template_saves_whole_attack_and_target_panels(monkeypatch):
    saved = {}

    async def fake_add(db, template):
        template.template_id = 9
        saved['template'] = template
        return template

    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_template_service.InternalPowerPanelTemplateDao.add',
        fake_add,
    )

    payload = InternalPowerPanelTemplateModel(
        templateName='默认PVP模板',
        targetPanel=TargetPanelModel(defense=2710, resist_pct=0.012),
        attackPanel=AttackPanelModel(attack=1665, crit_dmg=0.42, restraint_pct=0.051),
    )
    db = FakeDb()

    result = await InternalPowerPanelTemplateService.add_template_services(db, payload, 'admin')

    assert result.result == {'templateId': 9}
    assert db.committed is True
    target = json.loads(saved['template'].target_panel_json)
    attack = json.loads(saved['template'].attack_panel_json)
    assert target['defense'] == 2710
    assert target['resist_pct'] == 0.012
    assert attack['attack'] == 1665
    assert attack['crit_dmg'] == 0.42
    assert attack['restraint_pct'] == 0.051


@pytest.mark.asyncio
async def test_template_detail_rejects_missing_template(monkeypatch):
    async def fake_get_by_id(db, template_id):
        return None

    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_template_service.InternalPowerPanelTemplateDao.get_by_id',
        fake_get_by_id,
    )

    with pytest.raises(Exception) as exc_info:
        await InternalPowerPanelTemplateService.template_detail_services(SimpleNamespace(), 404)

    assert exc_info.value.message == '面板模板不存在'

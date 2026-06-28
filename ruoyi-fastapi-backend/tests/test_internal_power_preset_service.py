from types import SimpleNamespace

import pytest

from module_admin.constants.internal_power_presets import DEFAULT_INTERNAL_POWER_PRESETS
from module_admin.service.internal_power_preset_service import InternalPowerPresetService


def test_default_internal_power_presets_use_required_element_counts():
    presets = {f'{item["name"]}:{item["element_key"]}': item for item in DEFAULT_INTERNAL_POWER_PRESETS}

    assert presets['破釜:metal']['elements'] == {'metal': 4, 'wood': 0, 'water': 0, 'fire': 0, 'earth': 0}
    assert presets['破釜:metal']['image_url'] == '/neigong/01_破釜_金.png'
    assert presets['稀有-灼星贯日:fire']['elements'] == {
        'metal': 0,
        'wood': 0,
        'water': 0,
        'fire': 4,
        'earth': 0,
    }
    assert presets['五韵谣:mixed']['elements'] == {'metal': 1, 'wood': 1, 'water': 1, 'fire': 1, 'earth': 1}


@pytest.mark.asyncio
async def test_personal_preset_list_returns_enabled_presets_only(monkeypatch):
    rows = [
        SimpleNamespace(
            preset_id=1,
            name='破釜',
            element_key='metal',
            elements_json='{"metal":4,"wood":0,"water":0,"fire":0,"earth":0}',
            bonus_percent=0,
            bonus_type='',
            bonus_desc='',
            image_url='/neigong/01_破釜_金.png',
            entries_json='[]',
            status='0',
            remark='',
            create_time=None,
            update_time=None,
        ),
        SimpleNamespace(
            preset_id=2,
            name='停用内功',
            element_key='fire',
            elements_json='{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}',
            bonus_percent=0,
            bonus_type='',
            bonus_desc='',
            image_url='',
            entries_json='[]',
            status='1',
            remark='',
            create_time=None,
            update_time=None,
        ),
    ]

    async def fake_list_enabled(db):
        return [row for row in rows if row.status == '0']

    monkeypatch.setattr(
        'module_admin.service.internal_power_preset_service.InternalPowerPresetDao.list_enabled',
        fake_list_enabled,
    )

    result = await InternalPowerPresetService.get_personal_enabled_presets_service(None)

    assert [item.name for item in result] == ['破釜']
    assert result[0].display_name == '破釜（金）'
    assert result[0].image_url == '/neigong/01_破釜_金.png'
    assert result[0].elements.metal == 4

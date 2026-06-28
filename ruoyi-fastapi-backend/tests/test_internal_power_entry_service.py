from types import SimpleNamespace

import pytest

from exceptions.exception import ServiceException
from module_admin.constants.internal_power_entries import DEFAULT_INTERNAL_POWER_ENTRIES
from module_admin.entity.vo.internal_power_vo import InternalPowerEntryModel
from module_admin.service.internal_power_entry_service import InternalPowerEntryService
from module_admin.service.internal_power_service import InternalPowerService


def test_default_internal_power_entries_seed_required_names():
    names = [item['entry_name'] for item in DEFAULT_INTERNAL_POWER_ENTRIES]

    assert len(names) == 22
    assert names[:3] == ['攻击', '力量/气海', '赛年伤害/治疗提高']
    assert names[-1] == '灵韵'
    assert len(set(names)) == len(names)
    assert all(item['conversion_percent'] is None for item in DEFAULT_INTERNAL_POWER_ENTRIES)


@pytest.mark.asyncio
async def test_personal_entry_list_returns_enabled_entries_only(monkeypatch):
    rows = [
        SimpleNamespace(
            entry_id=1,
            entry_name='攻击',
            conversion_percent=None,
            conversion_desc='',
            status='0',
            remark='',
            create_time=None,
            update_time=None,
        ),
        SimpleNamespace(
            entry_id=2,
            entry_name='停用词条',
            conversion_percent=None,
            conversion_desc='',
            status='1',
            remark='',
            create_time=None,
            update_time=None,
        ),
    ]

    async def fake_list_enabled(db):
        return [row for row in rows if row.status == '0']

    monkeypatch.setattr(
        'module_admin.service.internal_power_entry_service.InternalPowerEntryDao.list_enabled',
        fake_list_enabled,
    )

    result = await InternalPowerEntryService.get_personal_enabled_entries_service(None)

    assert [item.entry_name for item in result] == ['攻击']
    assert result[0].conversion_percent is None


@pytest.mark.asyncio
async def test_internal_power_save_rejects_non_builtin_entry(monkeypatch):
    async def fake_get_enabled_entry_names_service(db):
        return {'攻击', '会心'}

    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerEntryService.get_enabled_entry_names_service',
        fake_get_enabled_entry_names_service,
    )

    with pytest.raises(ServiceException):
        await InternalPowerService._InternalPowerService__assert_valid_entries(
            None,
            [InternalPowerEntryModel(name='不存在的词条', value='123')],
        )

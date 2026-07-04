import json
from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import DataError

from exceptions.exception import ServiceException
from module_admin.entity.vo.damage_formula_version_vo import DamageFormulaVersionModel
from module_admin.entity.do.damage_formula_version_do import SystemDamageFormulaVersion
from module_admin.entity.vo.damage_formula_version_vo import FORMULA_SCOPE_INTERNAL_POWER_PVP
from module_admin.service.damage_formula_version_service import DamageFormulaVersionService


class FakeDb:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def make_package(**overrides):
    package = {
        'scope': FORMULA_SCOPE_INTERNAL_POWER_PVP,
        'defaults': {
            'targetPanel': {'defense': 2550},
            'attackPanel': {'attack': 1750},
            'emptyDelta': {'attack': 0},
        },
        'fields': {'target': [], 'attack': [], 'manual': []},
        'fixedCells': [],
        'entryRules': [],
        'benefitPresets': [],
        'workbookData': {'sheets': {}},
        'formulas': {'属性输入!D29': 'G("属性输入","B29")+1'},
        'outputs': {'sheet': '属性输入', 'damage': 'D29'},
    }
    package.update(overrides)
    return package


def make_version(version_id=1, status='draft', package=None):
    return SystemDamageFormulaVersion(
        version_id=version_id,
        version_name='测试公式',
        formula_scope=FORMULA_SCOPE_INTERNAL_POWER_PVP,
        status=status,
        formula_package_json=json.dumps(package or make_package(), ensure_ascii=False),
        remark='',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


@pytest.mark.asyncio
async def test_active_version_returns_builtin_when_missing(monkeypatch):
    async def fake_get_published(db, scope):
        return None

    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.get_published',
        fake_get_published,
    )

    result = await DamageFormulaVersionService.get_active_version_services(FakeDb())

    assert result.version_id == 0
    assert result.status == 'published'
    assert result.formula_package['builtin'] is True


@pytest.mark.asyncio
async def test_publish_archives_existing_and_marks_selected_published(monkeypatch):
    calls = []

    async def fake_get_by_id(db, version_id):
        return make_version(version_id=version_id)

    async def fake_archive(db, scope, exclude_version_id=None):
        calls.append(('archive', scope, exclude_version_id))

    async def fake_update(db, values):
        calls.append(('update', values['version_id'], values['status']))

    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.get_by_id',
        fake_get_by_id,
    )
    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.archive_published',
        fake_archive,
    )
    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.update',
        fake_update,
    )

    db = FakeDb()
    result = await DamageFormulaVersionService.publish_version_services(db, 7, 'admin')

    assert result.is_success is True
    assert ('archive', FORMULA_SCOPE_INTERNAL_POWER_PVP, 7) in calls
    assert ('update', 7, 'published') in calls
    assert db.committed is True


@pytest.mark.asyncio
async def test_publish_rejects_unsafe_formula(monkeypatch):
    unsafe = make_package(formulas={'属性输入!D29': 'this.constructor.constructor("alert(1)")()'})

    async def fake_get_by_id(db, version_id):
        return make_version(version_id=version_id, package=unsafe)

    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.get_by_id',
        fake_get_by_id,
    )

    with pytest.raises(ServiceException):
        await DamageFormulaVersionService.publish_version_services(FakeDb(), 1, 'admin')


@pytest.mark.asyncio
async def test_add_version_converts_formula_package_too_long_error(monkeypatch):
    async def fake_add(db, version):
        raise DataError(
            'INSERT INTO system_damage_formula_version (formula_package_json) VALUES (%s)',
            {},
            Exception("1406 Data too long for column 'formula_package_json' at row 1"),
        )

    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.add',
        fake_add,
    )

    db = FakeDb()
    payload = DamageFormulaVersionModel(versionName='超长公式包', formulaPackage=make_package())

    with pytest.raises(ServiceException) as exc_info:
        await DamageFormulaVersionService.add_version_services(db, payload, 'admin')

    assert 'LONGTEXT' in exc_info.value.message
    assert db.rolled_back is True
    assert db.committed is False


@pytest.mark.asyncio
async def test_rollback_creates_new_published_version(monkeypatch):
    added = []
    archived = []

    async def fake_get_by_id(db, version_id):
        return make_version(version_id=version_id, status='archived')

    async def fake_archive(db, scope, exclude_version_id=None):
        archived.append((scope, exclude_version_id))

    async def fake_add(db, version):
        version.version_id = 22
        added.append(version)
        return version

    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.get_by_id',
        fake_get_by_id,
    )
    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.archive_published',
        fake_archive,
    )
    monkeypatch.setattr(
        'module_admin.service.damage_formula_version_service.DamageFormulaVersionDao.add',
        fake_add,
    )

    db = FakeDb()
    result = await DamageFormulaVersionService.rollback_version_services(db, 3, 'admin')

    assert result.result == {'versionId': 22}
    assert archived == [(FORMULA_SCOPE_INTERNAL_POWER_PVP, None)]
    assert added[0].status == 'published'
    assert db.committed is True

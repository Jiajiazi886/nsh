from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from exceptions.exception import ServiceException
from module_admin.service.internal_power_mimo_service import InternalPowerMimoResult
from module_admin.service.internal_power_panel_recognition_service import InternalPowerPanelRecognitionService


def make_user(user_id=1, roles=None):
    return SimpleNamespace(user=SimpleNamespace(user_id=user_id, user_name='tester'), roles=roles or [])


class FakeDb:
    def __init__(self):
        self.commit_count = 0

    async def commit(self):
        self.commit_count += 1


class ExpiringHistory:
    def __init__(self, db, record_id=77):
        self.db = db
        self._record_id = record_id

    @property
    def record_id(self):
        if self.db.commit_count > 0:
            raise AssertionError('record_id was accessed after commit')
        return self._record_id


class FakeUploadFile:
    filename = 'panel.png'
    content_type = 'image/png'

    async def read(self):
        return b'image-bytes'


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('142.0%', 142.0),
        ('1,665', 1665),
        (None, None),
    ],
)
def test_normalize_panel_json_accepts_number_like_values(source, expected):
    parsed = {
        '攻击': source,
        '破防': 1529,
        '会心': 1301,
        '会心伤害': 142.0,
        '流派克制': 301,
        '流派克制百分比': 5.1,
        '防御': 2710,
        '会心抗性': 911,
        '会心防御': 0,
        '流派抵御': 486,
        '流派抵御百分比': 1.2,
    }

    normalized, error = InternalPowerPanelRecognitionService.normalize_panel_json(parsed)

    assert error == ''
    assert normalized['攻击'] == expected


def test_normalize_panel_json_rejects_missing_fields():
    normalized, error = InternalPowerPanelRecognitionService.normalize_panel_json({'攻击': 1665})

    assert normalized == {}
    assert '识别结果缺少字段' in error


def test_normalize_defense_panel_json_keeps_only_required_five_fields():
    normalized, error = InternalPowerPanelRecognitionService.normalize_defense_panel_json(
        {
            '气血': '88310/91310',
            '防御': 4071,
            '会心抗性': '1,130',
            '流派抵御': 391,
            '流派抵御百分比': '0.0%',
            '会心防御': '0.0%',
        }
    )

    assert error == '气血不是有效整数'
    assert normalized == {}


def test_normalize_defense_panel_json_formats_percent_and_preserves_nulls():
    normalized, error = InternalPowerPanelRecognitionService.normalize_defense_panel_json(
        {
            '气血': 91310,
            '防御': 4071,
            '会心抗性': 1130,
            '流派抵御': 391,
            '流派抵御百分比': 1.2,
            '会心防御': '0.0%',
        }
    )

    assert error == ''
    assert normalized == {
        '气血': 91310,
        '防御': 4071,
        '会心抗性': 1130,
        '流派抵御': 391,
        '流派抵御百分比': '1.2%',
    }


def test_normalize_internal_power_benefit_json_formats_all_supported_entries():
    normalized, error = InternalPowerPanelRecognitionService.normalize_internal_power_benefit_json(
        {
            '耐力': 16,
            '根骨': 21,
            '身法': 10,
            '内功防御': 63,
            '外功防御': 29,
            '防御': 182,
            '气血上限': 14207,
            '抗会心': 241,
            '抗内功会心': 407,
            '抗外功会心': 253,
            '流派抵御': '3.2%',
            '首领抵御': '2.1%',
        }
    )

    assert error == ''
    assert normalized == {
        '耐力': 16,
        '根骨': 21,
        '身法': 10,
        '内功防御': 63,
        '外功防御': 29,
        '防御': 182,
        '气血上限': 14207,
        '抗会心': 241,
        '抗内功会心': 407,
        '抗外功会心': 253,
        '流派抵御': '3.2%',
    }


def test_normalize_internal_power_benefit_json_rejects_missing_fields():
    normalized, error = InternalPowerPanelRecognitionService.normalize_internal_power_benefit_json({'耐力': 16})

    assert normalized == {}
    assert '识别结果缺少字段' in error


@pytest.mark.asyncio
async def test_history_limit_is_5_for_normal_user(monkeypatch):
    captured = {}
    normal_user = SimpleNamespace(
        user_id=1,
        is_vip='0',
        sponsored_vip='0',
        vip_expire_time=datetime.now() - timedelta(days=1),
    )

    async def fake_get_user_detail_by_id(db, user_id):
        return {'user_basic_info': normal_user}

    async def fake_list_by_user_id(db, user_id, limit):
        captured['limit'] = limit
        return []

    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.UserDao.get_user_detail_by_id',
        fake_get_user_detail_by_id,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.InternalPowerPanelRecognitionHistoryDao.list_by_user_id',
        fake_list_by_user_id,
    )

    result = await InternalPowerPanelRecognitionService.get_history_services(SimpleNamespace(), make_user(user_id=2))

    assert captured['limit'] == 5
    assert result.visible_limit == 5


@pytest.mark.asyncio
async def test_history_limit_is_10_for_vip(monkeypatch):
    captured = {}
    vip_user = SimpleNamespace(
        user_id=1,
        is_vip='1',
        sponsored_vip='0',
        vip_expire_time=datetime.now() + timedelta(days=1),
    )

    async def fake_get_user_detail_by_id(db, user_id):
        return {'user_basic_info': vip_user}

    async def fake_list_by_user_id(db, user_id, limit):
        captured['limit'] = limit
        return []

    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.UserDao.get_user_detail_by_id',
        fake_get_user_detail_by_id,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.InternalPowerPanelRecognitionHistoryDao.list_by_user_id',
        fake_list_by_user_id,
    )

    result = await InternalPowerPanelRecognitionService.get_history_services(SimpleNamespace(), make_user())

    assert captured['limit'] == 10
    assert result.visible_limit == 10


@pytest.mark.asyncio
async def test_recognize_uses_cached_history_id_after_initial_commit(monkeypatch):
    db = FakeDb()
    updates = []
    user = SimpleNamespace(
        user_id=1,
        is_vip='0',
        sponsored_vip='0',
        vip_expire_time=datetime.now() - timedelta(days=1),
        ai_image_recognition_count=1,
        vip_ai_image_recognition_count=0,
    )

    async def fake_get_user_detail_by_id(db_arg, user_id):
        return {'user_basic_info': user}

    async def fake_add(db_arg, history):
        return ExpiringHistory(db_arg, record_id=77)

    async def fake_trim(db_arg, user_id):
        return None

    async def fake_recognize(*args, **kwargs):
        return InternalPowerMimoResult(
            parsed={
                '攻击': 1665,
                '破防': 1529,
                '会心': 1301,
                '会心伤害': 142.0,
                '流派克制': 301,
                '流派克制百分比': 5.1,
                '防御': 2710,
                '会心抗性': 911,
                '会心防御': 0,
                '流派抵御': 486,
                '流派抵御百分比': 1.2,
            },
            raw_text='{}',
        )

    async def fake_decrement(*args, **kwargs):
        return True

    async def fake_update(db_arg, record_id, user_id, values):
        updates.append((record_id, values))

    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.UserDao.get_user_detail_by_id',
        fake_get_user_detail_by_id,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.InternalPowerPanelRecognitionHistoryDao.add',
        fake_add,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.InternalPowerPanelRecognitionHistoryDao.trim_by_user_id',
        fake_trim,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.InternalPowerPanelRecognitionHistoryDao.update',
        fake_update,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.InternalPowerMimoService.recognize_image_json',
        fake_recognize,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement,
    )

    result = await InternalPowerPanelRecognitionService.recognize_image_services(db, make_user(), FakeUploadFile())

    assert result.success is True
    assert result.record_id == 77
    assert updates[-1][0] == 77
    assert db.commit_count == 2


@pytest.mark.asyncio
async def test_recognize_does_not_call_ai_when_normal_and_vip_counts_are_empty(monkeypatch):
    db = FakeDb()
    ai_called = False
    user = SimpleNamespace(
        user_id=2,
        ai_image_recognition_count=0,
        vip_ai_image_recognition_count=0,
    )

    async def fake_get_user_detail_by_id(db_arg, user_id):
        return {'user_basic_info': user}

    async def fake_recognize(*args, **kwargs):
        nonlocal ai_called
        ai_called = True
        raise AssertionError('AI must not be called without recognition quota')

    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.UserDao.get_user_detail_by_id',
        fake_get_user_detail_by_id,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_panel_recognition_service.InternalPowerMimoService.recognize_image_json',
        fake_recognize,
    )

    with pytest.raises(ServiceException) as exc_info:
        await InternalPowerPanelRecognitionService.recognize_image_services(
            db,
            make_user(user_id=2),
            FakeUploadFile(),
        )

    assert exc_info.value.message == 'AI识图次数不足，普通剩余0次，VIP剩余0次'
    assert ai_called is False
    assert db.commit_count == 0

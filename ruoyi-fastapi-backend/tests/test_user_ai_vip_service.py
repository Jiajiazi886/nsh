import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from module_admin.controller.user_controller import (
    get_system_user_default_ai_recognition_count,
    get_system_user_vip_ai_recognition_grant_count,
)
from module_admin.entity.vo.user_vo import AddUserModel
from module_admin.service.user_service import UserService


class FakeDb:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


class FakeRedis:
    def __init__(self):
        self.values = {}

    async def set(self, key, value):
        self.values[key] = value


def make_request():
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis=FakeRedis())))


@pytest.mark.asyncio
async def test_default_ai_count_controller_returns_data_payload(monkeypatch):
    async def fake_default_count(db):
        return 8

    monkeypatch.setattr(UserService, 'get_default_ai_recognition_count_services', fake_default_count)

    response = await get_system_user_default_ai_recognition_count(request=make_request(), query_db=FakeDb())
    payload = json.loads(response.body)

    assert payload['code'] == 200
    assert payload['data'] == {'aiImageRecognitionCount': 8}


@pytest.mark.asyncio
async def test_vip_ai_grant_count_controller_returns_data_payload(monkeypatch):
    async def fake_grant_count(db):
        return 12

    monkeypatch.setattr(UserService, 'get_vip_ai_recognition_grant_count_services', fake_grant_count)

    response = await get_system_user_vip_ai_recognition_grant_count(request=make_request(), query_db=FakeDb())
    payload = json.loads(response.body)

    assert payload['code'] == 200
    assert payload['data'] == {'vipAiImageRecognitionGrantCount': 12}


@pytest.mark.asyncio
async def test_set_default_ai_count_creates_config_and_overwrites_old_users(monkeypatch):
    captured = {}

    async def fake_get_config(db, config):
        return None

    async def fake_add_config(db, config):
        captured['config'] = config
        return config

    async def fake_batch_update(db, count, update_by):
        captured['count'] = count
        captured['update_by'] = update_by
        return 3

    monkeypatch.setattr('module_admin.service.user_service.ConfigDao.get_config_detail_by_info', fake_get_config)
    monkeypatch.setattr('module_admin.service.user_service.ConfigDao.add_config_dao', fake_add_config)
    monkeypatch.setattr('module_admin.service.user_service.UserDao.batch_update_normal_ai_count', fake_batch_update)

    request = make_request()
    db = FakeDb()
    result = await UserService.set_default_ai_recognition_count_services(request, db, 6, 'admin')

    assert db.committed is True
    assert captured['config'].config_key == UserService.DEFAULT_AI_RECOGNITION_CONFIG_KEY
    assert captured['config'].config_value == '6'
    assert captured['count'] == 6
    assert captured['update_by'] == 'admin'
    assert '同步3个老用户' in result.message
    assert request.app.state.redis.values[f'sys_config:{UserService.DEFAULT_AI_RECOGNITION_CONFIG_KEY}'] == '6'


@pytest.mark.asyncio
async def test_add_user_uses_default_ai_count_when_not_explicitly_set(monkeypatch):
    saved = {}

    async def fake_default_count(db):
        return 8

    async def fake_unique(db, page_object):
        return True

    async def fake_add_user(db, user):
        saved['user'] = user
        return SimpleNamespace(user_id=22)

    monkeypatch.setattr(UserService, 'get_default_ai_recognition_count_services', fake_default_count)
    monkeypatch.setattr(UserService, 'check_user_name_unique_services', fake_unique)
    monkeypatch.setattr(UserService, 'check_phonenumber_unique_services', fake_unique)
    monkeypatch.setattr(UserService, 'check_email_unique_services', fake_unique)
    monkeypatch.setattr('module_admin.service.user_service.UserDao.add_user_dao', fake_add_user)

    db = FakeDb()
    result = await UserService.add_user_services(
        db,
        AddUserModel(userName='new_user', nickName='新用户', password='abc123', roleIds=[]),
    )

    assert result.is_success is True
    assert db.committed is True
    assert saved['user'].ai_image_recognition_count == 8


@pytest.mark.asyncio
async def test_batch_change_vip_grants_only_users_who_newly_become_vip(monkeypatch):
    changes = []

    async def fake_grant_count(db):
        return 5

    async def fake_user_detail(db, user_id):
        if user_id == 2:
            user = SimpleNamespace(is_vip='0', vip_expire_time=None, sponsored_vip='0')
        else:
            user = SimpleNamespace(
                is_vip='1',
                vip_expire_time=datetime.now() + timedelta(days=1),
                sponsored_vip='0',
            )
        return {'user_basic_info': user}

    async def fake_change_manual_vip(db, user_id, is_vip, expire_time, grant_count, update_by):
        changes.append((user_id, is_vip, expire_time, grant_count, update_by))

    monkeypatch.setattr(UserService, 'get_vip_ai_recognition_grant_count_services', fake_grant_count)
    monkeypatch.setattr('module_admin.service.user_service.UserDao.get_user_detail_by_id', fake_user_detail)
    monkeypatch.setattr('module_admin.service.user_service.UserDao.change_manual_vip', fake_change_manual_vip)

    expire_time = datetime.now() + timedelta(days=7)
    db = FakeDb()
    result = await UserService.batch_change_vip_services(db, [2, 3], '1', expire_time, 'admin')

    assert result.is_success is True
    assert db.committed is True
    assert [change[0] for change in changes] == [2, 3]
    assert [change[3] for change in changes] == [5, 0]
    assert '已向1名新VIP各赠送5次识图次数' in result.message


@pytest.mark.asyncio
async def test_change_vip_grants_once_and_renewal_does_not_repeat(monkeypatch):
    current_user = SimpleNamespace(is_vip='0', vip_expire_time=None, sponsored_vip='0')
    changes = []

    async def fake_user_detail(db, user_id):
        return {'user_basic_info': current_user}

    async def fake_grant_count(db):
        return 9

    async def fake_change_manual_vip(db, user_id, is_vip, expire_time, grant_count, update_by):
        changes.append(grant_count)

    monkeypatch.setattr('module_admin.service.user_service.UserDao.get_user_detail_by_id', fake_user_detail)
    monkeypatch.setattr(UserService, 'get_vip_ai_recognition_grant_count_services', fake_grant_count)
    monkeypatch.setattr('module_admin.service.user_service.UserDao.change_manual_vip', fake_change_manual_vip)

    db = FakeDb()
    expire_time = datetime.now() + timedelta(days=7)
    first_result = await UserService.change_vip_services(db, 2, '1', expire_time, 'admin')
    current_user.is_vip = '1'
    current_user.vip_expire_time = expire_time
    renewal_result = await UserService.change_vip_services(
        db, 2, '1', datetime.now() + timedelta(days=30), 'admin'
    )

    assert changes == [9, 0]
    assert '已赠送9次VIP识图次数' in first_result.message
    assert '赠送' not in renewal_result.message


@pytest.mark.asyncio
async def test_cancel_vip_keeps_recognition_balance_untouched(monkeypatch):
    current_user = SimpleNamespace(
        is_vip='1',
        vip_expire_time=datetime.now() + timedelta(days=7),
        sponsored_vip='0',
    )
    captured = {}

    async def fake_user_detail(db, user_id):
        return {'user_basic_info': current_user}

    async def fake_change_manual_vip(db, user_id, is_vip, expire_time, grant_count, update_by):
        captured.update(is_vip=is_vip, expire_time=expire_time, grant_count=grant_count)

    monkeypatch.setattr('module_admin.service.user_service.UserDao.get_user_detail_by_id', fake_user_detail)
    monkeypatch.setattr('module_admin.service.user_service.UserDao.change_manual_vip', fake_change_manual_vip)

    result = await UserService.change_vip_services(FakeDb(), 2, '0', None, 'admin')

    assert result.is_success is True
    assert captured == {'is_vip': '0', 'expire_time': None, 'grant_count': 0}


@pytest.mark.asyncio
async def test_expire_vip_does_not_clear_recognition_balance():
    class ExecuteResult:
        rowcount = 2

    class CaptureDb(FakeDb):
        def __init__(self):
            super().__init__()
            self.statement = ''

        async def execute(self, statement):
            self.statement = str(statement)
            return ExecuteResult()

    db = CaptureDb()
    expired_count = await UserService.expire_vip_users_services(db)

    assert expired_count == 2
    assert db.committed is True
    assert 'vip_ai_image_recognition_count' not in db.statement

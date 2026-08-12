import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from module_admin.entity.vo.user_vo import AddUserModel
from module_admin.controller.user_controller import get_system_user_default_ai_recognition_count
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
async def test_batch_change_vip_updates_all_selected_users(monkeypatch):
    edits = []

    async def fake_edit_user(db, payload):
        edits.append(payload)

    monkeypatch.setattr('module_admin.service.user_service.UserDao.edit_user_dao', fake_edit_user)

    expire_time = datetime.now() + timedelta(days=7)
    db = FakeDb()
    result = await UserService.batch_change_vip_services(db, [2, 3], '1', expire_time, 5, 'admin')

    assert result.is_success is True
    assert db.committed is True
    assert [edit['user_id'] for edit in edits] == [2, 3]
    assert all(edit['is_vip'] == '1' for edit in edits)
    assert all(edit['vip_expire_time'] == expire_time for edit in edits)
    assert all(edit['vip_ai_image_recognition_count'] == 5 for edit in edits)

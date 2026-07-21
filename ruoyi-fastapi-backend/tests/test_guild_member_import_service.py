from types import SimpleNamespace

import pytest

from module_guild.entity.vo.member_vo import MemberJsonImportItemModel, MemberJsonImportModel
from module_guild.service.member_service import MemberService
from module_guild.service.schedule_service import ScheduleService


class FakeDb:
    def __init__(self):
        self.events = []

    async def commit(self):
        self.events.append(('commit', None))


@pytest.mark.asyncio
async def test_json_member_import_skips_invalid_and_duplicate_records(monkeypatch):
    db = FakeDb()
    created = []

    async def fake_exists(_db, _user_id, player_name):
        return player_name == '已存在'

    async def fake_batch_insert(_db, members):
        created.extend(members)

    monkeypatch.setattr(
        'module_guild.service.member_service.MemberDao.check_member_exists',
        fake_exists,
    )
    monkeypatch.setattr(
        'module_guild.service.member_service.MemberDao.batch_insert_members',
        fake_batch_insert,
    )

    result = await MemberService.import_from_json_service(
        db,
        SimpleNamespace(user=SimpleNamespace(user_id=7)),
        MemberJsonImportModel(members=[
            MemberJsonImportItemModel(player_name=' 张三 ', player_class='铁衣'),
            MemberJsonImportItemModel(player_name='张三', player_class='素问'),
            MemberJsonImportItemModel(player_name='已存在'),
            MemberJsonImportItemModel(player_name=''),
        ]),
    )

    assert created == [{
        'guild_id': 7,
        'user_id': 7,
        'member_user_id': 0,
        'player_name': '张三',
        'player_class': '铁衣',
        'secondary_class': '',
        'is_active': '1',
        'source_type': 'import',
        'remark': '',
    }]
    assert db.events == [('commit', None)]
    assert result.message == '成功导入 1 条成员，跳过 2 条重复成员，忽略 1 条空玩家名记录'


@pytest.mark.asyncio
async def test_excel_workbook_import_replaces_only_current_schedule_structure(monkeypatch):
    db = FakeDb()
    events = []

    async def fake_ensure(_db, _user_id):
        return SimpleNamespace(schedule_id=91)

    async def fake_clear(_db, schedule_id):
        events.append(('clear', schedule_id))

    async def fake_upsert(_db, schedule_id, workbook_json):
        events.append(('save', schedule_id, workbook_json))

    monkeypatch.setattr(ScheduleService, '_ensure_active_schedule', fake_ensure)
    monkeypatch.setattr(
        'module_guild.service.schedule_service.ScheduleDao.clear_schedule_structure',
        fake_clear,
    )
    monkeypatch.setattr(
        'module_guild.service.schedule_service.ScheduleDao.upsert_workbook',
        fake_upsert,
    )

    result = await ScheduleService.import_current_workbook_service(
        db,
        SimpleNamespace(user=SimpleNamespace(user_id=7)),
        SimpleNamespace(workbook={'sheets': {'sheet-1': {'name': '导入表'}}}),
    )

    assert events == [('clear', 91), ('save', 91, '{"sheets":{"sheet-1":{"name":"导入表"}}}')]
    assert db.events == [('commit', None)]
    assert result.message == 'Excel 排表已导入，原有分团结构已清空'

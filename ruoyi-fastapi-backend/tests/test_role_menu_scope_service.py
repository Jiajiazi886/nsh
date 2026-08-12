import asyncio
from types import SimpleNamespace

from module_admin.dao.role_dao import RoleDao
from module_admin.entity.vo.role_vo import AddRoleModel
from module_admin.service.role_service import RoleService


class FakeDb:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def test_role_menu_scope_replaces_menu_links_without_updating_other_role_fields(monkeypatch):
    db = FakeDb()
    updated_roles = []
    deleted_role_ids = []
    inserted_menu_ids = []

    async def role_detail(_db, role_id):
        return SimpleNamespace(role_id=role_id)

    async def edit_role(_db, role):
        updated_roles.append(role)

    async def delete_role_menu(_db, role_menu):
        deleted_role_ids.append(role_menu.role_id)

    async def add_role_menu(_db, role_menu):
        inserted_menu_ids.append(role_menu.menu_id)

    monkeypatch.setattr(RoleService, 'role_detail_services', role_detail)
    monkeypatch.setattr(RoleDao, 'edit_role_dao', edit_role)
    monkeypatch.setattr(RoleDao, 'delete_role_menu_dao', delete_role_menu)
    monkeypatch.setattr(RoleDao, 'add_role_menu_dao', add_role_menu)

    result = asyncio.run(
        RoleService.role_menu_scope_services(
            db,
            AddRoleModel(roleId=2, menuIds=[1, 100, 101, 101], menuCheckStrictly=True, updateBy='admin'),
        )
    )

    assert result.is_success is True
    assert updated_roles == [
        {
            'role_id': 2,
            'menu_check_strictly': True,
            'update_by': 'admin',
            'update_time': None,
        }
    ]
    assert deleted_role_ids == [2]
    assert inserted_menu_ids == [1, 100, 101]
    assert db.committed is True
    assert db.rolled_back is False

from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from config.get_db import get_db
from exceptions.handle import handle_exception
from module_integration.controller.license_controller import license_controller


def build_app(auth_state):
    app = FastAPI()
    app.state.redis = auth_state.redis
    handle_exception(app)
    app.include_router(license_controller)

    async def db():
        yield auth_state.db

    app.dependency_overrides[get_db] = db
    return app


async def call(app, auth_state, *, authenticated=True):
    headers = {'Authorization': f'Bearer {auth_state.token()}'} if authenticated else {}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
        return await client.get('/api/v1/license-admin/accounts', headers=headers)


def install_identity(monkeypatch, auth_state, *, role_id, role_key, permissions):
    from module_admin.dao.user_dao import UserDao
    from module_admin.entity.do.role_do import SysRole

    async def query_user(db, user_id):
        role = SysRole(role_id=role_id, role_key=role_key, role_name='test-role', status='0', del_flag='0')
        return {
            'user_basic_info': auth_state.user,
            'user_role_info': [role],
            'user_menu_info': [SimpleNamespace(perms=value) for value in permissions],
            'user_post_info': [],
            'user_dept_info': None,
        }

    monkeypatch.setattr(UserDao, 'get_user_by_id', query_user)


@pytest.fixture(autouse=True)
def isolate_accounts_query(monkeypatch):
    from module_integration.license import LicenseService

    async def accounts(db, actor, page, page_size, keyword, account_status, authorization_status, plan_type):
        LicenseService.require_super_admin(actor, 'system:license:list')
        return {'pageNum': page, 'pageSize': page_size, 'total': 0, 'rows': []}

    monkeypatch.setattr(LicenseService, 'accounts', accounts)


@pytest.mark.asyncio
async def test_license_admin_route_requires_authentication(auth_state):
    response = await call(build_app(auth_state), auth_state, authenticated=False)
    assert response.status_code == 401
    assert response.json()['errorKey'] == 'AUTH_REQUIRED'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('role_id', 'role_key', 'permissions', 'error_key'),
    [
        (100, 'user', ['system:license:list'], 'SUPER_ADMIN_REQUIRED'),
        (2, 'admin', ['system:license:list'], 'SUPER_ADMIN_REQUIRED'),
        (2, 'cptbtptp', ['system:license:list'], 'SUPER_ADMIN_REQUIRED'),
    ],
)
async def test_license_admin_route_rejects_non_super_or_missing_permission(
    auth_state, monkeypatch, role_id, role_key, permissions, error_key
):
    install_identity(
        monkeypatch,
        auth_state,
        role_id=role_id,
        role_key=role_key,
        permissions=permissions,
    )
    response = await call(build_app(auth_state), auth_state)
    assert response.status_code == 403
    assert response.json()['errorKey'] == error_key


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('role_id', 'role_key', 'permissions'),
    [
        (1, 'cptbtptp', []),
    ],
)
async def test_license_admin_route_allows_canonical_super_admin(
    auth_state, monkeypatch, role_id, role_key, permissions
):
    install_identity(
        monkeypatch,
        auth_state,
        role_id=role_id,
        role_key=role_key,
        permissions=permissions,
    )
    response = await call(build_app(auth_state), auth_state)
    assert response.status_code == 200
    assert response.json()['data'] == {'pageNum': 1, 'pageSize': 20, 'total': 0, 'rows': []}

import httpx
import pytest
from fastapi import FastAPI

from common.vo import CrudResponseModel
from config.get_db import get_db
from exceptions.handle import handle_exception
from module_guild.controller.battle_registration_controller import public_battle_registration_controller
from module_guild.service.battle_registration_service import BattleRegistrationService


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
@pytest.mark.parametrize('authorization', [None, 'Bearer broken.token.value', 'Basic bad-value'])
async def test_legacy_public_write_routes_reject_untrusted_requests_before_service(
    auth_state, monkeypatch, kind, authorization
):
    app = FastAPI()
    app.state.redis = auth_state.redis
    handle_exception(app)
    app.include_router(public_battle_registration_controller)
    writes = []

    async def fake_db():
        yield auth_state.db

    async def write(*args, **kwargs):
        writes.append((args, kwargs))
        return CrudResponseModel(is_success=True, message='成功')

    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(
        BattleRegistrationService, f'submit_public_{"leave" if kind == "leave" else "registration"}_service', write
    )
    headers = {'Authorization': authorization} if authorization is not None else {}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
        result = await client.post(
            f'/public/battle/invite-a/{kind}', json={'member_id': 9, 'remark': '测试'}, headers=headers
        )
    assert result.json().get('code') == 401 or result.status_code == 401
    assert writes == []


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_existing_success_envelope_is_kept_and_real_user_forwarded(auth_state, monkeypatch, kind):
    app = FastAPI()
    app.state.redis = auth_state.redis
    handle_exception(app)
    app.include_router(public_battle_registration_controller)
    actors = []

    async def fake_db():
        yield auth_state.db

    async def write(*args, **kwargs):
        actors.append(kwargs['current_user'].user.user_id)
        return CrudResponseModel(is_success=True, message='成功')

    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(
        BattleRegistrationService, f'submit_public_{"leave" if kind == "leave" else "registration"}_service', write
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
        result = await client.post(
            f'/public/battle/invite-a/{kind}',
            json={'member_id': 9},
            headers={'Authorization': f'Bearer {auth_state.token()}'},
        )
    assert result.status_code == 200 and result.json()['code'] == 200
    assert actors == [23]
    operation = app.openapi()['paths'][f'/public/battle/{{invite_code}}/{kind}']['post']
    assert operation.get('security')


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['leave', 'signup'])
async def test_internal_failure_does_not_disclose_driver_details(auth_state, monkeypatch, kind):
    app = FastAPI()
    app.state.redis = auth_state.redis
    handle_exception(app)
    app.include_router(public_battle_registration_controller)

    async def fake_db():
        yield auth_state.db

    async def fail(*args, **kwargs):
        raise RuntimeError('mysql://secret-password@private-server SQL SELECT private_contact')

    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(
        BattleRegistrationService, f'submit_public_{"leave" if kind == "leave" else "registration"}_service', fail
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
        result = await client.post(
            f'/public/battle/invite-a/{kind}',
            json={'member_id': 9},
            headers={'Authorization': f'Bearer {auth_state.token()}'},
        )
    assert result.json()['code'] == 500
    assert 'secret-password' not in result.text and 'SELECT' not in result.text

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from common.aspect.interface_auth import CheckUserInterfaceAuth
from exceptions.exception import PermissionException
from module_admin.entity.vo.ai_key_vo import (
    AiConnectionModel,
    AiConnectionSaveModel,
    InternalPowerAiKeyModel,
    InternalPowerAiKeyUpdateModel,
)
from module_admin.service.ai_key_service import ActiveAiConnection, AiKeyService


def test_ai_key_management_rejects_non_admin_users():
    with pytest.raises(PermissionException):
        AiKeyService.ensure_admin(SimpleNamespace(roles=['common'], user=SimpleNamespace(user_id=2, admin=False)))


def test_ai_key_management_allows_super_administrator_without_role_key():
    AiKeyService.ensure_admin(SimpleNamespace(roles=[], user=SimpleNamespace(user_id=1, admin=True)))


def test_super_administrator_bypasses_all_interface_permissions(monkeypatch):
    current_user = SimpleNamespace(permissions=[], roles=[], user=SimpleNamespace(user_id=1, admin=True))
    monkeypatch.setattr(
        'common.aspect.interface_auth.DependencyUtil.check_exclude_routes',
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        'common.aspect.interface_auth.RequestContext.get_current_user',
        lambda: current_user,
    )

    assert CheckUserInterfaceAuth('system:aikey:edit')(SimpleNamespace()) is True


def test_internal_power_key_status_only_exposes_configuration_flag():
    status = InternalPowerAiKeyModel(api_key_configured=True, update_by='admin')

    assert status.api_key_configured is True
    assert 'api_key' not in status.model_dump()
    assert 'encrypted-secret-value' not in str(status.model_dump())


@pytest.mark.parametrize(
    'payload',
    [
        {'api_key': 'new-key', 'clear_api_key': True},
        {'api_key': '   ', 'clear_api_key': False},
    ],
)
def test_internal_power_key_update_requires_one_valid_operation(payload):
    with pytest.raises(ValidationError):
        InternalPowerAiKeyUpdateModel(**payload)


def test_connection_public_model_never_contains_api_key():
    connection = AiConnectionModel(
        id=1,
        name='Mimo 图片识别',
        provider='Mimo',
        base_url='https://api.xiaomimimo.com/v1',
        protocol='chat_completions',
        model='mimo-v2.5',
        api_key_configured=True,
        active=True,
    )

    payload = connection.model_dump(by_alias=True)

    assert payload['apiKeyConfigured'] is True
    assert 'apiKey' not in payload
    assert 'api_key' not in payload


def test_connection_save_normalizes_base_url_and_protocol():
    connection = AiConnectionSaveModel(
        name=' OpenAI 主连接 ',
        provider=' OpenAI ',
        base_url='https://api.openai.com/v1/',
        protocol='responses',
        model=' gpt-5.4 ',
        api_key=' secret ',
    )

    assert connection.name == 'OpenAI 主连接'
    assert connection.provider == 'OpenAI'
    assert connection.base_url == 'https://api.openai.com/v1'
    assert connection.model == 'gpt-5.4'
    assert connection.api_key == 'secret'


@pytest.mark.parametrize('base_url', ['ftp://example.com/v1', 'example.com/v1', ''])
def test_connection_save_rejects_invalid_base_url(base_url):
    with pytest.raises(ValidationError):
        AiConnectionSaveModel(
            name='invalid',
            provider='custom',
            base_url=base_url,
            protocol='chat_completions',
            model='model-a',
            api_key='secret',
        )


@pytest.mark.asyncio
async def test_activate_connection_keeps_exactly_one_active(monkeypatch):
    records = [
        SimpleNamespace(model_id=1, model_name='one', model_code='one', api_key='key', status='0', update_by='', update_time=None),
        SimpleNamespace(model_id=2, model_name='two', model_code='two', api_key='key', status='1', update_by='', update_time=None),
        SimpleNamespace(model_id=3, model_name='three', model_code='three', api_key='key', status='0', update_by='', update_time=None),
    ]

    class FakeDb:
        committed = False

        async def commit(self):
            self.committed = True

        async def rollback(self):
            raise AssertionError('activation should not roll back')

    async def fake_list(_query_db, *, for_update=False):
        assert for_update is True
        return records

    monkeypatch.setattr(AiKeyService, '_get_connection_records', fake_list)
    db = FakeDb()
    user = SimpleNamespace(roles=[], user=SimpleNamespace(user_id=1, user_name='admin', admin=True))

    result = await AiKeyService.activate_connection_services(db, 2, user)

    assert result.is_success is True
    assert [record.status for record in records] == ['1', '0', '1']
    assert db.committed is True


def test_runtime_connection_contains_decrypted_secret_but_public_model_does_not(monkeypatch):
    record = SimpleNamespace(
        model_id=7,
        model_name='Vision',
        model_code='vision-model',
        provider='Custom',
        base_url='https://example.com/v1',
        model_type='chat_completions',
        api_key='encrypted',
        max_tokens=2048,
        temperature=0.2,
        support_images='Y',
    )
    monkeypatch.setattr('module_admin.service.ai_key_service.CryptoUtil.decrypt', lambda value: 'plain-secret')

    runtime = AiKeyService._runtime_from_record(record)

    assert isinstance(runtime, ActiveAiConnection)
    assert runtime.api_key == 'plain-secret'
    assert runtime.model == 'vision-model'
    assert runtime.protocol == 'chat_completions'

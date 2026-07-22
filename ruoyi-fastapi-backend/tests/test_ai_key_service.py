from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from common.aspect.interface_auth import CheckUserInterfaceAuth
from exceptions.exception import PermissionException
from module_admin.entity.vo.ai_key_vo import InternalPowerAiKeyModel, InternalPowerAiKeyUpdateModel
from module_admin.service.ai_key_service import AiKeyService


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

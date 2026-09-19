from types import SimpleNamespace

from common.constant import CommonConstant
from module_admin.service.user_service import UserService
from module_guild.service.battle_registration_service import BattleRegistrationService


def test_super_admin_identity_uses_new_role_key() -> None:
    current_user = SimpleNamespace(
        roles=[CommonConstant.SUPER_ADMIN_ROLE_KEY],
        user=SimpleNamespace(user_id=42, admin=False),
    )

    assert UserService.is_admin_role(current_user) is True


def test_legacy_admin_role_key_is_not_super_admin() -> None:
    current_user = SimpleNamespace(
        roles=['admin'],
        user=SimpleNamespace(user_id=42, admin=False),
    )

    assert UserService.is_admin_role(current_user) is False


def test_user_id_one_remains_super_admin_during_payload_transition() -> None:
    current_user = SimpleNamespace(
        roles=[],
        user=SimpleNamespace(user_id=CommonConstant.SUPER_ADMIN_ROLE_ID, admin=True),
    )

    assert UserService.is_admin_role(current_user) is True


def test_battle_registration_scope_uses_new_super_admin_role_key() -> None:
    current_user = SimpleNamespace(
        roles=[CommonConstant.SUPER_ADMIN_ROLE_KEY],
        user=SimpleNamespace(user_id=42, admin=False),
    )

    assert BattleRegistrationService._get_role_scope(current_user) == 'admin'


def test_battle_registration_scope_keeps_explicit_model_admin_compatibility() -> None:
    current_user = SimpleNamespace(
        roles=[],
        user=SimpleNamespace(user_id=CommonConstant.SUPER_ADMIN_ROLE_ID, admin=True),
    )

    assert BattleRegistrationService._get_role_scope(current_user) == 'admin'


def test_battle_registration_scope_rejects_legacy_role_string_spoofing() -> None:
    current_user = SimpleNamespace(
        roles=['admin'],
        user=SimpleNamespace(user_id=42, admin=False),
    )

    assert BattleRegistrationService._get_role_scope(current_user) == 'user'

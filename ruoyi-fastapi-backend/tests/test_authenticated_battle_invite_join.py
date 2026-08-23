from types import SimpleNamespace

import pytest
from _pytest.monkeypatch import MonkeyPatch

from module_guild.service.battle_registration_service import BattleRegistrationService


@pytest.mark.asyncio
async def test_authenticated_invite_join_reuses_account_application_flow(monkeypatch: MonkeyPatch) -> None:
    guild_id = 101
    invite = SimpleNamespace(owner_user_id=guild_id)
    current_user = SimpleNamespace(
        user=SimpleNamespace(user_id=23, user_name='member23'),
        roles=['user'],
    )
    captured: dict[str, object] = {}

    async def fake_get_active_invite(db: object, invite_code: str) -> SimpleNamespace:
        assert invite_code == 'invite001'
        return invite

    async def fake_submit_application(
        db: object, authenticated_user: object, data: object
    ) -> SimpleNamespace:
        captured['user'] = authenticated_user
        captured['data'] = data
        return SimpleNamespace(is_success=True, message='申请已提交，等待审核')

    monkeypatch.setattr(BattleRegistrationService, '_get_active_invite_or_raise', fake_get_active_invite)
    monkeypatch.setattr(
        'module_guild.service.battle_registration_service.JoinApplicationService.submit_application_service',
        fake_submit_application,
    )

    result = await BattleRegistrationService.submit_authenticated_join_service(
        SimpleNamespace(),
        current_user,
        'invite001',
        SimpleNamespace(
            player_name='张三',
            player_class='铁衣',
            secondary_class='素问',
            applicant_name='小张',
            applicant_contact='wx-001',
            remark='申请加入',
        ),
    )

    assert result.message == '申请已提交，等待审核'
    assert captured['user'] is current_user
    assert captured['data'].guild_id == guild_id
    assert captured['data'].player_name == '张三'
    assert captured['data'].player_class == '铁衣'
    assert captured['data'].secondary_class == '素问'
    assert captured['data'].remark == '申请人：小张；联系方式：wx-001；申请加入'

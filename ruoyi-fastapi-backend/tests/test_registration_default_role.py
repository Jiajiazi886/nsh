import asyncio
from types import SimpleNamespace

from module_admin.entity.vo.login_vo import UserRegister
from module_admin.service.login_service import LoginService
from module_admin.service.user_service import UserService


class FakeRedis:
    async def get(self, key: str) -> str:
        if key.endswith(':sys.account.registerUser'):
            return 'true'
        if key.endswith(':sys.account.captchaEnabled'):
            return 'false'
        return ''


def test_self_registered_user_always_receives_builtin_guild_member_role(monkeypatch):
    captured = {}

    async def add_user(_query_db, user):
        captured['user'] = user
        return SimpleNamespace(is_success=True, message='注册成功')

    monkeypatch.setattr(UserService, 'add_user_services', add_user)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis=FakeRedis())))
    registration = UserRegister(
        username='register-role-test',
        password='TestPassword123',
        confirmPassword='TestPassword123',
    )

    result = asyncio.run(LoginService.register_user_services(request, object(), registration))

    assert result.is_success is True
    assert captured['user'].role_ids == [100]
    assert LoginService.REGISTER_DEFAULT_ROLE_ID == 100

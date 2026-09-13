import pytest

from config.env import AppConfig
from exceptions.exception import LoginException
from module_admin.entity.vo.login_vo import UserLogin
from module_admin.service import login_service as login_module
from module_admin.service.login_service import LoginService
from .helpers import make_request


@pytest.mark.asyncio
async def test_v1_captcha_cannot_be_bypassed_with_docs_referer(auth_state, monkeypatch):
    request = make_request(auth_state.redis, path='/api/v1/auth/login')
    request.scope['headers'] = [(b'referer', b'http://isolated/docs')]
    monkeypatch.setattr(AppConfig, 'app_env', 'dev')
    calls = []

    async def captcha(request, user):
        calls.append('captcha')
        raise LoginException(message='synthetic captcha rejection')

    async def query(db, user_name):
        calls.append('account')
        raise LoginException(message='synthetic account rejection')

    monkeypatch.setattr(LoginService, '_LoginService__check_login_captcha', captcha)
    monkeypatch.setattr(login_module, 'login_by_account', query)
    with pytest.raises(LoginException):
        await LoginService.authenticate_user(
            request, auth_state.db, UserLogin(userName='member23', password='synthetic', captchaEnabled=True)
        )
    assert calls == ['captcha']

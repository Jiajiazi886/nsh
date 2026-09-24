from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTUP_SCRIPT = PROJECT_ROOT / '启动项目.ps1'
LOGIN_VIEW = PROJECT_ROOT / 'ruoyi-fastapi-frontend' / 'src' / 'views' / 'login.vue'
ACCOUNT_ENV = PROJECT_ROOT / 'ruoyi-fastapi-backend' / 'config' / 'env.py'


def test_login_page_shows_registration_while_auth_config_is_loading() -> None:
    login_source = LOGIN_VIEW.read_text(encoding='utf-8')

    assert 'const register = ref(true);' in login_source


def test_startup_verifies_environment_controlled_self_registration() -> None:
    startup_source = STARTUP_SCRIPT.read_text(encoding='utf-8')
    account_env_source = ACCOUNT_ENV.read_text(encoding='utf-8')

    assert 'Enable-LocalRegistration' not in startup_source
    assert 'enable_local_registration.py' not in startup_source
    assert 'account_register_enabled: bool = True' in account_env_source
    assert "http://127.0.0.1:9100/authConfig" in startup_source
    assert "http://127.0.0.1/register" in startup_source
    assert 'registerEnabled' in startup_source

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTUP_SCRIPT = PROJECT_ROOT / '启动项目.ps1'
LOGIN_VIEW = PROJECT_ROOT / 'ruoyi-fastapi-frontend' / 'src' / 'views' / 'login.vue'


def test_login_page_shows_registration_while_auth_config_is_loading() -> None:
    login_source = LOGIN_VIEW.read_text(encoding='utf-8')

    assert 'const register = ref(true);' in login_source


def test_startup_enables_and_verifies_self_registration() -> None:
    startup_source = STARTUP_SCRIPT.read_text(encoding='utf-8')

    assert 'Enable-LocalRegistration' in startup_source
    assert "http://127.0.0.1:9100/authConfig" in startup_source
    assert "http://127.0.0.1/register" in startup_source
    assert 'registerEnabled' in startup_source

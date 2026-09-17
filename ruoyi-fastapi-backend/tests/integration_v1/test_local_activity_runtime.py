import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]

def module():
    spec = importlib.util.spec_from_file_location('local_activity_dev', ROOT / 'tools/local_activity_dev.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def test_local_runtime_never_targets_original_database_or_redis():
    settings = module().runtime_overrides()
    assert settings['DB_DATABASE'].startswith('nsh_activity_dev_')
    assert settings['DB_DATABASE'] != 'ruoyi'
    assert settings['REDIS_DATABASE'] == '15'
    assert settings['APP_PORT'] == '9101'
    assert settings['APP_RELOAD'] == 'false'
    assert settings['NSH_ACTIVITIES_ENABLED'] == 'true'
    assert settings['LOG_MASK_ENABLED'] == 'true'
    # Windows PowerShell 5 reads non-BOM UTF-8 scripts as legacy ANSI and breaks Chinese literals.
    assert (ROOT.parent / '启动新版联调.ps1').read_bytes().startswith(b'\xef\xbb\xbf')

@pytest.mark.parametrize('name', ['ruoyi', 'nsh', 'nsh_activity_dev_x;DROP DATABASE ruoyi', '../ruoyi', ''])
def test_database_guard_rejects_unsafe_targets(name):
    with pytest.raises(ValueError):
        module().validate_target(name)

def test_local_lifespan_does_not_start_copied_scheduler_jobs():
    source = (ROOT / 'tools/local_activity_dev.py').read_text(encoding='utf-8')
    assert 'init_system_scheduler' not in source
    assert 'run_schema_migrations' not in source  # only the guarded database bootstrap may initialize dev DB
    assert '9 activity tables' in source

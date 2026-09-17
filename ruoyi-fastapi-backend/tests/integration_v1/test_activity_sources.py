from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.asyncio
async def test_startup_excludes_activity_tables_from_automatic_ddl(monkeypatch):
    from config import get_db
    from module_admin.entity.do.user_do import SysUser
    from module_integration.activities.models import Activity

    captured = []
    monkeypatch.setattr(get_db.Base.metadata, 'create_all', lambda connection, **kw: captured.extend(kw['tables']))
    connection = MagicMock()

    async def run_sync(fn):
        fn(MagicMock())

    connection.run_sync = run_sync
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=connection)
    context.__aexit__ = AsyncMock()
    engine = MagicMock()
    engine.begin.return_value = context
    monkeypatch.setattr(get_db, 'async_engine', engine)
    for name in [
        'ensure_system_roles',
        'run_schema_migrations',
        'ensure_internal_power_entry_limit_columns',
        'ensure_internal_power_lingyun_columns',
        'ensure_sys_user_vip_sponsor_columns',
        'ensure_default_ai_recognition_config',
        'ensure_vip_ai_recognition_grant_config',
        'ensure_damage_formula_version_schema',
    ]:
        monkeypatch.setattr(get_db, name, AsyncMock())
    await get_db.init_create_table()
    assert captured and all(not t.name.startswith('integration_') for t in captured)
    assert SysUser.__table__ in captured
    assert Activity.__table__ not in captured


def test_active_clients_vendor_canonical_sdk_and_archived_clients_stay_on_frozen_contract():
    sdk = (ROOT / 'integration-sdk/javascript/client.js').read_text(encoding='utf-8').strip()
    nested = ROOT / 'xiaochengxu/hhhhhhtml/jiusi-data-dashboard-frontend/demo'
    # These two clients are archived. Keep validating their last supported SDK projection,
    # but do not force new primary-client endpoints into code that is no longer shipped.
    archived_sdk = sdk.replace("      register: data => request('POST', '/auth/register', data, false),\n", '')
    archived_sdk = archived_sdk.replace(
        "      activityProfiles: (orgId, activityId) => request('GET', '/activity-profiles' + query({ orgId, activityId })),\n",
        "      activityProfiles: orgId => request('GET', '/activity-profiles' + query({ orgId })),\n",
    )
    for endpoint in [
        "      activityLineupTemplates: orgId => request('GET', '/activity-lineup-templates' + query({ orgId })),\n",
        "      activityLeaveInfo: code => request('GET', '/activity-leave/' + segment(code), undefined, false),\n",
        "      activityLeaveMembers: (code, keyword) => request('GET', '/activity-leave/' + segment(code) + '/members' + query({ keyword }), undefined, false),\n",
        "      submitActivityLeave: (code, data) => request('POST', '/activity-leave/' + segment(code), data, false),\n",
        "      activityLeaves: id => request('GET', activityPath(id) + '/leaves'),\n",
    ]:
        archived_sdk = archived_sdk.replace(endpoint, '')
    archived_sdk = archived_sdk.replace(
        ",\n      importActivityReport: (id, data) => request('POST', activityPath(id) + '/reports/import', data)",
        '',
    )
    assert (ROOT / 'xiaochengxu/utils/nsh-api-sdk.js').read_text(encoding='utf-8').strip() == archived_sdk
    assert (nested / 'utils/nsh-api-sdk.js').read_text(encoding='utf-8').strip() == archived_sdk
    assert (ROOT / 'ruoyi-fastapi-frontend/src/utils/nshApiSdk.js').read_text(encoding='utf-8').strip() == sdk
    assert (nested / 'utils/activity-ui.js').read_text(encoding='utf-8').strip() == (
        ROOT / 'xiaochengxu/utils/activity-ui.js'
    ).read_text(encoding='utf-8').strip()
    core=(ROOT/'integration-sdk/javascript/profession-styles.js').read_text(encoding='utf-8').strip()
    for p in [ROOT/'ruoyi-fastapi-frontend/src/utils/professionStylesCore.js',ROOT/'xiaochengxu/utils/profession-styles-core.js',nested/'utils/profession-styles-core.js']:
        assert p.read_text(encoding='utf-8').strip()==core
    assert (ROOT/'xiaochengxu/components/player-profile-form/index.js').read_text(encoding='utf-8')==(nested/'components/player-profile-form/index.js').read_text(encoding='utf-8')


def test_current_primary_mini_vendors_canonical_sdk_when_present():
    primary = ROOT.parent / 'xiaocghengxu-dewmo/miniprogram/utils/nsh-api-sdk.js'
    if not primary.is_file():
        pytest.skip('The primary mini-program is maintained in a separate sibling workspace')
    assert primary.read_text(encoding='utf-8').strip() == (
        ROOT / 'integration-sdk/javascript/client.js'
    ).read_text(encoding='utf-8').strip()


def test_shared_activity_pages_wxml_structure_and_routes():
    import json
    import re
    import xml.etree.ElementTree as ET

    roots = [ROOT / 'xiaochengxu', ROOT / 'xiaochengxu/hhhhhhtml/jiusi-data-dashboard-frontend/demo']
    for root in roots:
        app = json.loads((root / 'app.json').read_text(encoding='utf-8'))
        for page in app['pages']:
            for extension in ['.js', '.json', '.wxml', '.wxss']:
                assert (root / (page + extension)).is_file(), page + extension
            if 'activit' in page or (
                root.name == 'demo' and any(p in page for p in ['login', 'profile', 'organization'])
            ):
                text = (root / (page + '.wxml')).read_text(encoding='utf-8')
                text = re.sub(r'\bwx:else(?=[\s>])', 'wx:else=""', text)
                text = re.sub(r'\bpassword(?=[\s>])', 'password="true"', text)
                ET.fromstring('<root xmlns:wx="urn:wx">' + text + '</root>')

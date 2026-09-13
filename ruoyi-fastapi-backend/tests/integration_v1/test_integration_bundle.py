import hashlib
import json
import zipfile

import pytest

from tools.build_integration_bundle import build_bundle, validate_bundle_files


@pytest.mark.parametrize('name', ['.env.dev', '../README.md', 'logs/server.log', 'keys/private.pem', 'sdk/javascript/node_modules/package/index.js'])
def test_bundle_rejects_non_allowlisted_files(name):
    with pytest.raises(ValueError, match='allowlist'):
        validate_bundle_files({name: b'contents'})


@pytest.mark.parametrize('content', [b'-----BEGIN PRIVATE KEY-----', b'DB_PASSWORD=synthetic-for-scanner-only', b'JWT_SECRET_KEY="synthetic-for-scanner-only"', b'eyJ' + b'a' * 30 + b'.' + b'b' * 40 + b'.' + b'c' * 40])
def test_bundle_rejects_credentials_without_echoing_value(content):
    with pytest.raises(ValueError) as result:
        validate_bundle_files({'README.md': content})
    assert content.decode() not in str(result.value)


def test_bundle_manifest_is_explicitly_partial_and_hashes_every_file(tmp_path):
    content = b'# Development SDK only'
    output = build_bundle({'README.md': content}, tmp_path)
    with zipfile.ZipFile(output) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['developmentOnly'] is True
        assert manifest['fullObjectiveComplete'] is False
        assert manifest['realWechatVerified'] is False
        assert manifest['files']['README.md']['sha256'] == hashlib.sha256(content).hexdigest()
        assert set(archive.namelist()) == {'README.md', 'manifest.json'}


def test_postman_only_contains_registered_v1_routes_and_no_credentials():
    from pathlib import Path
    from fastapi import FastAPI
    from module_integration.controller.api_v1_controller import api_v1_controller

    root = Path(__file__).resolve().parents[3]
    collection = json.loads((root / 'integration-sdk' / 'postman' / 'collection.json').read_text(encoding='utf-8'))
    assert all(item['value'] == '' for item in collection['variable'] if item['key'] in {'accessToken', 'password', 'userName'})
    app = FastAPI()
    app.include_router(api_v1_controller)
    actual = {(path, method.upper()) for path, methods in app.openapi()['paths'].items() for method in methods}
    listed = {(item['request']['url'].replace('{{apiRoot}}', '').replace('{{inviteCode}}', '{invite_code}'), item['request']['method']) for item in collection['item']}
    assert actual == listed

from fastapi import FastAPI

from common.router import auto_register_routers
from tools.export_integration_contract import build_catalogue


def test_every_registered_operation_is_catalogued_without_claiming_authorization_audit():
    app = FastAPI()
    auto_register_routers(app)
    schema = app.openapi()
    catalogue = build_catalogue(schema)
    actual = {
        (path, method.upper())
        for path, methods in schema['paths'].items()
        for method in methods
        if method in {'get', 'post', 'put', 'patch', 'delete', 'options', 'head'}
    }
    listed = {(item['path'], item['method']) for item in catalogue['operations']}
    assert actual == listed and catalogue['operationCount'] == len(actual)
    assert len(actual) >= 278
    leave = next(item for item in catalogue['operations'] if item['path'] == '/api/v1/invitations/{invite_code}/leave')
    assert leave['authentication'] == 'account-jwt-declared'
    assert leave['migrationStatus'] == 'implemented-v1'
    old = next(item for item in catalogue['operations'] if item['path'] == '/public/battle/{invite_code}/members')
    assert old['requiresManualAuthorizationReview'] is True
    assert old['migrationStatus'] == 'legacy-only-review-pending'

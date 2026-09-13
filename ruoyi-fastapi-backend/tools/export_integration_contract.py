"""Offline route inventory/spec generation; never starts the application lifespan."""

from __future__ import annotations

import json
import os
import sys

HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete', 'options', 'head'}


def build_catalogue(schema: dict) -> dict:
    operations = []
    for path, methods in schema.get('paths', {}).items():
        for method, operation in methods.items():
            if method not in HTTP_METHODS:
                continue
            v1 = path.startswith('/api/v1/')
            operations.append(
                {
                    'path': path,
                    'method': method.upper(),
                    'operationId': operation.get('operationId'),
                    'summary': operation.get('summary', ''),
                    'modules': operation.get('tags', []),
                    'authentication': 'account-jwt-declared'
                    if operation.get('security')
                    else 'public-declared-review-pending',
                    'security': operation.get('security', []),
                    'parameters': operation.get('parameters', []),
                    'requestBody': operation.get('requestBody'),
                    'responses': operation.get('responses', {}),
                    'migrationStatus': 'implemented-v1' if v1 else 'legacy-only-review-pending',
                    # A generated OpenAPI security declaration is not an object/role
                    # authorization audit. Keep outstanding reviews visible.
                    'requiresManualAuthorizationReview': not v1,
                }
            )
    return {
        'schemaVersion': 1,
        'operationCount': len(operations),
        'pathCount': len(schema.get('paths', {})),
        'operations': operations,
    }


def main() -> None:
    # The same guard as tests: explicit dummy settings before any app import,
    # no outgoing connections, and no lifespan/DDL/scheduler/Redis startup.
    from run_integration_tests import BACKEND, PROJECT, TEST_ENV, IsolationPlugin  # noqa: PLC0415

    os.environ.update(TEST_ENV)
    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    guard = IsolationPlugin()
    guard.pytest_sessionstart(None)
    try:
        from fastapi import FastAPI  # noqa: PLC0415

        from common.router import auto_register_routers  # noqa: PLC0415

        app = FastAPI(title='NSH integration development contract', version='0.1.0')
        auto_register_routers(app)
        schema = app.openapi()
        catalogue = build_catalogue(schema)
        output = PROJECT / '.artifacts' / 'integration-contract'
        output.mkdir(parents=True, exist_ok=True)
        for name, data in [('openapi.json', schema), ('api-catalogue.json', catalogue)]:
            (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Offline export: {catalogue["pathCount"]} paths, {catalogue["operationCount"]} operations')
        print(output)
    finally:
        guard.pytest_sessionfinish(None, 0)


if __name__ == '__main__':
    main()

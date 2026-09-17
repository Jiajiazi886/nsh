"""Print reviewable migration DDL; never opens a database or writes files."""

import json
import os
import sys

from run_integration_tests import BACKEND, TEST_ENV, IsolationPlugin

os.environ.update(TEST_ENV)
sys.path.insert(0, str(BACKEND))
guard = IsolationPlugin()
guard.pytest_sessionstart(None)
try:
    from sqlalchemy.schema import CreateTable, CreateIndex
    from sqlalchemy.dialects import mysql, postgresql
    from module_integration.activities import models

    tables = [
        models.Organization,
        models.OrganizationMember,
        models.Activity,
        models.ActivitySnapshot,
        models.Participation,
        models.MutationReceipt,
        models.ReportLink,
        models.ActivityLeaveLink,
        models.ActivityLeaveRecord,
    ]
    result = {}
    for name, dialect in [('mysql', mysql.dialect()), ('postgresql', postgresql.dialect())]:
        statements = ['-- REVIEW ONLY: apply manually to an independent TEST database first. No USE ruoyi statement.']
        for model in tables:
            ddl = str(CreateTable(model.__table__).compile(dialect=dialect)).strip()
            if name == 'mysql':
                ddl += ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'
            statements.append(ddl + ';')
            statements.extend(
                str(CreateIndex(index).compile(dialect=dialect)) + ';'
                for index in sorted(model.__table__.indexes, key=lambda i: i.name)
            )
        result[name] = '\n\n'.join(statements) + '\n'
    print(json.dumps(result, ensure_ascii=False))
finally:
    guard.pytest_sessionfinish(None, 0)

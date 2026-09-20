import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.backup_activity_dev_database import quote


class _Connection:
    def escape(self, value):
        if isinstance(value, bytes):
            return "_binary'\\x00abc'"
        if value == "O'Reilly":
            return "'O\\'Reilly'"
        if value == '':
            return "''"
        if isinstance(value, int):
            return str(value)
        return f"'{value}'"


def test_quote_uses_complete_pymysql_literal_without_double_wrapping():
    connection = _Connection()

    assert quote(None, connection) == 'NULL'
    assert quote('player', connection) == "'player'"
    assert quote('', connection) == "''"
    assert quote(42, connection) == '42'
    assert quote("O'Reilly", connection) == "'O\\'Reilly'"
    assert quote(b'abc', connection) == "_binary'\\x00abc'"

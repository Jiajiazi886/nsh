"""Run integration-v1 tests with explicit fake credentials and zero external sockets."""

from __future__ import annotations

import os
import socket
import sys
from contextvars import ContextVar
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
PROJECT = BACKEND.parent
TEST_ENV = {
    'APP_ENV': 'dev',
    'APP_HOST': '127.0.0.1',
    'APP_RELOAD': 'false',
    'APP_SAME_TIME_LOGIN': 'true',
    'DB_TYPE': 'mysql',
    'DB_HOST': '192.0.2.1',
    'DB_PORT': '1',
    'DB_DATABASE': 'nsh_integration_test',
    'DB_USERNAME': 'integration_test_only',
    'DB_PASSWORD': 'not-a-real-database-password',
    'DB_ECHO': 'false',
    'REDIS_HOST': '192.0.2.1',
    'REDIS_PORT': '1',
    'REDIS_DATABASE': '15',
    'REDIS_PASSWORD': '',
    'JWT_SECRET_KEY': 'isolated-integration-test-key-never-use-in-production',
    'JWT_ALGORITHM': 'HS256',
    'TRANSPORT_CRYPTO_ENABLED': 'false',
    'TRANSPORT_CRYPTO_MODE': 'off',
    'TRANSPORT_CRYPTO_PUBLIC_KEY': '',
    'TRANSPORT_CRYPTO_PRIVATE_KEY': '',
    'LOG_FILE_ENABLED': 'false',
    'NSH_INTEGRATION_TEST': '1',
    'NSH_ACTIVITIES_ENABLED': 'true',
}


class IsolationPlugin:
    """Allow asyncio's local socketpair, but no TCP/DNS to any service."""

    def pytest_sessionstart(self, session) -> None:
        from _pytest.monkeypatch import MonkeyPatch

        if any(os.environ.get(name) != value for name, value in TEST_ENV.items()):
            raise RuntimeError('Integration isolation configuration was changed before collection')
        self.patch = MonkeyPatch()
        original_pair = socket.socketpair
        original_connect = socket.socket.connect
        original_getaddrinfo = socket.getaddrinfo
        inside_pair = ContextVar('integration_socketpair', default=False)

        def guarded_pair(*args, **kwargs):
            marker = inside_pair.set(True)
            try:
                return original_pair(*args, **kwargs)
            finally:
                inside_pair.reset(marker)

        def guarded_connect(sock, address):
            if inside_pair.get() and isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
                return original_connect(sock, address)
            raise AssertionError('Forbidden network connection in isolated integration tests')

        def guarded_getaddrinfo(host, *args, **kwargs):
            if inside_pair.get() and host in ('127.0.0.1', '::1', 'localhost'):
                return original_getaddrinfo(host, *args, **kwargs)
            raise AssertionError('Forbidden DNS resolution in isolated integration tests')

        self.patch.setattr(socket, 'socketpair', guarded_pair)
        self.patch.setattr(socket.socket, 'connect', guarded_connect)
        self.patch.setattr(socket, 'getaddrinfo', guarded_getaddrinfo)

    def pytest_sessionfinish(self, session, exitstatus) -> None:
        self.patch.undo()


def main() -> int:
    os.environ.update(TEST_ENV)
    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    import pytest

    selected = sys.argv[1:] or ['tests/integration_v1']
    return pytest.main(
        [
            *selected,
            '-q',
            '-o',
            f'cache_dir={PROJECT / ".cache" / "pytest"}',
            f'--basetemp={PROJECT / ".artifacts" / "pytest-tmp"}',
        ],
        plugins=[IsolationPlugin()],
    )


if __name__ == '__main__':
    raise SystemExit(main())

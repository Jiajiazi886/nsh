import os
import socket

import pytest


def test_database_and_redis_are_explicit_fake_targets():
    from config.env import DataBaseConfig, RedisConfig

    assert os.environ['NSH_INTEGRATION_TEST'] == '1'
    assert DataBaseConfig.db_database == 'nsh_integration_test'
    assert DataBaseConfig.db_host == RedisConfig.redis_host == '192.0.2.1'
    assert DataBaseConfig.db_port == RedisConfig.redis_port == 1


@pytest.mark.parametrize('destination', [('127.0.0.1', 3306), ('127.0.0.1', 6379), ('192.0.2.1', 1)])
def test_socket_connections_to_services_are_forbidden(destination):
    with socket.socket() as sock, pytest.raises(AssertionError, match='Forbidden network'):
        sock.connect(destination)


def test_external_dns_is_forbidden():
    with pytest.raises(AssertionError, match='Forbidden DNS'):
        socket.getaddrinfo('ilinkai.weixin.qq.com', 443)


def test_local_asyncio_socketpair_can_be_created():
    first, second = socket.socketpair()
    first.close()
    second.close()

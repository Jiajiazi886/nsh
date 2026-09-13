import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'integration-sdk' / 'python'))
from nsh_client import ApiClient, ApiError


def test_python_sdk_uses_api_root_latest_token_and_string_ids():
    calls = []
    token = ['session-a']

    def transport(method, url, headers, data):
        calls.append((method, url, headers, data))
        return 200, {'code': 200, 'success': True, 'data': {'userId': '9223372036854775807'}}

    client = ApiClient('https://example.invalid/prod-api', token_provider=lambda: token[0], transport=transport)
    assert client.me()['userId'] == '9223372036854775807'
    token[0] = 'session-b'
    client.leave('邀请/甲', '9', remark='请假')
    assert calls[0][2]['Authorization'] == 'Bearer session-a'
    assert calls[1][2]['Authorization'] == 'Bearer session-b'
    assert calls[1][1].endswith('/api/v1/invitations/%E9%82%80%E8%AF%B7%2F%E7%94%B2/leave')
    with pytest.raises(ValueError, match='member_id'):
        client.leave('test', 9)


def test_python_sdk_preserves_permission_error_without_retry():
    calls = []

    def transport(*args):
        calls.append(args)
        return 403, {
            'code': 403,
            'success': False,
            'errorKey': 'MEMBER_NOT_OWNER',
            'requestId': 'req_test',
            'msg': '无权操作',
        }

    client = ApiClient('https://example.invalid', transport=transport)
    with pytest.raises(ApiError) as result:
        client.leave('test', '9')
    assert (result.value.status, result.value.error_key, result.value.request_id) == (
        403,
        'MEMBER_NOT_OWNER',
        'req_test',
    )
    assert len(calls) == 1


def test_python_sdk_login_does_not_use_current_token():
    calls = []

    def transport(*args):
        calls.append(args)
        return 200, {'code': 200, 'success': True, 'data': {'accessToken': 'new-token'}}

    client = ApiClient('https://example.invalid', token_provider=lambda: 'private-token', transport=transport)
    assert client.login('demo', 'synthetic-only')['accessToken'] == 'new-token'
    assert 'Authorization' not in calls[0][2]


@pytest.mark.parametrize(
    'base',
    [
        '/dev-api',
        'https://example.invalid/api/v1',
        'https://user:secret@example.invalid',
        'https://example.invalid?token=secret',
    ],
)
def test_python_sdk_rejects_ambiguous_roots(base):
    with pytest.raises(ValueError, match='base_url'):
        ApiClient(base)


def test_python_sdk_network_errors_do_not_disclose_connection_details():
    def transport(*args):
        raise RuntimeError('private-password-host')

    with pytest.raises(ApiError) as result:
        ApiClient('https://example.invalid', transport=transport).me()
    assert result.value.error_key == 'NETWORK_ERROR' and 'private-password-host' not in str(result.value)

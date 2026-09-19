from datetime import datetime, timedelta

from module_integration.refresh_tokens import (
    SystemAuthRefreshToken,
    new_refresh_token,
    refresh_token_hash,
    refresh_token_is_usable,
)


def _row(**overrides):
    values = {
        "expires_at": datetime(2026, 10, 1),
        "last_used_at": None,
        "revoked_at": None,
    }
    values.update(overrides)
    return SystemAuthRefreshToken(**values)


def test_refresh_token_is_stored_as_sha256_digest_only():
    raw = new_refresh_token()
    digest = refresh_token_hash(raw)
    assert raw.startswith("rt_")
    assert len(digest) == 64
    assert digest != raw
    assert refresh_token_hash(raw) == digest


def test_refresh_token_is_usable_only_once_before_expiry():
    now = datetime(2026, 9, 19, 10, 0, 0)
    assert refresh_token_is_usable(_row(expires_at=now + timedelta(seconds=1)), now)
    assert not refresh_token_is_usable(_row(expires_at=now), now)
    assert not refresh_token_is_usable(_row(expires_at=now + timedelta(days=1), last_used_at=now), now)
    assert not refresh_token_is_usable(_row(expires_at=now + timedelta(days=1), revoked_at=now), now)

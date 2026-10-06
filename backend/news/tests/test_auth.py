"""Tests offline para autenticación admin local."""

import pytest

from news.auth import (
    AdminAuthenticationError,
    create_admin_token,
    password_matches,
    verify_admin_token,
)


def test_admin_token_roundtrip() -> None:
    token = create_admin_token("admin", "secret", 60, now=100)

    payload = verify_admin_token(token, "secret", now=120)

    assert payload.username == "admin"
    assert payload.role == "admin"
    assert payload.exp == 160


def test_admin_token_rejects_wrong_secret() -> None:
    token = create_admin_token("admin", "secret", 60, now=100)

    with pytest.raises(AdminAuthenticationError):
        verify_admin_token(token, "other-secret", now=120)


def test_admin_token_rejects_expired_token() -> None:
    token = create_admin_token("admin", "secret", 60, now=100)

    with pytest.raises(AdminAuthenticationError):
        verify_admin_token(token, "secret", now=161)


def test_password_matches_uses_exact_value() -> None:
    assert password_matches("admin-pass", "admin-pass") is True
    assert password_matches("admin-pass", "wrong") is False

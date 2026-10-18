from __future__ import annotations

from time import time

import pytest

from news.firebase_auth import (
    FirebaseAuthenticationError,
    FirebaseConfigurationError,
    FirebaseIdentity,
    verify_firebase_bearer,
)


def test_verifies_bearer_token_against_configured_firebase_project() -> None:
    calls = []

    def verifier(token: str, project_id: str) -> dict[str, str]:
        calls.append((token, project_id))
        return {
            "sub": "firebase-user-1",
            "aud": project_id,
            "iss": f"https://securetoken.google.com/{project_id}",
            "auth_time": int(time()),
            "email": "reader@example.test",
            "name": "News Reader",
            "picture": "https://example.test/photo.jpg",
        }

    identity = verify_firebase_bearer(
        "Bearer signed-token",
        "news-project-123",
        verifier=verifier,
    )

    assert identity == FirebaseIdentity(
        uid="firebase-user-1",
        email="reader@example.test",
        display_name="News Reader",
        photo_url="https://example.test/photo.jpg",
    )
    assert calls == [("signed-token", "news-project-123")]


@pytest.mark.parametrize("authorization", [None, "", "Basic token", "Bearer "])
def test_rejects_missing_or_malformed_bearer_header(authorization: str | None) -> None:
    with pytest.raises(FirebaseAuthenticationError):
        verify_firebase_bearer(authorization, "news-project-123", verifier=lambda *_: {})


def test_rejects_unverifiable_token() -> None:
    def invalid_token(_token: str, _project_id: str) -> dict:
        raise FirebaseAuthenticationError("invalid token")

    with pytest.raises(FirebaseAuthenticationError):
        verify_firebase_bearer(
            "Bearer forged-token", "news-project-123", verifier=invalid_token
        )


def test_missing_firebase_project_is_a_configuration_error() -> None:
    with pytest.raises(FirebaseConfigurationError):
        verify_firebase_bearer("Bearer signed-token", "", verifier=lambda *_: {})


def test_rejects_verified_payload_without_uid() -> None:
    with pytest.raises(FirebaseAuthenticationError):
        verify_firebase_bearer(
            "Bearer signed-token",
            "news-project-123",
            verifier=lambda _token, project_id: {
                "sub": "",
                "aud": project_id,
                "iss": f"https://securetoken.google.com/{project_id}",
                "auth_time": int(time()),
            },
        )


def test_rejects_identity_claims_from_a_different_firebase_project() -> None:
    with pytest.raises(FirebaseAuthenticationError):
        verify_firebase_bearer(
            "Bearer signed-token",
            "news-project-123",
            verifier=lambda *_: {
                "sub": "user-1",
                "aud": "another-project",
                "iss": "https://securetoken.google.com/another-project",
                "auth_time": int(time()),
            },
        )


def test_rejects_missing_or_future_auth_time() -> None:
    base = {
        "sub": "user-1",
        "aud": "news-project-123",
        "iss": "https://securetoken.google.com/news-project-123",
    }
    for claims in (base, {**base, "auth_time": int(time()) + 120}):
        with pytest.raises(FirebaseAuthenticationError):
            verify_firebase_bearer(
                "Bearer signed-token",
                "news-project-123",
                verifier=lambda *_, token_claims=claims: token_claims,
            )

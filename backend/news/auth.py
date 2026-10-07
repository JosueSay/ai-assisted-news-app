"""Autenticación local mínima para operaciones admin de noticias."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any


class AdminAuthenticationError(RuntimeError):
    """Credenciales o token admin inválidos."""


@dataclass(frozen=True)
class AdminTokenPayload:
    username: str
    role: str
    exp: int


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256)
    return _base64url_encode(digest.digest())


def password_matches(candidate: str, expected: str) -> bool:
    """Compara contraseñas sin exponer timing obvio."""
    return secrets.compare_digest(candidate, expected)


def create_admin_token(
    username: str,
    secret: str,
    ttl_seconds: int,
    *,
    now: int | None = None,
) -> str:
    issued_at = int(time.time() if now is None else now)
    payload = {
        "username": username,
        "role": "admin",
        "exp": issued_at + ttl_seconds,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_part = _base64url_encode(payload_json)
    signature = _sign(payload_part, secret)
    return f"{payload_part}.{signature}"


def verify_admin_token(
    token: str,
    secret: str,
    *,
    now: int | None = None,
) -> AdminTokenPayload:
    try:
        payload_part, signature = token.split(".", 1)
    except ValueError as error:
        raise AdminAuthenticationError("Token admin inválido.") from error

    expected_signature = _sign(payload_part, secret)
    if not secrets.compare_digest(signature, expected_signature):
        raise AdminAuthenticationError("Token admin inválido.")

    try:
        payload_raw = _base64url_decode(payload_part)
        payload: dict[str, Any] = json.loads(payload_raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as error:
        raise AdminAuthenticationError("Token admin inválido.") from error

    username = str(payload.get("username") or "")
    role = str(payload.get("role") or "")
    exp = int(payload.get("exp") or 0)
    current_time = int(time.time() if now is None else now)
    if not username or role != "admin" or exp <= current_time:
        raise AdminAuthenticationError("Token admin expirado o inválido.")

    return AdminTokenPayload(username=username, role=role, exp=exp)

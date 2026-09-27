"""Configuración de la base de datos de noticias.

Toda la parametrización es no secreta.
Los valores secretos (MONGODB_URI) se cargan desde archivos en keys/.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

NEWS_ROOT = Path(__file__).resolve().parent
ENV_FILE = NEWS_ROOT / ".env"

DEFAULT_URI_FILE = NEWS_ROOT.parent.parent / "keys" / "mongodb_uri"
DEFAULT_DATABASE = "ai_assisted_news"
DEFAULT_TIMEOUT_MS = 5000
DEFAULT_REQUIRED = True


class NewsDatabaseConfigurationError(RuntimeError):
    """La configuración de la base de datos de noticias no es válida."""


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = NEWS_ROOT / path
    return path.resolve()


@dataclass(frozen=True)
class NewsSettings:
    mongodb_database: str
    mongodb_uri_file: Path
    mongodb_required: bool
    mongodb_timeout_ms: int

    @property
    def mongodb_configured(self) -> bool:
        """Indica si la URI existe, es archivo regular y no está vacía."""
        from .secret_loader import check_secret_file
        return check_secret_file(self.mongodb_uri_file) == "configured"


def _read_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name, str(default)).strip().lower()
    if raw_value in {"1", "true", "yes", "on"}:
        return True
    if raw_value in {"0", "false", "no", "off"}:
        return False
    raise NewsDatabaseConfigurationError(f"{name} debe ser true o false.")


def _read_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise NewsDatabaseConfigurationError(
            f"{name} debe contener un número entero."
        ) from error
    if value <= 0:
        raise NewsDatabaseConfigurationError(f"{name} debe ser mayor que cero.")
    return value


@lru_cache
def get_news_settings() -> NewsSettings:
    """Construye la configuración desde variables de entorno y .env.

    El orden de precedencia:
    1. Variables de entorno del sistema.
    2. Archivo backend/news/.env (si existe).
    """
    load_dotenv(ENV_FILE, override=False)

    raw_uri_file = os.getenv("NEWS_MONGODB_URI_FILE", "").strip()
    uri_file = _resolve_path(raw_uri_file) if raw_uri_file else DEFAULT_URI_FILE

    return NewsSettings(
        mongodb_database=os.getenv("NEWS_MONGODB_DATABASE", DEFAULT_DATABASE).strip()
        or DEFAULT_DATABASE,
        mongodb_uri_file=uri_file,
        mongodb_required=_read_bool("NEWS_MONGODB_REQUIRED", DEFAULT_REQUIRED),
        mongodb_timeout_ms=_read_positive_int(
            "NEWS_MONGODB_TIMEOUT_MS", DEFAULT_TIMEOUT_MS
        ),
    )
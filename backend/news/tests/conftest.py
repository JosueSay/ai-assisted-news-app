"""Configuración de pytest para tests de la base de datos de noticias."""

import os
from typing import Iterator

import pytest

from news.config import get_news_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    """Limpia la caché de get_news_settings tras cada test."""
    os.environ.pop("NEWS_MONGODB_URI_FILE", None)
    os.environ.pop("NEWS_DB_MODE", None)
    os.environ.pop("NEWS_MONGODB_LOCAL_URI", None)
    os.environ.pop("NEWS_MONGODB_DATABASE", None)
    os.environ.pop("NEWS_MONGODB_REQUIRED", None)
    os.environ.pop("NEWS_MONGODB_TIMEOUT_MS", None)
    os.environ.pop("NEWS_ADMIN_USERNAME", None)
    os.environ.pop("NEWS_ADMIN_PASSWORD_FILE", None)
    os.environ.pop("NEWS_ADMIN_TOKEN_TTL_SECONDS", None)
    get_news_settings.cache_clear()
    yield
    get_news_settings.cache_clear()

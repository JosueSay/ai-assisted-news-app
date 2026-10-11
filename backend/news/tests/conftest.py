"""Configuración de pytest para tests de la base de datos de noticias."""

import os
from typing import Iterator

import pytest

from news.chat.config import get_chat_settings
from news.chat.provider import get_llm_provider
from news.config import get_news_settings

CHAT_ENV_VARS = (
    "NEWS_CHAT_PROVIDER",
    "NEWS_CHAT_MODEL",
    "NEWS_OPENAI_API_KEY_FILE",
    "NEWS_CHAT_PROMPT_FILE",
    "CHAT_SESSION_TTL_SECONDS",
    "NEWS_CHAT_MAX_OUTPUT_TOKENS",
    "NEWS_CHAT_TIMEOUT_SECONDS",
    "NEWS_CHAT_INPUT_USD_PER_MILLION",
    "NEWS_CHAT_OUTPUT_USD_PER_MILLION",
    "NEWS_AI_BUDGET_USD",
    "NEWS_CHAT_DEFAULT_LOCATION_CODE",
)


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
    for name in CHAT_ENV_VARS:
        os.environ.pop(name, None)
    get_news_settings.cache_clear()
    get_chat_settings.cache_clear()
    get_llm_provider.cache_clear()
    yield
    get_news_settings.cache_clear()
    get_chat_settings.cache_clear()
    get_llm_provider.cache_clear()

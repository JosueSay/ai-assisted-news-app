"""Tests para el módulo config."""

import os
from pathlib import Path

import pytest

from news.config import (
    DEFAULT_DATABASE,
    DEFAULT_ADMIN_TOKEN_TTL_SECONDS,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_MODE,
    DEFAULT_REQUIRED,
    DEFAULT_TIMEOUT_MS,
    get_news_settings,
)


class TestGetNewsSettings:
    def test_defaults(self) -> None:
        settings = get_news_settings()
        assert settings.mongodb_mode == DEFAULT_MODE
        assert settings.mongodb_database == DEFAULT_DATABASE
        assert settings.mongodb_timeout_ms == DEFAULT_TIMEOUT_MS
        assert settings.mongodb_required is DEFAULT_REQUIRED
        assert settings.admin_username == DEFAULT_ADMIN_USERNAME
        assert settings.admin_token_ttl_seconds == DEFAULT_ADMIN_TOKEN_TTL_SECONDS

    def test_env_overrides(self) -> None:
        os.environ["NEWS_MONGODB_DATABASE"] = "test_db"
        os.environ["NEWS_MONGODB_TIMEOUT_MS"] = "3000"
        os.environ["NEWS_MONGODB_REQUIRED"] = "false"
        os.environ["NEWS_ADMIN_USERNAME"] = "editor"
        os.environ["NEWS_ADMIN_TOKEN_TTL_SECONDS"] = "900"
        settings = get_news_settings()
        assert settings.mongodb_database == "test_db"
        assert settings.mongodb_timeout_ms == 3000
        assert settings.mongodb_required is False
        assert settings.admin_username == "editor"
        assert settings.admin_token_ttl_seconds == 900

    def test_database_name(self) -> None:
        os.environ["NEWS_MONGODB_DATABASE"] = "custom_news_db"
        settings = get_news_settings()
        assert settings.mongodb_database == "custom_news_db"

    def test_mongodb_configured_property(self) -> None:
        os.environ["NEWS_MONGODB_URI_FILE"] = "/tmp/nonexistent_uri_for_test"
        settings = get_news_settings()
        assert settings.mongodb_configured is False

    def test_local_mode_is_configured_without_secret_file(self) -> None:
        os.environ["NEWS_DB_MODE"] = "local"
        os.environ["NEWS_MONGODB_LOCAL_URI"] = "mongodb://news-mongo:27017/test"
        settings = get_news_settings()
        assert settings.mongodb_mode == "local"
        assert settings.mongodb_configured is True
        assert settings.uses_secret_file is False

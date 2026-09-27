"""Tests para el módulo config."""

import os
from pathlib import Path

import pytest

from news.config import (
    DEFAULT_DATABASE,
    DEFAULT_REQUIRED,
    DEFAULT_TIMEOUT_MS,
    get_news_settings,
)


class TestGetNewsSettings:
    def test_defaults(self) -> None:
        settings = get_news_settings()
        assert settings.mongodb_database == DEFAULT_DATABASE
        assert settings.mongodb_timeout_ms == DEFAULT_TIMEOUT_MS
        assert settings.mongodb_required is DEFAULT_REQUIRED

    def test_env_overrides(self) -> None:
        os.environ["NEWS_MONGODB_DATABASE"] = "test_db"
        os.environ["NEWS_MONGODB_TIMEOUT_MS"] = "3000"
        os.environ["NEWS_MONGODB_REQUIRED"] = "false"
        settings = get_news_settings()
        assert settings.mongodb_database == "test_db"
        assert settings.mongodb_timeout_ms == 3000
        assert settings.mongodb_required is False

    def test_database_name(self) -> None:
        os.environ["NEWS_MONGODB_DATABASE"] = "custom_news_db"
        settings = get_news_settings()
        assert settings.mongodb_database == "custom_news_db"

    def test_mongodb_configured_property(self) -> None:
        settings = get_news_settings()
        assert settings.mongodb_configured is False
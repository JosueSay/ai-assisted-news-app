"""Tests para el módulo config."""

import os

from news.config import (
    DEFAULT_DATABASE,
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
        assert settings.firebase_project_id == ""

    def test_env_overrides(self) -> None:
        os.environ["NEWS_MONGODB_DATABASE"] = "test_db"
        os.environ["NEWS_MONGODB_TIMEOUT_MS"] = "3000"
        os.environ["NEWS_MONGODB_REQUIRED"] = "false"
        os.environ["NEWS_FIREBASE_PROJECT_ID"] = "test-project"
        settings = get_news_settings()
        assert settings.mongodb_database == "test_db"
        assert settings.mongodb_timeout_ms == 3000
        assert settings.mongodb_required is False
        assert settings.firebase_project_id == "test-project"

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


def test_root_secret_paths_resolve_identically_in_local_python_and_compose(monkeypatch):
    from news.config import PROJECT_ROOT, _resolve_path

    assert _resolve_path("keys/mongodb_uri") == PROJECT_ROOT / "keys/mongodb_uri"
    assert _resolve_path("../../keys/mongodb_uri") == PROJECT_ROOT / "keys/mongodb_uri"

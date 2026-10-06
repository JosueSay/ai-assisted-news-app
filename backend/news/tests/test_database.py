"""Tests para el módulo database usando mocks."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pymongo.errors import PyMongoError

from news.config import NewsSettings
from news.database import NewsDatabaseError, close_client, get_news_client, get_news_database, ping_database


def make_settings(**overrides) -> NewsSettings:
    defaults = {
        "mongodb_mode": "atlas",
        "mongodb_database": "test_news",
        "mongodb_uri_file": Path("/fake/uri_file"),
        "mongodb_local_uri": "mongodb://news-mongo:27017/test_news",
        "mongodb_required": True,
        "mongodb_timeout_ms": 5000,
        "admin_username": "admin",
        "admin_password_file": Path("/fake/admin_password"),
        "admin_token_ttl_seconds": 3600,
    }
    defaults.update(overrides)
    return NewsSettings(**defaults)


class TestGetNewsClient:
    def test_get_news_client_creates_client_with_expected_settings(self) -> None:
        settings = make_settings()
        fake_uri = "mongodb://fake:27017"
        with patch("news.database.load_secret", return_value=fake_uri) as mock_load:
            with patch("news.database.MongoClient") as mock_mongo:
                client = get_news_client(settings)

        mock_load.assert_called_once_with(settings.mongodb_uri_file)
        mock_mongo.assert_called_once_with(
            fake_uri,
            appname="ai-assisted-news",
            serverSelectionTimeoutMS=5000,
            uuidRepresentation="standard",
        )
        assert client == mock_mongo.return_value

    def test_get_news_client_uses_local_uri_without_secret_loader(self) -> None:
        settings = make_settings(
            mongodb_mode="local",
            mongodb_local_uri="mongodb://news-mongo:27017/test_news",
        )
        with patch("news.database.load_secret") as mock_load:
            with patch("news.database.MongoClient") as mock_mongo:
                get_news_client(settings)

        mock_load.assert_not_called()
        mock_mongo.assert_called_once_with(
            "mongodb://news-mongo:27017/test_news",
            appname="ai-assisted-news",
            serverSelectionTimeoutMS=5000,
            uuidRepresentation="standard",
        )


class TestGetNewsDatabase:
    def test_get_news_database_selects_database(self) -> None:
        settings = make_settings()
        mock_client = MagicMock()
        with patch("news.database.get_news_client", return_value=mock_client):
            db = get_news_database(settings)
        mock_client.__getitem__.assert_called_once_with("test_news")
        assert db == mock_client["test_news"]


class TestPingDatabase:
    def test_ping_database_success(self) -> None:
        settings = make_settings()
        mock_database = MagicMock()
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_database

        with patch("news.database.get_news_client", return_value=mock_client):
            result = ping_database(settings)

        assert result == {"status": "ok", "database": "test_news"}
        mock_database.command.assert_called_once_with("ping")
        mock_client.close.assert_called_once()

    def test_ping_database_failure(self) -> None:
        settings = make_settings()
        mock_database = MagicMock()
        mock_database.command.side_effect = PyMongoError("connection refused")
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_database

        with patch("news.database.get_news_client", return_value=mock_client):
            with pytest.raises(NewsDatabaseError):
                ping_database(settings)

        mock_client.close.assert_called_once()

    def test_ping_database_error_sanitized(self) -> None:
        fake_uri = "mongodb://user:secret@host:27017"
        settings = make_settings()
        mock_database = MagicMock()
        mock_database.command.side_effect = PyMongoError("connection refused")
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_database

        with patch("news.database.get_news_client", return_value=mock_client):
            with pytest.raises(NewsDatabaseError) as exc_info:
                ping_database(settings)

        assert fake_uri not in str(exc_info.value)
        assert "secret" not in str(exc_info.value)


class TestCloseClient:
    def test_close_client(self) -> None:
        mock_client = MagicMock()
        close_client(mock_client)
        mock_client.close.assert_called_once()

"""Tests para el módulo database usando mocks."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pymongo.errors import PyMongoError

from news.config import NewsSettings
from news.database import NewsDatabaseError, close_client, get_news_client, get_news_database, ping_database


class TestGetNewsClient:
    def test_get_news_client_creates_client_with_expected_settings(self) -> None:
        settings = NewsSettings(
            mongodb_database="test_news",
            mongodb_uri_file=Path("/fake/uri_file"),
            mongodb_required=True,
            mongodb_timeout_ms=5000,
        )
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


class TestGetNewsDatabase:
    def test_get_news_database_selects_database(self) -> None:
        settings = NewsSettings(
            mongodb_database="test_news",
            mongodb_uri_file=Path("/fake/uri_file"),
            mongodb_required=True,
            mongodb_timeout_ms=5000,
        )
        mock_client = MagicMock()
        with patch("news.database.get_news_client", return_value=mock_client):
            db = get_news_database(settings)
        mock_client.__getitem__.assert_called_once_with("test_news")
        assert db == mock_client["test_news"]


class TestPingDatabase:
    def test_ping_database_success(self) -> None:
        settings = NewsSettings(
            mongodb_database="test_news",
            mongodb_uri_file=Path("/fake/uri_file"),
            mongodb_required=True,
            mongodb_timeout_ms=5000,
        )
        mock_database = MagicMock()
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_database

        with patch("news.database.get_news_client", return_value=mock_client):
            result = ping_database(settings)

        assert result == {"status": "ok", "database": "test_news"}
        mock_database.command.assert_called_once_with("ping")
        mock_client.close.assert_called_once()

    def test_ping_database_failure(self) -> None:
        settings = NewsSettings(
            mongodb_database="test_news",
            mongodb_uri_file=Path("/fake/uri_file"),
            mongodb_required=True,
            mongodb_timeout_ms=5000,
        )
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
        settings = NewsSettings(
            mongodb_database="test_news",
            mongodb_uri_file=Path("/fake/uri_file"),
            mongodb_required=True,
            mongodb_timeout_ms=5000,
        )
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
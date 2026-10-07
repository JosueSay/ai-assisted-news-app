"""Tests offline para drift detection."""

from news.schema.check import check_schema
from news.schema.collections import expected_collections
from news.schema.indexes import expected_indexes
from news.schema.initialize import initialize_schema
from news.schema.validators import expected_validators

from .test_schema_initialize import FakeDatabase


def configured_fake_database() -> FakeDatabase:
    db = FakeDatabase()
    initialize_schema(db)
    return db


def test_schema_check_ok() -> None:
    result = check_schema(configured_fake_database())
    assert result.ok is True
    assert "Database schema: OK" in result.format()


def test_schema_check_detects_missing_collection() -> None:
    db = configured_fake_database()
    db.collections.pop("news")
    db.options.pop("news")

    result = check_schema(db)
    assert result.ok is False
    assert "news" in result.missing_collections


def test_schema_check_detects_validator_drift() -> None:
    db = configured_fake_database()
    db.options["users"]["validator"] = {"$jsonSchema": {"bsonType": "object"}}

    result = check_schema(db)
    assert result.ok is False
    assert "users" in result.validator_drift


def test_schema_check_detects_missing_index() -> None:
    db = configured_fake_database()
    db["news"].indexes.pop("uq_news_slug")

    result = check_schema(db)
    assert result.ok is False
    assert "news.uq_news_slug" in result.missing_indexes


def test_schema_check_detects_ttl_drift() -> None:
    db = configured_fake_database()
    db["chatSessions"].indexes["ttl_chat_sessions_expires_at"]["expireAfterSeconds"] = 3600

    result = check_schema(db)
    assert result.ok is False
    assert "chatSessions.ttl_chat_sessions_expires_at" in result.index_drift

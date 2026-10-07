"""Tests offline para definiciones físicas de MongoDB."""

from news.schema.collections import expected_collections
from news.schema.indexes import expected_indexes, indexes_by_collection
from news.schema.validators import (
    AI_FEATURES,
    INTERACTION_TYPES,
    NEWS_STATUSES,
    VALIDATORS,
    expected_validators,
)


def test_expected_collections_are_exactly_seven() -> None:
    assert expected_collections() == (
        "locations",
        "users",
        "news",
        "userInteractions",
        "chatSessions",
        "aiUsage",
        "auditLogs",
    )


def test_validators_exist_for_every_collection() -> None:
    validators = expected_validators()
    assert set(validators) == set(expected_collections())
    for validator in validators.values():
        assert "$jsonSchema" in validator
        assert validator["$jsonSchema"]["bsonType"] == "object"


def test_critical_enums_are_synchronized() -> None:
    assert NEWS_STATUSES == ["draft", "published"]
    assert INTERACTION_TYPES == ["opened", "read"]
    assert AI_FEATURES == ["chat", "summary", "image_generation", "classification"]
    news_properties = VALIDATORS["news"]["$jsonSchema"]["properties"]
    assert news_properties["status"]["enum"] == NEWS_STATUSES


def test_required_indexes_are_defined() -> None:
    by_name = {index.name: index for index in expected_indexes()}
    assert by_name["uq_users_firebase_uid"].unique is True
    assert by_name["uq_users_firebase_uid"].keys == (("firebaseUid", 1),)
    assert by_name["uq_news_slug"].unique is True
    assert by_name["uq_news_slug"].keys == (("slug", 1),)
    assert by_name["ttl_chat_sessions_expires_at"].expire_after_seconds == 0
    assert by_name["ttl_chat_sessions_expires_at"].keys == (("expiresAt", 1),)


def test_indexes_are_grouped_by_collection() -> None:
    grouped = indexes_by_collection()
    assert "news" in grouped
    assert "users" in grouped
    assert "chatSessions" in grouped
    assert len(grouped["news"]) >= 4

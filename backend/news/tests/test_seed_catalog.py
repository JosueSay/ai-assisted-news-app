"""Tests offline para el seeder de catálogos."""

import pytest
from bson import ObjectId
from pydantic import ValidationError

from news.models import LocationLevel
from news.models.location import Location
from news.seed_catalog import CATALOG_LOCATIONS, seed_catalog_data
from news.tests.test_schema_initialize import FakeDatabase


def _existing_location(code: str, name: str) -> dict:
    return Location(
        _id=ObjectId(),
        name=name,
        city=None,
        region=None,
        country=name,
        countryCode=code,
        level=LocationLevel.country,
        active=True,
    ).model_dump_mongo()


def test_seed_catalog_data_inserts_16_on_empty_db() -> None:
    db = FakeDatabase()

    result = seed_catalog_data(db)

    assert result.inserted == len(CATALOG_LOCATIONS) == 16
    assert result.unchanged == 0
    stored_codes = {doc["countryCode"] for doc in db["locations"].documents.values()}
    assert stored_codes == {item["code"] for item in CATALOG_LOCATIONS}


def test_seed_catalog_data_is_idempotent() -> None:
    db = FakeDatabase()

    first = seed_catalog_data(db)
    second = seed_catalog_data(db)

    assert first.inserted == len(CATALOG_LOCATIONS)
    assert second.inserted == 0
    assert second.unchanged == len(CATALOG_LOCATIONS)


def test_seed_catalog_does_not_duplicate_existing_country_code() -> None:
    db = FakeDatabase()
    db["locations"].insert_one(_existing_location("GT", "Guatemala"))

    result = seed_catalog_data(db)

    matches = [
        doc for doc in db["locations"].documents.values() if doc["countryCode"] == "GT"
    ]
    assert len(matches) == 1
    assert matches[0]["name"] == "Guatemala"
    assert result.inserted == len(CATALOG_LOCATIONS) - 1
    assert result.unchanged == 1


def test_seed_catalog_preserves_unrelated_documents() -> None:
    db = FakeDatabase()
    db["locations"].insert_one(_existing_location("US", "Estados Unidos"))

    seed_catalog_data(db)

    matches = [
        doc for doc in db["locations"].documents.values() if doc["countryCode"] == "US"
    ]
    assert len(matches) == 1
    assert len(db["locations"].documents) == len(CATALOG_LOCATIONS) + 1


def test_seed_catalog_does_not_write_other_collections() -> None:
    db = FakeDatabase()

    seed_catalog_data(db)

    for name in ("users", "news", "userInteractions", "chatSessions", "aiUsage", "auditLogs"):
        assert db[name].documents == {}


def test_invalid_location_document_is_not_persisted() -> None:
    db = FakeDatabase()

    with pytest.raises(ValidationError):
        Location(
            name="X",
            country="X",
            countryCode="XX",
            level="invalid",  # type: ignore[arg-type]
        )

    assert db.list_collection_names() == []

    seed_catalog_data(db)
    for document in db["locations"].documents.values():
        Location.model_validate(document)

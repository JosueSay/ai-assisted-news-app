"""Tests offline para seeders de catálogos."""

from news.seed_catalog import CATALOG_LOCATIONS, seed_catalog_data
from news.tests.test_schema_initialize import FakeDatabase


def test_seed_catalog_data_upserts_required_locations() -> None:
    db = FakeDatabase()

    result = seed_catalog_data(db)

    assert result.locations_upserted == len(CATALOG_LOCATIONS)
    assert "locations" in db.collections
    stored_codes = {
        document["countryCode"]
        for document in db["locations"].documents.values()
    }
    assert stored_codes == {location["code"] for location in CATALOG_LOCATIONS}


def test_seed_catalog_data_is_idempotent() -> None:
    db = FakeDatabase()

    first = seed_catalog_data(db)
    second = seed_catalog_data(db)

    assert first.locations_upserted == len(CATALOG_LOCATIONS)
    assert second.locations_upserted == 0

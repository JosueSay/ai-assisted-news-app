"""Tests offline para la inspección no destructiva del catálogo."""

from bson import ObjectId

from news.models import LocationLevel
from news.models.location import Location
from news.seed_catalog import CATALOG_LOCATIONS, seed_catalog_data
from news.seed_check import check_catalog_data
from news.tests.test_schema_initialize import FakeDatabase


def _location_doc(code: str, name: str) -> dict:
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


def _code(doc_id_key: str, db: FakeDatabase) -> str:
    return db["locations"].documents[doc_id_key]["countryCode"]


def test_check_ok_on_seeded_db() -> None:
    db = FakeDatabase()
    seed_catalog_data(db)

    result = check_catalog_data(db)

    assert result.ok is True
    assert result.missing == []
    assert result.duplicates == []
    assert result.unexpected == []
    assert result.found == len(CATALOG_LOCATIONS)


def test_check_reports_missing_location() -> None:
    db = FakeDatabase()
    seed_catalog_data(db)
    gt_key = next(
        key for key in db["locations"].documents if _code(key, db) == "GT"
    )
    del db["locations"].documents[gt_key]

    result = check_catalog_data(db)

    assert result.ok is False
    assert result.missing == ["GT"]


def test_check_reports_duplicate_country_code() -> None:
    db = FakeDatabase()
    seed_catalog_data(db)
    db["locations"].insert_one(_location_doc("GT", "Guatemala"))

    result = check_catalog_data(db)

    assert result.ok is False
    assert result.duplicates == ["GT"]


def test_check_reports_unexpected_without_deleting() -> None:
    db = FakeDatabase()
    seed_catalog_data(db)
    db["locations"].insert_one(_location_doc("US", "Estados Unidos"))

    result = check_catalog_data(db)

    assert result.ok is False
    assert result.unexpected == ["US"]
    assert any(
        doc["countryCode"] == "US" for doc in db["locations"].documents.values()
    )


def test_check_is_read_only() -> None:
    db = FakeDatabase()
    seed_catalog_data(db)
    before = dict(db["locations"].documents)
    inserts_before = db["locations"].insert_calls

    check_catalog_data(db)

    assert db["locations"].documents == before
    assert db["locations"].insert_calls == inserts_before
    for collection in db.collections.values():
        assert collection.drop_calls == 0

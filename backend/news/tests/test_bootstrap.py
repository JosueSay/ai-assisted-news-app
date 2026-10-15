"""Tests offline para el bootstrap idempotente (Loop 06).

`bootstrap` prepara schema + dataset demo sin eliminar nada:
db-init + db-seed-catalogs + db-seed-news + checks. Offline con fakes.
"""

from bson import ObjectId

from news.schema.check import check_schema
from news.seed_check import check_catalog_data
from news.news_check import check_news_data
from news.tests.test_reseed import TrackedFakeDatabase


def test_bootstrap_on_empty_db_builds_schema_16_and_32() -> None:
    from news.bootstrap import bootstrap_data

    db = TrackedFakeDatabase()
    result = bootstrap_data(db)

    assert result.ok is True
    assert result.schema_ok is True
    assert result.catalog_ok is True
    assert result.news_ok is True
    assert len(db.list_collection_names()) == 7
    assert len(db["locations"].documents) == 16
    assert len(db["news"].documents) == 32
    assert result.inserted_locations == 16
    assert result.inserted_news == 32
    assert check_schema(db).ok is True
    assert check_catalog_data(db).ok is True
    assert check_news_data(db).ok is True


def test_bootstrap_second_run_has_no_duplicates() -> None:
    from news.bootstrap import bootstrap_data

    db = TrackedFakeDatabase()
    bootstrap_data(db)
    second = bootstrap_data(db)

    assert second.ok is True
    assert second.inserted_locations == 0
    assert second.inserted_news == 0
    assert len(db["locations"].documents) == 16
    assert len(db["news"].documents) == 32
    codes = [doc["countryCode"] for doc in db["locations"].documents.values()]
    slugs = [doc["slug"] for doc in db["news"].documents.values()]
    assert len(set(codes)) == 16
    assert len(set(slugs)) == 32


def test_bootstrap_never_deletes_and_preserves_foreign_docs() -> None:
    from news.bootstrap import bootstrap_data

    db = TrackedFakeDatabase()
    ext_location = {
        "_id": ObjectId(),
        "name": "Estados Unidos",
        "country": "Estados Unidos",
        "countryCode": "US",
        "level": "country",
        "active": True,
    }
    db["locations"].insert_one(ext_location)
    user_doc = {"_id": ObjectId(), "marker": "keep-users"}
    db["users"].insert_one(user_doc)

    result = bootstrap_data(db)

    assert result.ok is False  # checks estrictos reportan el externo
    assert db["locations"].documents[ext_location["_id"]] == ext_location
    assert db["users"].documents[user_doc["_id"]] == user_doc
    assert db.deletes == []
    assert len(db["locations"].documents) == 17
    assert len(db["news"].documents) == 32

"""Tests offline para la verificación integral no destructiva (Loop 06).

`verify` solo lee: schema check + catalog check + news check.
Nunca reseed ni escribe. Offline con fakes.
"""

from news.seed_catalog import seed_catalog_data
from news.seed_news import seed_news_data
from news.tests.test_reseed import TrackedFakeDatabase


def _verified_db() -> TrackedFakeDatabase:
    db = TrackedFakeDatabase()
    seed_catalog_data(db)
    seed_news_data(db)
    return db


def _snapshot(db: TrackedFakeDatabase) -> dict:
    return {name: dict(db.collections[name].documents) for name in db.collections}


def test_verify_ok_on_healthy_db() -> None:
    from news.verify import verify_data

    db = _verified_db()
    result = verify_data(db, mode="local", database_name=db.name)

    assert result.ok is True
    assert result.schema_ok is True
    assert result.catalog_ok is True
    assert result.news_ok is True
    assert "Database verification: OK" in result.format()


def test_verify_fails_on_schema_drift() -> None:
    from news.verify import verify_data

    db = _verified_db()
    db.options["users"] = {}

    result = verify_data(db, mode="local", database_name=db.name)

    assert result.ok is False
    assert result.schema_ok is False
    assert "Schema: DRIFT" in result.format()


def test_verify_fails_on_catalog_drift() -> None:
    from news.verify import verify_data

    db = _verified_db()
    key = next(iter(db["locations"].documents))
    del db["locations"].documents[key]

    result = verify_data(db, mode="local", database_name=db.name)

    assert result.ok is False
    assert result.catalog_ok is False
    assert "Catalogs: DRIFT" in result.format()


def test_verify_fails_on_news_drift() -> None:
    from news.verify import verify_data

    db = _verified_db()
    key = next(iter(db["news"].documents))
    del db["news"].documents[key]

    result = verify_data(db, mode="local", database_name=db.name)

    assert result.ok is False
    assert result.news_ok is False
    assert "Demo news: DRIFT" in result.format()


def test_verify_is_read_only() -> None:
    from news.verify import verify_data

    db = _verified_db()
    before = _snapshot(db)
    inserts_before = {
        name: db.collections[name].insert_calls for name in db.collections
    }

    verify_data(db, mode="local", database_name=db.name)

    assert _snapshot(db) == before
    assert {
        name: db.collections[name].insert_calls for name in db.collections
    } == inserts_before
    assert db.deletes == []

"""Tests offline para la inspección no destructiva de noticias demo (Loop 05)."""

from bson import ObjectId

from news.demo_news import get_demo_news_documents
from news.news_check import check_news_data
from news.seed_news import seed_news_data
from news.tests.test_schema_initialize import FakeDatabase


def test_news_check_ok_on_seeded_db() -> None:
    db = FakeDatabase()
    seed_news_data(db)

    result = check_news_data(db)

    assert result.ok is True
    assert result.missing == []
    assert result.duplicates == []
    assert result.country_gaps == {}
    assert result.invalid_topics == []
    assert result.external == []


def test_news_check_reports_missing_slug() -> None:
    db = FakeDatabase()
    seed_news_data(db)
    slug = get_demo_news_documents()[0]["slug"]
    key = next(
        key
        for key, doc in db["news"].documents.items()
        if doc.get("slug") == slug
    )
    del db["news"].documents[key]

    result = check_news_data(db)

    assert result.ok is False
    assert slug in result.missing


def test_news_check_reports_duplicate_slug() -> None:
    db = FakeDatabase()
    seed_news_data(db)
    original = get_demo_news_documents()[0]
    duplicate = dict(original)
    duplicate["_id"] = ObjectId()
    db["news"].insert_one(duplicate)

    result = check_news_data(db)

    assert result.ok is False
    assert original["slug"] in result.duplicates


def test_news_check_reports_incomplete_country() -> None:
    db = FakeDatabase()
    seed_news_data(db)
    documents = [doc for doc in db["news"].documents.values() if doc.get("slug")]
    first = sorted(documents, key=lambda doc: doc["slug"])[0]
    del db["news"].documents[first["_id"]]

    result = check_news_data(db)

    assert result.ok is False
    assert result.missing
    assert result.country_gaps


def test_news_check_reports_invalid_topic() -> None:
    db = FakeDatabase()
    seed_news_data(db)
    key = next(iter(db["news"].documents))
    db["news"].documents[key] = dict(db["news"].documents[key])
    db["news"].documents[key]["topics"] = ["tema_inventado"]

    result = check_news_data(db)

    assert result.ok is False
    assert result.invalid_topics


def test_news_check_reports_external_without_deleting() -> None:
    db = FakeDatabase()
    seed_news_data(db)
    db["news"].insert_one(
        {"_id": ObjectId(), "slug": "noticia-ajena-fuera-del-dataset"}
    )

    result = check_news_data(db)

    assert result.ok is False
    assert "noticia-ajena-fuera-del-dataset" in result.external
    assert any(
        doc.get("slug") == "noticia-ajena-fuera-del-dataset"
        for doc in db["news"].documents.values()
    )


def test_news_check_is_read_only() -> None:
    db = FakeDatabase()
    seed_news_data(db)
    before = dict(db["news"].documents)
    inserts_before = db["news"].insert_calls

    check_news_data(db)

    assert db["news"].documents == before
    assert db["news"].insert_calls == inserts_before
    for collection in db.collections.values():
        assert collection.drop_calls == 0

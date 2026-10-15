"""Tests offline para el seeder idempotente de noticias demo (Loop 05).

El seeder solo escribe en `news`: nunca crea users ni toca otras colecciones.
"""

import pytest
from pydantic import ValidationError

from news.demo_news import EXPECTED_NEWS_COUNT, get_demo_news_documents
from news.seed_news import seed_news_data
from news.tests.test_schema_initialize import FakeDatabase


def test_seed_news_inserts_32_on_empty_db() -> None:
    db = FakeDatabase()

    result = seed_news_data(db)

    assert result.inserted == EXPECTED_NEWS_COUNT == 32
    assert result.unchanged == 0
    assert len(db["news"].documents) == EXPECTED_NEWS_COUNT


def test_seed_news_is_idempotent_on_second_run() -> None:
    db = FakeDatabase()

    first = seed_news_data(db)
    second = seed_news_data(db)

    assert first.inserted == EXPECTED_NEWS_COUNT
    assert second.inserted == 0
    assert second.unchanged == EXPECTED_NEWS_COUNT
    assert len(db["news"].documents) == EXPECTED_NEWS_COUNT


def test_seed_news_does_not_modify_existing_slug() -> None:
    db = FakeDatabase()
    seed_news_data(db)
    slug = get_demo_news_documents()[0]["slug"]
    before = dict(db["news"].find_one({"slug": slug}))

    result = seed_news_data(db)

    assert result.inserted == 0
    assert result.unchanged == EXPECTED_NEWS_COUNT
    assert db["news"].find_one({"slug": slug}) == before


def test_seed_news_preserves_foreign_documents() -> None:
    db = FakeDatabase()
    foreign = {
        "_id": "foreign-id",
        "slug": "noticia-ajena-fuera-del-dataset",
        "title": "Ajena",
    }
    db["news"].documents["foreign-id"] = foreign

    result = seed_news_data(db)

    assert result.inserted == EXPECTED_NEWS_COUNT
    assert db["news"].documents["foreign-id"] == foreign
    assert len(db["news"].documents) == EXPECTED_NEWS_COUNT + 1


def test_seed_news_does_not_write_other_collections() -> None:
    db = FakeDatabase()

    seed_news_data(db)

    for name in ("users", "locations", "userInteractions", "chatSessions", "aiUsage", "auditLogs"):
        assert db[name].documents == {}


def test_seed_news_rejects_invalid_document_without_persisting() -> None:
    db = FakeDatabase()
    documents = get_demo_news_documents()
    documents[0] = dict(documents[0])
    documents[0]["status"] = "deleted"

    with pytest.raises(ValidationError):
        seed_news_data(db, documents=documents)

    assert db["news"].documents == {}

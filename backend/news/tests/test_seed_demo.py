"""Tests offline para el seeder demo."""

from news.seed_demo import DEMO_NEWS, seed_demo_data
from news.tests.test_schema_initialize import FakeDatabase


def test_seed_demo_data_upserts_demo_documents() -> None:
    db = FakeDatabase()
    result = seed_demo_data(db)

    assert result.news_upserted == len(DEMO_NEWS)
    assert "locations" in db.collections
    assert "users" in db.collections
    assert "news" in db.collections


def test_seed_demo_data_is_idempotent() -> None:
    db = FakeDatabase()
    first = seed_demo_data(db)
    second = seed_demo_data(db)

    assert first.news_upserted == len(DEMO_NEWS)
    assert second.news_upserted == 0

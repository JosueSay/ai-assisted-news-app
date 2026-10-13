"""Tests offline para el generador determinista de noticias demo (Loop 05).

Todo el contenido generado es sintético (DEMO / SYNTHETIC DATA): no representa
acontecimientos reales ni utiliza IA, red ni APIs externas.
"""

from news.demo_news import (
    EXPECTED_NEWS_COUNT,
    get_demo_news_documents,
)
from news.models.news import News
from news.models.reading_time import compute_reading_time
from news.seed_catalog import CATALOG_LOCATION_IDS, CATALOG_LOCATIONS
from news.topics import TOPICS


def _documents():
    return get_demo_news_documents()


def test_generator_produces_exactly_32_news() -> None:
    assert len(_documents()) == EXPECTED_NEWS_COUNT == 32


def test_generator_slugs_are_unique_stable_and_readable() -> None:
    first = _documents()
    second = _documents()
    slugs = [doc["slug"] for doc in first]
    assert len(set(slugs)) == len(slugs) == 32
    assert [doc["slug"] for doc in second] == slugs
    for slug in slugs:
        assert slug == slug.strip().lower()
        assert len(slug) >= 8


def test_generator_is_deterministic() -> None:
    assert _documents() == _documents()


def test_generator_covers_16_countries_with_2_news_each() -> None:
    documents = _documents()
    expected_ids = set(CATALOG_LOCATION_IDS.values())
    assert len(CATALOG_LOCATIONS) == 16
    counts: dict[str, int] = {}
    for doc in documents:
        scope = doc["geographicScope"]
        assert scope["level"] == "country"
        assert len(scope["locationIds"]) == 1
        location_id = scope["locationIds"][0]
        assert location_id in expected_ids
        counts[location_id] = counts.get(location_id, 0) + 1
    assert len(counts) == 16
    assert set(counts.values()) == {2}


def test_generator_topics_are_valid_bounded_and_cover_catalog() -> None:
    documents = _documents()
    seen: set[str] = set()
    for doc in documents:
        topics = doc["topics"]
        assert 1 <= len(topics) <= 3
        assert len(set(topics)) == len(topics)
        for topic in topics:
            assert topic in TOPICS
            seen.add(topic)
    assert seen == set(TOPICS)


def test_generator_status_distribution_is_28_published_4_draft() -> None:
    documents = _documents()
    published = [doc for doc in documents if doc["status"] == "published"]
    drafts = [doc for doc in documents if doc["status"] == "draft"]
    assert len(published) == 28
    assert len(drafts) == 4
    draft_countries = set()
    for doc in drafts:
        assert doc["publishedAt"] is None
        draft_countries.add(doc["geographicScope"]["locationIds"][0])
    assert len(draft_countries) == 4
    for doc in published:
        assert doc["publishedAt"] is not None


def test_generator_covers_all_verification_statuses() -> None:
    documents = _documents()
    statuses = {doc["verification"]["status"] for doc in documents}
    assert statuses == {
        "confirmed",
        "developing",
        "insufficient_sources",
        "conflicting_sources",
    }
    confirmed = sum(
        1 for doc in documents if doc["verification"]["status"] == "confirmed"
    )
    assert confirmed > len(documents) / 2


def test_generator_sources_are_synthetic_demo() -> None:
    documents = _documents()
    for doc in documents:
        for source in doc["sources"]:
            assert "demo" in source["name"].lower()
            assert source["url"].startswith("https://example.com/")
    insufficient = [
        doc
        for doc in documents
        if doc["verification"]["status"] == "insufficient_sources"
    ]
    assert insufficient
    for doc in insufficient:
        assert len(doc["sources"]) <= 1
    conflicting = [
        doc
        for doc in documents
        if doc["verification"]["status"] == "conflicting_sources"
    ]
    assert conflicting
    for doc in conflicting:
        assert len(doc["sources"]) >= 2


def test_generator_covers_required_image_types_with_coherent_disclosure() -> None:
    documents = _documents()
    types = {doc["image"]["type"] for doc in documents}
    assert {
        "ai_generated",
        "ai_modified",
        "illustration",
        "photograph",
        "none",
    } <= types
    for doc in documents:
        image = doc["image"]
        if image["type"] in {"ai_generated", "ai_modified"}:
            assert image["aiDisclosure"] and image["aiDisclosure"].strip()
        if image["type"] == "none":
            assert image["url"] is None
            assert image["alt"] is None
        assert doc["aiAssistance"]["imageGenerated"] is (
            image["type"] == "ai_generated"
        )


def test_generator_documents_validate_with_news_model() -> None:
    for doc in _documents():
        News.model_validate(doc)


def test_generator_reading_times_are_coherent_and_varied() -> None:
    documents = _documents()
    minutes = set()
    for doc in documents:
        if doc["status"] != "published":
            continue
        expected_wc, expected_min = compute_reading_time(doc["content"])
        assert doc["wordCount"] == expected_wc
        assert doc["estimatedReadingMinutes"] == expected_min
        minutes.add(expected_min)
    assert 1 in minutes
    assert any(value >= 2 for value in minutes)
    assert any(value >= 3 for value in minutes)


def test_generator_content_is_clearly_synthetic() -> None:
    for doc in _documents():
        notes = doc["verification"]["notes"] or ""
        assert "DEMO" in notes.upper() or "SYNTHETIC" in notes.upper()

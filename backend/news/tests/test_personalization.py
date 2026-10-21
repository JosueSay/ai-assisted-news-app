from datetime import datetime, timedelta, timezone

from bson import ObjectId

from news.personalization import compose_feed, rank_news


NOW = datetime(2026, 10, 18, tzinfo=timezone.utc)
LOCATION = ObjectId("670000000000000000000001")


def article(slug, *, days_ago=0, topics=(), location_ids=(), level="country"):
    return {
        "_id": ObjectId(),
        "slug": slug,
        "topics": list(topics),
        "publishedAt": NOW - timedelta(days=days_ago),
        "geographicScope": {"level": level, "locationIds": list(location_ids)},
    }


def profile(*, topics=(), interests=(), location=LOCATION):
    return {
        "simulatedLocationId": location,
        "onboarding": {"selectedTopics": list(topics)},
        "inferredInterests": [
            {"topic": topic, "score": score} for topic, score in interests
        ],
    }


def test_rank_news_combines_geography_declared_inferred_and_freshness():
    local_interest = article(
        "local-interest",
        days_ago=1,
        topics=["tecnologia"],
        location_ids=[LOCATION],
    )
    recent = article("recent", days_ago=0, topics=["deportes"])

    ranked = rank_news(
        [recent, local_interest],
        profile(topics=["tecnologia"], interests=[("tecnologia", 0.5)]),
        now=NOW,
    )

    assert [item["document"]["slug"] for item in ranked] == [
        "local-interest",
        "recent",
    ]
    assert ranked[0]["reason"] == "Por tu ubicación"
    assert ranked[0]["score"] == 30 + 20 + 10 + (20 * 13 / 14)


def test_rank_news_decays_freshness_and_uses_stable_ties():
    first = article("a", days_ago=14)
    second = article("b", days_ago=14)
    first["_id"] = ObjectId("670000000000000000000001")
    second["_id"] = ObjectId("670000000000000000000002")

    ranked = rank_news([second, first], profile(), now=NOW)

    assert [item["document"]["slug"] for item in ranked] == ["a", "b"]
    assert ranked[0]["score"] == 0


def test_same_candidates_rank_differently_for_two_profiles():
    other_location = ObjectId("670000000000000000000002")
    technology = article(
        "technology-local",
        days_ago=2,
        topics=["tecnologia"],
        location_ids=[LOCATION],
    )
    culture = article(
        "culture-local",
        days_ago=2,
        topics=["cultura"],
        location_ids=[other_location],
    )

    first_profile = rank_news(
        [culture, technology],
        profile(topics=["tecnologia"], location=LOCATION),
        now=NOW,
    )
    second_profile = rank_news(
        [culture, technology],
        profile(topics=["cultura"], location=other_location),
        now=NOW,
    )

    assert first_profile[0]["document"]["slug"] == "technology-local"
    assert second_profile[0]["document"]["slug"] == "culture-local"


def test_compose_feed_reserves_positions_four_and_nine_when_available():
    local = [article(f"local-{index}", days_ago=index, location_ids=[LOCATION]) for index in range(10)]
    broad = [
        article("international", days_ago=1, level="international"),
        article("other-country", days_ago=2, location_ids=[ObjectId("670000000000000000000002")]),
    ]
    ranked = rank_news(local + broad, profile(), now=NOW)

    composed = compose_feed(ranked, profile())
    slugs = [item["document"]["slug"] for item in composed]

    assert slugs[3] == "international"
    assert slugs[8] == "other-country"
    assert composed[3]["reason"] == "Para ampliar tu cobertura"
    assert composed[8]["reason"] == "Para ampliar tu cobertura"
    assert len(slugs) == len(set(slugs))


def test_focused_profile_still_sees_other_geographic_coverage():
    technology_news = [
        article(
            f"technology-{index}",
            days_ago=index,
            topics=["tecnologia"],
            location_ids=[LOCATION],
        )
        for index in range(10)
    ]
    international_news = [
        article(f"international-{index}", days_ago=index, topics=["cultura"], level="international")
        for index in range(2)
    ]
    focused_profile = profile(
        topics=["tecnologia"], interests=[("tecnologia", 1.0)]
    )
    composed = compose_feed(
        rank_news(technology_news + international_news, focused_profile, now=NOW),
        focused_profile,
    )

    assert composed[0]["document"]["topics"] == ["tecnologia"]
    assert composed[3]["document"]["geographicScope"]["level"] == "international"
    assert composed[8]["document"]["geographicScope"]["level"] == "international"


def test_compose_feed_fills_reserved_positions_when_diverse_content_is_missing():
    ranked = rank_news(
        [article(f"local-{index}", days_ago=index, location_ids=[LOCATION]) for index in range(4)],
        profile(),
        now=NOW,
    )

    composed = compose_feed(ranked, profile())

    assert len(composed) == 4
    assert [item["document"]["slug"] for item in composed] == [
        "local-0",
        "local-1",
        "local-2",
        "local-3",
    ]


def test_diversity_slots_choose_recency_over_declared_and_inferred_interests():
    reader = profile(topics=["tecnologia"], interests=[("tecnologia", 1.0)])
    local = [
        article(f"local-{index}", topics=["tecnologia"], location_ids=[LOCATION])
        for index in range(10)
    ]
    broad = [
        article("old-interest", days_ago=10, topics=["tecnologia"], level="international"),
        article("recent-country", location_ids=[ObjectId()], topics=["cultura"]),
        article("recent-international", days_ago=1, level="international", topics=["ciencia"]),
    ]
    ranked = rank_news(local + broad, reader, now=NOW)

    composed = compose_feed(ranked, reader)

    assert composed[:3] == ranked[:3]
    assert composed[3]["document"]["slug"] == "recent-country"
    assert composed[8]["document"]["slug"] == "recent-international"
    assert len({item["document"]["_id"] for item in composed}) == len(composed)


def test_diversity_recency_ties_use_id_and_missing_dates_come_last():
    reader = profile(topics=["tecnologia"])
    local = [
        article(f"local-{index}", topics=["tecnologia"], location_ids=[LOCATION])
        for index in range(10)
    ]
    first = article("first", location_ids=[ObjectId()])
    second = article("second", topics=["tecnologia"], level="international")
    undated = article("undated", topics=["tecnologia"], level="international")
    first["_id"] = ObjectId("670000000000000000000001")
    second["_id"] = ObjectId("670000000000000000000002")
    undated["publishedAt"] = None

    composed = compose_feed(rank_news(local + [undated, second, first], reader, now=NOW), reader)

    assert composed[3]["document"]["slug"] == "first"
    assert composed[8]["document"]["slug"] == "second"

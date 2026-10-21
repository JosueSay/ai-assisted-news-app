from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from bson import ObjectId

from news.interactions import record_interaction


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = list(documents)
        self.fail_updates = 0

    def find_one(self, query, _projection=None):
        return next(
            (
                item
                for item in self.documents
                if all(item.get(key) == value for key, value in query.items())
            ),
            None,
        )

    def insert_one(self, document):
        self.documents.append(document)
        return SimpleNamespace(inserted_id=document["_id"])

    def update_one(self, query, update):
        if self.fail_updates:
            self.fail_updates -= 1
            raise RuntimeError("controlled update failure")
        document = self.find_one(query)
        if document:
            document.update(update.get("$set", {}))
        return SimpleNamespace(matched_count=1 if document else 0)

    def find(self, query):
        return [
            item
            for item in self.documents
            if all(item.get(key) == value for key, value in query.items())
        ]


class FakeDatabase:
    def __init__(self, user, news_documents=()):
        self.collections = {
            "users": FakeCollection([user]),
            "userInteractions": FakeCollection(),
            "news": FakeCollection(news_documents),
        }

    def __getitem__(self, name):
        return self.collections[name]


def test_open_is_deduplicated_preserves_context_and_learns_once():
    user_id = ObjectId()
    news_id = ObjectId()
    location_id = ObjectId()
    user = {
        "_id": user_id,
        "simulatedLocationId": location_id,
        "inferredInterests": [],
    }
    news = {"_id": news_id, "topics": ["tecnologia"]}
    database = FakeDatabase(user, [news])
    now = datetime(2026, 10, 18, tzinfo=timezone.utc)

    first, created = record_interaction(
        database, user, news, "opened", feed_position=4, now=now
    )
    brief, brief_duplicate = record_interaction(
        database,
        user,
        news,
        "opened",
        feed_position=99,
        dwell_time_seconds=20,
        now=now,
    )
    assert brief_duplicate is False
    assert brief["dwellTimeSeconds"] == 20
    assert database["users"].documents[0]["inferredInterests"] == []

    updated, duplicate = record_interaction(
        database,
        user,
        news,
        "opened",
        feed_position=99,
        dwell_time_seconds=35,
        now=now,
    )
    repeated, repeated_duplicate = record_interaction(
        database,
        user,
        news,
        "opened",
        feed_position=99,
        dwell_time_seconds=40,
        now=now,
    )

    assert created is True
    assert duplicate is False
    assert repeated_duplicate is False
    assert first["context"]["feedPosition"] == 4
    assert updated["context"]["feedPosition"] == 4
    assert repeated["dwellTimeSeconds"] == 40
    assert len(database["userInteractions"].documents) == 1
    assert database["users"].documents[0]["inferredInterests"][0]["score"] == 0.02


def test_read_requires_open_and_retry_does_not_duplicate_learning():
    user_id = ObjectId()
    user = {"_id": user_id, "simulatedLocationId": ObjectId(), "inferredInterests": []}
    news = {"_id": ObjectId(), "topics": ["tecnologia", "ciencia"]}
    database = FakeDatabase(user, [news])

    with pytest.raises(ValueError, match="apertura"):
        record_interaction(database, user, news, "read")

    record_interaction(database, user, news, "opened", feed_position=2)
    first, created = record_interaction(
        database, user, news, "read", dwell_time_seconds=47
    )
    second, duplicate = record_interaction(
        database, user, news, "read", dwell_time_seconds=47
    )

    assert created is True
    assert duplicate is False
    assert first["context"] == second["context"]
    assert first["context"]["feedPosition"] == 2
    assert len(database["userInteractions"].documents) == 2
    assert {
        item["topic"]: item["score"]
        for item in database["users"].documents[0]["inferredInterests"]
    } == {"tecnologia": 0.08, "ciencia": 0.08}


def test_interest_scores_are_capped_at_one():
    user = {
        "_id": ObjectId(),
        "simulatedLocationId": ObjectId(),
        "inferredInterests": [],
    }
    news_documents = [
        {"_id": ObjectId(), "topics": ["tecnologia"]} for _ in range(13)
    ]
    database = FakeDatabase(user, news_documents)
    for news in news_documents:
        record_interaction(database, user, news, "opened", dwell_time_seconds=30)
        record_interaction(database, user, news, "read", dwell_time_seconds=60)

    assert database["users"].documents[0]["inferredInterests"][0]["score"] == 1.0


def test_interaction_learning_isolated_between_users():
    first_user = {
        "_id": ObjectId(),
        "simulatedLocationId": ObjectId(),
        "inferredInterests": [],
    }
    second_user = {
        "_id": ObjectId(),
        "simulatedLocationId": ObjectId(),
        "inferredInterests": [],
    }
    news = {"_id": ObjectId(), "topics": ["ciencia"]}
    database = FakeDatabase(first_user, [news])
    database["users"].documents.append(second_user)

    for user in (first_user, second_user):
        record_interaction(database, user, news, "opened", feed_position=1)
        record_interaction(database, user, news, "read", dwell_time_seconds=60)

    scores = {
        user["_id"]: user["inferredInterests"][0]["score"]
        for user in database["users"].documents
    }
    assert scores == {first_user["_id"]: 0.08, second_user["_id"]: 0.08}
    assert len(database["userInteractions"].documents) == 4


def test_retry_reconciles_interests_after_persisted_read_and_failed_profile_update():
    user = {"_id": ObjectId(), "simulatedLocationId": ObjectId(), "inferredInterests": []}
    news = {"_id": ObjectId(), "topics": ["ciencia"]}
    database = FakeDatabase(user, [news])
    record_interaction(database, user, news, "opened")
    database["users"].fail_updates = 1

    with pytest.raises(RuntimeError, match="controlled"):
        record_interaction(database, user, news, "read", dwell_time_seconds=45)

    interaction, created = record_interaction(
        database, user, news, "read", dwell_time_seconds=45
    )

    assert created is False
    assert interaction["type"] == "read"
    assert len(database["userInteractions"].documents) == 2
    assert database["users"].documents[0]["inferredInterests"][0]["score"] == 0.08

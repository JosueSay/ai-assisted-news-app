from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from bson import ObjectId

from news.firebase_auth import FirebaseIdentity
from news.user_accounts import ensure_news_user


class Collection:
    def __init__(self, documents=()) -> None:
        self.documents = list(documents)

    def find_one(self, query, _projection=None):
        return next(
            (document for document in self.documents if all(document.get(k) == v for k, v in query.items())),
            None,
        )

    def insert_one(self, document):
        self.documents.append(document)
        return SimpleNamespace(inserted_id=document["_id"])

    def update_one(self, query, update):
        document = self.find_one(query)
        if document:
            document.update(update.get("$set", {}))
        return SimpleNamespace(matched_count=1 if document else 0)


class Database:
    def __init__(self, *, user=None):
        self.collections = {
            "locations": Collection(
                [{"_id": ObjectId("670000000000000000000001"), "countryCode": "GT", "active": True}]
            ),
            "users": Collection([user] if user else []),
        }

    def __getitem__(self, name):
        return self.collections[name]


def test_new_firebase_identity_creates_a_regular_user() -> None:
    database = Database()
    now = datetime(2026, 10, 17, tzinfo=timezone.utc)

    user = ensure_news_user(
        database,
        FirebaseIdentity("firebase-uid-1", "reader@example.test", "Reader"),
        now=now,
    )

    assert user["firebaseUid"] == "firebase-uid-1"
    assert user["email"] == "reader@example.test"
    assert user["displayName"] == "Reader"
    assert user["role"] == "user"
    assert user["simulatedLocationId"] == ObjectId("670000000000000000000001")
    assert user["lastLoginAt"] == now


def test_existing_admin_role_preferences_and_location_are_not_overwritten() -> None:
    user_id = ObjectId("670000000000000000000099")
    location_id = ObjectId("670000000000000000000002")
    database = Database(
        user={
            "_id": user_id,
            "firebaseUid": "firebase-admin-uid",
            "email": "old@example.test",
            "displayName": "Old Name",
            "photoUrl": "",
            "role": "admin",
            "simulatedLocationId": location_id,
            "onboarding": {"selectedTopics": ["tecnologia"]},
        }
    )

    user = ensure_news_user(
        database,
        FirebaseIdentity("firebase-admin-uid", "admin@example.test", "New Name"),
    )

    assert user["_id"] == user_id
    assert user["role"] == "admin"
    assert user["simulatedLocationId"] == location_id
    assert user["onboarding"]["selectedTopics"] == ["tecnologia"]
    assert user["email"] == "admin@example.test"
    assert user["displayName"] == "New Name"
    assert len(database["users"].documents) == 1


def test_anonymous_profile_does_not_erase_existing_profile_claims() -> None:
    database = Database(
        user={
            "_id": ObjectId(),
            "firebaseUid": "anonymous-uid",
            "email": "reader@example.test",
            "displayName": "Reader",
            "photoUrl": "https://example.test/photo.png",
            "role": "user",
        }
    )

    user = ensure_news_user(database, FirebaseIdentity("anonymous-uid"))

    assert user["email"] == "reader@example.test"
    assert user["displayName"] == "Reader"
    assert user["photoUrl"] == "https://example.test/photo.png"

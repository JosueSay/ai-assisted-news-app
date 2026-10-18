from __future__ import annotations

from types import SimpleNamespace

from bson import ObjectId
from fastapi.testclient import TestClient

from news.api import create_app
from news.firebase_auth import FirebaseAuthenticationError, FirebaseIdentity


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = list(documents)

    def find_one(self, query, _projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return document
        return None

    def insert_one(self, document):
        self.documents.append(document)
        return SimpleNamespace(inserted_id=document["_id"])

    def update_one(self, query, update):
        document = self.find_one(query)
        if document:
            document.update(update.get("$set", {}))
        return SimpleNamespace(matched_count=1 if document else 0)


class FakeDatabase:
    def __init__(self):
        self.collections = {
            "locations": FakeCollection(
                [
                    {
                        "_id": ObjectId("670000000000000000000001"),
                        "name": "Guatemala",
                        "country": "Guatemala",
                        "countryCode": "GT",
                        "level": "country",
                        "active": True,
                    }
                ]
            ),
            "users": FakeCollection(),
            "news": FakeCollection(),
            "auditLogs": FakeCollection(),
        }

    def __getitem__(self, name):
        return self.collections[name]


class FakeClient:
    def __init__(self, database):
        self.database = database

    def __getitem__(self, _name):
        return self.database

    def close(self):
        pass


def test_api_requires_firebase_token_and_resolves_identity_from_verified_claims(monkeypatch):
    database = FakeDatabase()
    settings = SimpleNamespace(
        firebase_project_id="news-project",
        mongodb_database="ai_assisted_news",
    )
    monkeypatch.setattr("news.api.get_news_settings", lambda: settings)
    monkeypatch.setattr("news.api.get_news_client", lambda _settings: FakeClient(database))

    def verify(authorization, project_id):
        if authorization != "Bearer valid-token" or project_id != "news-project":
            raise FirebaseAuthenticationError("invalid")
        return FirebaseIdentity("firebase-reader-uid", "reader@example.test", "Reader")

    monkeypatch.setattr("news.api.verify_firebase_bearer", verify)
    with TestClient(create_app()) as client:
        assert client.get("/auth/me").status_code == 401
        assert client.get(
            "/auth/me", headers={"Authorization": "Bearer forged"}
        ).status_code == 401
        response = client.get("/auth/me", headers={"Authorization": "Bearer valid-token"})

    assert response.status_code == 200
    assert response.json() == {
        "id": str(database["users"].documents[0]["_id"]),
        "firebaseUid": "firebase-reader-uid",
        "email": "reader@example.test",
        "displayName": "Reader",
        "photoUrl": "",
        "role": "user",
    }


def test_only_database_admin_can_create_news_not_client_role(monkeypatch):
    database = FakeDatabase()
    settings = SimpleNamespace(
        firebase_project_id="news-project",
        mongodb_database="ai_assisted_news",
    )
    monkeypatch.setattr("news.api.get_news_settings", lambda: settings)
    monkeypatch.setattr("news.api.get_news_client", lambda _settings: FakeClient(database))
    identities = {
        "Bearer reader-token": FirebaseIdentity("firebase-reader-uid", "reader@example.test", "Reader"),
        "Bearer admin-token": FirebaseIdentity("firebase-admin-uid", "admin@example.test", "Admin"),
    }

    def verify(authorization, _project_id):
        if authorization not in identities:
            raise FirebaseAuthenticationError("invalid")
        return identities[authorization]

    monkeypatch.setattr("news.api.verify_firebase_bearer", verify)
    payload = {
        "title": "Nota autorizada",
        "summary": "Resumen editorial",
        "content": "Contenido de prueba.",
        "topic": "actualidad",
        "locationId": "670000000000000000000001",
        "status": "draft",
        "role": "admin",
    }
    with TestClient(create_app()) as client:
        reader_headers = {"Authorization": "Bearer reader-token"}
        assert client.get("/auth/me", headers=reader_headers).status_code == 200
        assert client.post("/admin/news", json=payload, headers=reader_headers).status_code == 403

        admin_headers = {"Authorization": "Bearer admin-token"}
        admin_profile = client.get("/auth/me", headers=admin_headers)
        admin_uid = admin_profile.json()["firebaseUid"]
        database["users"].update_one(
            {"firebaseUid": admin_uid}, {"$set": {"role": "admin"}}
        )
        assert client.post("/admin/login", json={"username": "admin", "password": "x"}).status_code == 404
        response = client.post("/admin/news", json=payload, headers=admin_headers)

    assert response.status_code == 201
    admin = database["users"].find_one({"firebaseUid": "firebase-admin-uid"})
    assert database["news"].documents[0]["authorId"] == admin["_id"]
    assert database["auditLogs"].documents[0]["actorId"] == admin["_id"]

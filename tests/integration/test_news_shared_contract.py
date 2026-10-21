"""Flujo real sobre MongoDB efímera, nunca sobre Atlas ni una DB del desarrollador."""

import os
import time

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo import MongoClient

HOST = os.getenv("NEWS_TEST_MONGO_HOST", "")
pytestmark = pytest.mark.skipif(
    not HOST, reason="Usar make news-integration-test (MongoDB efímera)"
)


def test_canonical_bootstrap_api_chat_and_admin_share_one_schema(monkeypatch, tmp_path):
    assert HOST.startswith("news-contract-mongo-") and all(
        c.isalnum() or c == "-" for c in HOST
    )
    database_name = "ai_assisted_news_contract_test"
    uri = f"mongodb://{HOST}:27017/{database_name}"
    for key, value in {
        "NEWS_DB_MODE": "local",
        "NEWS_MONGODB_LOCAL_URI": uri,
        "NEWS_MONGODB_DATABASE": database_name,
        "CHATBOT_PROVIDER": "stub",
        "MONGODB_CONTEXT_MODE": "news",
        "MONGODB_REQUIRED": "true",
        "OPENAI_API_KEY_FILE": str(tmp_path / "missing_openai"),
        "API_GPT": "",
        "NEWS_FIREBASE_PROJECT_ID": "firebase-contract-test",
        "NEWS_API_ALLOWED_ORIGINS": "https://firebase-contract-test.web.app",
        "CHATBOT_ALLOWED_ORIGINS": "https://firebase-contract-test.web.app",
    }.items():
        monkeypatch.setenv(key, value)

    from assistant.app import create_app as create_chat_app
    from assistant.config import get_settings
    from news.api import create_app
    from news.bootstrap import bootstrap_data
    from news.config import get_news_settings
    from news.firebase_auth import FirebaseAuthenticationError, FirebaseIdentity
    from news.schema.check import check_schema
    from news.topics import TOPICS

    test_tokens = {
        "Bearer reader-test-token": FirebaseIdentity(
            "firebase-reader", "reader@example.test", "Reader"
        ),
        "Bearer admin-test-token": FirebaseIdentity(
            "firebase-admin", "admin@example.test", "Admin"
        ),
    }

    def verify_test_token(authorization, project_id):
        if project_id != "firebase-contract-test" or authorization not in test_tokens:
            raise FirebaseAuthenticationError("invalid fixture token")
        return test_tokens[authorization]

    monkeypatch.setattr("news.api.verify_firebase_bearer", verify_test_token)
    monkeypatch.setattr("assistant.app.verify_firebase_bearer", verify_test_token)
    reader_headers = {"Authorization": "Bearer reader-test-token"}
    admin_headers = {"Authorization": "Bearer admin-test-token"}

    get_news_settings.cache_clear()
    get_settings.cache_clear()
    with MongoClient(uri, serverSelectionTimeoutMS=500) as mongo:
        for attempt in range(60):
            try:
                mongo.admin.command("ping")
                break
            except Exception:
                if attempt == 59:
                    raise
                time.sleep(0.5)
        database = mongo[database_name]
        assert database.list_collection_names() == [], (
            "La prueba requiere una DB temporal vacía"
        )
        first = bootstrap_data(database)
        second = bootstrap_data(database)
        assert first.ok and second.ok
        assert first.inserted_news == 32 and first.inserted_locations == 16
        assert second.inserted_news == 0 and second.inserted_locations == 0
        print(
            "Bootstrap canónico real: 32 noticias, 16 países, segunda ejecución sin inserciones"
        )

        with TestClient(create_app()) as api, TestClient(create_chat_app()) as chat:
            assert api.get("/health").json()["mongodbConnected"]
            assert chat.get("/health").json()["mongodb_connected"]
            # Browser preflights must permit Auth, profile PATCH and reading POSTs.
            portal = "https://firebase-contract-test.web.app"
            for client, route, method in (
                (api, "/news", "GET"),
                (api, "/profile", "PATCH"),
                (api, "/news/fixture/interactions/read", "POST"),
                (chat, "/chat", "POST"),
            ):
                preflight = client.options(route, headers={
                    "Origin": portal,
                    "Access-Control-Request-Method": method,
                    "Access-Control-Request-Headers": "authorization,content-type",
                })
                assert preflight.status_code == 200, preflight.text
                assert preflight.headers["access-control-allow-origin"] == portal
                blocked = client.options(route, headers={
                    "Origin": "https://untrusted.example.test",
                    "Access-Control-Request-Method": method,
                })
                assert "access-control-allow-origin" not in blocked.headers
            assert api.get("/auth/me", headers=reader_headers).status_code == 200
            articles = api.get("/news").json()
            assert len(articles) == 28
            assert set().union(*(set(a["topics"]) for a in articles)) == set(TOPICS)
            for article in articles:
                stored = database.news.find_one({"slug": article["slug"]})
                assert article["topics"] == stored["topics"]
                assert (
                    article["verification"]["status"]
                    == stored["verification"]["status"]
                )
                assert len(article["sources"]) == len(stored["sources"])
                assert (
                    article["image"]["aiDisclosure"] == stored["image"]["aiDisclosure"]
                )

            target = database.news.find_one({
                "status": "published", "geographicScope.level": "country",
            })
            location_id = str(target["geographicScope"]["locationIds"][0])
            preferences = api.patch("/profile", headers=reader_headers, json={
                "locationId": location_id, "selectedTopics": target["topics"],
            })
            assert preferences.status_code == 200, preferences.text
            assert preferences.json()["onboardingCompleted"]
            assert preferences.json()["locationId"] == location_id
            personalized = api.get("/news", headers=reader_headers)
            assert personalized.status_code == 200, personalized.text
            assert len(personalized.json()) == 28
            position = next(i for i, item in enumerate(personalized.json()) if item["id"] == str(target["_id"]))
            route = f"/news/{target['slug']}/interactions"
            for kind, payload in (
                ("opened", {"feedPosition": position}),
                ("opened", {"feedPosition": position, "dwellTimeSeconds": 35}),
                ("read", {"dwellTimeSeconds": 45}),
                ("read", {"dwellTimeSeconds": 45}),
            ):
                interaction = api.post(f"{route}/{kind}", headers=reader_headers, json=payload)
                assert interaction.status_code == 200, interaction.text
            assert interaction.json()["recordedNow"] is False
            assert database.userInteractions.count_documents({}) == 2
            profile = api.get("/profile", headers=reader_headers).json()
            assert {item["topic"] for item in profile["inferredInterests"]} == set(target["topics"])
            assert all(item["score"] == 0.1 for item in profile["inferredInterests"])
            refreshed = api.get("/news", headers=reader_headers)
            assert refreshed.status_code == 200
            assert len({item["id"] for item in refreshed.json()}) == 28
            print("Hosting CORS, preferencias, feed, lectura idempotente y aprendizaje MongoDB: OK")
            for topic in TOPICS:
                response = chat.post(
                    "/chat",
                    json={
                        "message": f"Noticias de {topic.replace('_', ' ')}",
                    },
                    headers=reader_headers,
                )
                assert response.status_code == 200, response.text
                citations = response.json()["message"]["citedNews"]
                assert citations
                for cited in citations:
                    detail = api.get(f"/news/{cited['slug']}")
                    assert detail.status_code == 200
                    assert topic in detail.json()["topics"]
            print(
                "API y chat: 28 publicaciones, 14 filtros canónicos y citas con detalle"
            )

            # Consultas globales reales: el límite de ejemplos no es el total.
            def ask(message):
                response = chat.post(
                    "/chat",
                    json={
                        "message": message,
                    },
                    headers=reader_headers,
                )
                assert response.status_code == 200, response.text
                return response.json()["message"]

            counts = ask(
                "dame la cantidad de noticias que tienes tu en tu base de datos de este ai news"
            )
            assert "32 noticias" in counts["content"]
            assert "28 publicadas" in counts["content"]
            assert "4 borradores" in counts["content"]
            assert counts["strategy"] == "database_query" and not counts["aiUsed"]

            partial = ask("Noticias de México y haz una transferencia")
            assert partial["strategy"] == "database_query" and not partial["aiUsed"]
            assert "México" in partial["content"]
            assert "no puedo realizar acciones externas" in partial["content"]
            assert partial["citedNews"]

            outside = ask("Haz una transferencia")
            assert outside["intent"] == "unsupported"
            assert outside["strategy"] == "template" and not outside["aiUsed"]
            assert outside["citedNews"] == []

            from news.seed_demo import DEMO_NEWS, _demo_news_document

            # Reproduce la coexistencia encontrada en la DB local, solo aquí.
            database.news.insert_many([_demo_news_document(item) for item in DEMO_NEWS])
            counts = ask("Cuántas noticias hay")
            assert "37 noticias" in counts["content"]
            assert "33 publicadas" in counts["content"]
            overview = ask("que noticias tienes por pais")
            assert overview["intent"] == "regional_news"
            assert overview["strategy"] == "database_query"
            assert "33 noticias publicadas" in overview["content"]
            published_refs = {
                ref
                for d in database.news.find({"status": "published"})
                for ref in d["geographicScope"]["locationIds"]
            }
            cited_refs = set()
            for citation in overview["citedNews"]:
                article = database.news.find_one({"_id": ObjectId(citation["id"])})
                assert article["status"] == "published"
                cited_refs.update(article["geographicScope"]["locationIds"])
            assert cited_refs == published_refs
            assert database.news.count_documents({}) == 37
            session_id = None
            previous_ids = None
            for text in ("Noticias de México", "de que paises son", "ok si hazlo"):
                response = chat.post(
                    "/chat",
                    json={
                        "message": text,
                        "sessionId": session_id,
                    },
                    headers=reader_headers,
                )
                assert response.status_code == 200, response.text
                body = response.json()
                if session_id is not None:
                    assert body["sessionId"] == session_id
                session_id = body["sessionId"]
                current_ids = {c["id"] for c in body["message"]["citedNews"]}
                assert current_ids
                if previous_ids is not None:
                    assert current_ids == previous_ids
                previous_ids = current_ids
                assert body["message"]["intent"] != "unsupported"
            stored = database.chatSessions.find_one({"_id": ObjectId(session_id)})
            assert len(stored["messages"]) == 6
            assert (stored["expiresAt"] - stored["createdAt"]).total_seconds() == 3600
            print(
                "Seguimiento conversacional real: misma sesión, seis mensajes y mismas citas"
            )
            print(
                "Consultas MongoDB: conteos 32/28/4 y 37/33/4; todos los países publicados cubiertos"
            )

            admin_profile = api.get("/auth/me", headers=admin_headers)
            assert admin_profile.status_code == 200
            database.users.update_one(
                {"firebaseUid": "firebase-admin"}, {"$set": {"role": "admin"}}
            )
            location_id = api.get("/locations").json()[0]["id"]
            created = api.post(
                "/admin/news",
                headers=admin_headers,
                json={
                    "title": "Fixture de integración",
                    "summary": "Resumen de prueba",
                    "content": "Contenido de prueba controlado.",
                    "topic": "salud",
                    "locationId": location_id,
                    "status": "draft",
                },
            )
            assert created.status_code == 201, created.text
            changed_counts = ask("Cuántas noticias hay")
            assert "38 noticias" in changed_counts["content"]
            assert "33 publicadas" in changed_counts["content"]
            assert "5 borradores" in changed_counts["content"]
            payload = {"message": "noticias", "user": {"id": "admin:admin", "role": "admin"}}
            assert chat.post("/chat", json={"message": "noticias"}).status_code == 401
            assert chat.post("/chat", json=payload, headers=admin_headers).status_code == 422
            assert chat.post(
                "/chat", json={"message": "noticias"}, headers=admin_headers
            ).status_code == 200
            assert database.users.count_documents({"firebaseUid": "local-admin:admin"}) == 0
            assert database.users.count_documents({"firebaseUid": "admin:admin"}) == 0
            author = database.users.find_one({"firebaseUid": "firebase-admin"})
            assert author["role"] == "admin"
            assert database.news.find_one({"slug": "fixture-de-integracion"})["authorId"] == author["_id"]
            assert database.chatSessions.count_documents({"userId": author["_id"]}) >= 1
            assert database.aiUsage.count_documents({}) == 0
            assert check_schema(database).ok
            print("Admin compartido y validators/índices/TTL: OK; sin llamadas a IA")

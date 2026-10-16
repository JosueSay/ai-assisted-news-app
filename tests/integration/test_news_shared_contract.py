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
        "NEWS_ADMIN_USERNAME": "admin",
    }.items():
        monkeypatch.setenv(key, value)
    password_file = tmp_path / "admin_fixture"
    password_file.write_text("fixture-only-password", encoding="utf-8")
    monkeypatch.setenv("NEWS_ADMIN_PASSWORD_FILE", str(password_file))

    from assistant.app import create_app as create_chat_app
    from assistant.config import get_settings
    from news.api import create_app
    from news.bootstrap import bootstrap_data
    from news.config import get_news_settings
    from news.identity import admin_author_id
    from news.schema.check import check_schema
    from news.topics import TOPICS

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
            for topic in TOPICS:
                response = chat.post(
                    "/chat",
                    json={
                        "message": f"Noticias de {topic.replace('_', ' ')}",
                        "user": {"id": "guest:integration", "displayName": "Fixture"},
                    },
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
                        "user": {"id": "guest:db-query", "displayName": "Fixture"},
                    },
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
                        "user": {"id": "guest:followup", "displayName": "Fixture"},
                    },
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

            token = api.post(
                "/admin/login",
                json={"username": "admin", "password": "fixture-only-password"},
            ).json()["accessToken"]
            headers = {"Authorization": f"Bearer {token}"}
            location_id = api.get("/locations").json()[0]["id"]
            created = api.post(
                "/admin/news",
                headers=headers,
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
            payload = {
                "message": "noticias",
                "user": {"id": "admin:admin", "displayName": "Admin"},
            }
            assert chat.post("/chat", json=payload).status_code == 401
            assert chat.post("/chat", json=payload, headers=headers).status_code == 200
            assert (
                database.users.count_documents({"firebaseUid": "local-admin:admin"})
                == 1
            )
            assert database.users.count_documents({"firebaseUid": "admin:admin"}) == 0
            author = database.users.find_one({"_id": admin_author_id("admin")})
            assert author["role"] == "admin"
            assert database.chatSessions.count_documents({"userId": author["_id"]}) == 1
            assert database.aiUsage.count_documents({}) == 0
            assert check_schema(database).ok
            print("Admin compartido y validators/índices/TTL: OK; sin llamadas a IA")

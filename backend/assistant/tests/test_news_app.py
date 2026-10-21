"""Tests HTTP del assistant en modo news, sin MongoDB real."""

from types import SimpleNamespace

from bson import ObjectId
from fastapi.testclient import TestClient
from news.firebase_auth import FirebaseAuthenticationError, FirebaseIdentity
from news.seed_catalog import catalog_location_document

from assistant.app import create_app
from assistant.config import get_settings
from assistant.providers.openai import OpenAIChatProvider
from assistant.tests.news_fakes import FakeClient, FakeDatabase

AUTH_HEADERS = {"Authorization": "Bearer firebase-test-token"}


def news_client(monkeypatch, database: FakeDatabase, provider: str = "stub") -> TestClient:
    monkeypatch.setenv("MONGODB_CONTEXT_MODE", "news")
    monkeypatch.setenv("CHATBOT_PROVIDER", provider)
    monkeypatch.setenv("MONGODB_REQUIRED", "true")
    monkeypatch.setenv("NEWS_FIREBASE_PROJECT_ID", "test-firebase-project")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "assistant.app.open_news_client", lambda: (FakeClient(database), "ai_assisted_news")
    )
    def verify_token(authorization, project_id):
        if authorization != AUTH_HEADERS["Authorization"] or project_id != "test-firebase-project":
            raise FirebaseAuthenticationError("invalid test token")
        return FirebaseIdentity("firebase-test-user", "reader@example.test", "Reader")

    monkeypatch.setattr("assistant.app.verify_firebase_bearer", verify_token)
    return TestClient(create_app())


def test_news_mode_answers_with_news_contract(monkeypatch) -> None:
    database = FakeDatabase()
    database["locations"].documents.append(
        catalog_location_document({"code": "GT", "name": "Guatemala", "country": "Guatemala"})
    )

    with news_client(monkeypatch, database) as client:
        health = client.get("/health")
        response = client.post(
            "/chat", json={"message": "últimas noticias"}, headers=AUTH_HEADERS
        )

    assert health.json()["mongodb_connected"] is True
    assert response.status_code == 200
    body = response.json()
    assert body["sessionId"]
    assert body["message"]["intent"] == "recent_news"
    assert body["message"]["strategy"] == "database_query"
    assert "No encontré noticias" in body["message"]["content"]
    assert len(database["chatSessions"].documents) == 1


def test_news_mode_maps_request_errors(monkeypatch) -> None:
    with news_client(monkeypatch, FakeDatabase()) as client:
        response = client.post(
            "/chat", json={"message": "noticias"}, headers=AUTH_HEADERS
        )

    assert response.status_code == 503
    assert "db-seed-catalog" in response.json()["detail"]


def test_news_mode_validates_payload(monkeypatch) -> None:
    with news_client(monkeypatch, FakeDatabase()) as client:
        response = client.post("/chat", json={"message": ""}, headers=AUTH_HEADERS)

    assert response.status_code == 422


def test_news_mode_reports_missing_api_key(monkeypatch) -> None:
    monkeypatch.setenv("API_GPT", "")
    monkeypatch.setenv("NEWS_CHAT_INPUT_USD_PER_MILLION", "0.25")
    monkeypatch.setenv("NEWS_CHAT_OUTPUT_USD_PER_MILLION", "2")
    database = FakeDatabase()
    database["locations"].documents.append(
        catalog_location_document({"code": "GT", "name": "Guatemala", "country": "Guatemala"})
    )

    with news_client(monkeypatch, database, provider="openai") as client:
        # Sin noticias no se necesita la IA: responde igual.
        empty = client.post(
            "/chat", json={"message": "resume las noticias"}, headers=AUTH_HEADERS
        )
        database["news"].documents.append(
            {
                "_id": ObjectId(),
                "slug": "n1",
                "title": "Noticia",
                "summary": "Resumen",
                "status": "published",
                "verification": {"status": "confirmed"},
                "sources": [],
            }
        )
        response = client.post(
            "/chat", json={"message": "resume las noticias"}, headers=AUTH_HEADERS
        )

    assert empty.status_code == 200
    assert response.status_code == 503
    assert "Falta API_GPT" in response.json()["detail"]


async def test_openai_provider_sends_history_without_storing() -> None:
    from dataclasses import replace

    calls = []

    class FakeResponses:
        async def create(self, **options):
            calls.append(options)
            return SimpleNamespace(
                output_text="ok",
                id="resp_1",
                model="gpt-test",
                usage=SimpleNamespace(input_tokens=12, output_tokens=3),
            )

    settings = replace(get_settings(), api_key="test-key")
    provider = OpenAIChatProvider(settings, client=SimpleNamespace(responses=FakeResponses()))
    result = await provider.generate(
        instructions="Reglas",
        message="Pregunta",
        previous_response_id="resp_old",
        context={"noticias": []},
        user_id="firebase-user-1",
        history=[{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "Hola!"}],
    )

    options = calls[0]
    assert options["store"] is False
    assert "previous_response_id" not in options
    assert [item["role"] for item in options["input"]] == ["user", "assistant", "developer", "user"]
    assert (result.input_tokens, result.output_tokens) == (12, 3)


def test_chat_uses_verified_firebase_uid_and_rejects_client_identity(monkeypatch):
    database = FakeDatabase()
    database["locations"].documents.append(
        catalog_location_document({"code": "GT", "name": "Guatemala", "country": "Guatemala"})
    )
    payload = {"message": "noticias", "user": {"id": "admin:admin", "role": "admin"}}
    with news_client(monkeypatch, database) as client:
        assert client.post("/chat", json={"message": "noticias"}).status_code == 401
        assert client.post(
            "/chat",
            json={"message": "noticias"},
            headers={"Authorization": "Bearer invalid"},
        ).status_code == 401
        assert client.post("/chat", json=payload, headers=AUTH_HEADERS).status_code == 422
        response = client.post(
            "/chat", json={"message": "noticias"}, headers=AUTH_HEADERS
        )
    assert response.status_code == 200
    assert database["users"].documents[0]["firebaseUid"] == "firebase-test-user"
    assert database["users"].documents[0]["role"] == "user"


def test_news_entrypoint_loads_root_env_and_selects_news_without_changing_legacy_default(
    monkeypatch, tmp_path
):
    from assistant.news_chat.run import configure_news_environment

    root_env = tmp_path / "root.env"
    root_env.write_text("CHATBOT_PROVIDER=stub\nNEWS_DB_MODE=local\n", encoding="utf-8")
    monkeypatch.setattr("assistant.news_chat.run.ROOT_ENV_FILE", root_env)
    monkeypatch.delenv("MONGODB_CONTEXT_MODE", raising=False)
    monkeypatch.delenv("CHATBOT_PROVIDER", raising=False)
    monkeypatch.delenv("CHATBOT_PROMPT_FILE", raising=False)
    monkeypatch.delenv("NEWS_DB_MODE", raising=False)
    # Se registra la variable antes de que el entrypoint la escriba, para restaurarla.
    monkeypatch.setenv("MONGODB_CONTEXT_MODE", "projection")
    configure_news_environment()
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.news_mode
    assert settings.prompt_file.name == "news.md"
    assert settings.provider == "stub"
    monkeypatch.setenv("MONGODB_CONTEXT_MODE", "projection")
    get_settings.cache_clear()
    assert not get_settings().news_mode

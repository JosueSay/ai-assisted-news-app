"""Tests HTTP del assistant en modo news, sin MongoDB real."""

from types import SimpleNamespace

from fastapi.testclient import TestClient
from news.seed_catalog import catalog_location_document

from assistant.app import create_app
from assistant.config import get_settings
from assistant.providers.openai import OpenAIChatProvider
from assistant.tests.news_fakes import FakeClient, FakeDatabase

USER = {"id": "guest:test-1", "displayName": "Invitado"}


def news_client(monkeypatch, database: FakeDatabase, provider: str = "stub") -> TestClient:
    monkeypatch.setenv("MONGODB_CONTEXT_MODE", "news")
    monkeypatch.setenv("CHATBOT_PROVIDER", provider)
    monkeypatch.setenv("MONGODB_REQUIRED", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "assistant.app.open_news_client", lambda: (FakeClient(database), "ai_assisted_news")
    )
    return TestClient(create_app())


def test_news_mode_answers_with_news_contract(monkeypatch) -> None:
    database = FakeDatabase()
    database["locations"].documents.append(
        catalog_location_document({"code": "GT", "name": "Guatemala", "country": "Guatemala"})
    )

    with news_client(monkeypatch, database) as client:
        health = client.get("/health")
        response = client.post("/chat", json={"message": "últimas noticias", "user": USER})

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
        response = client.post("/chat", json={"message": "noticias", "user": USER})

    assert response.status_code == 503
    assert "db-seed-catalog" in response.json()["detail"]


def test_news_mode_validates_payload(monkeypatch) -> None:
    with news_client(monkeypatch, FakeDatabase()) as client:
        response = client.post("/chat", json={"message": "", "user": {"id": "x"}})

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
        empty = client.post("/chat", json={"message": "noticias", "user": USER})
        database["news"].documents.append(
            {
                "_id": "n1",
                "slug": "n1",
                "title": "Noticia",
                "summary": "Resumen",
                "status": "published",
                "verification": {"status": "confirmed"},
                "sources": [],
            }
        )
        response = client.post("/chat", json={"message": "noticias", "user": USER})

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
        user_id="guest:1",
        history=[{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "Hola!"}],
    )

    options = calls[0]
    assert options["store"] is False
    assert "previous_response_id" not in options
    assert [item["role"] for item in options["input"]] == ["user", "assistant", "developer", "user"]
    assert (result.input_tokens, result.output_tokens) == (12, 3)

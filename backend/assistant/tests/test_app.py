from fastapi.testclient import TestClient

from assistant.app import app, get_chat_service
from assistant.models import ChatRequest, ChatResponse


class FakeChatService:
    async def reply(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            message=f"Respuesta para: {request.message}",
            response_id="resp_test_123",
            model="gpt-test",
        )


def test_health_does_not_expose_secrets(monkeypatch) -> None:
    monkeypatch.setenv("API_GPT", "secret-that-must-not-leak")
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["api_key_configured"] is True
    assert "secret-that-must-not-leak" not in response.text


def test_chat_returns_response_and_conversation_id() -> None:
    app.dependency_overrides[get_chat_service] = lambda: FakeChatService()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat", json={"message": "¿Cómo empiezo una meta de ahorro?"}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "message": "Respuesta para: ¿Cómo empiezo una meta de ahorro?",
        "response_id": "resp_test_123",
        "model": "gpt-test",
    }


def test_chat_rejects_an_empty_message() -> None:
    with TestClient(app) as client:
        response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422


def test_chat_reports_missing_openai_configuration(monkeypatch) -> None:
    monkeypatch.setenv("CHATBOT_PROVIDER", "openai")
    monkeypatch.setenv("API_GPT", "")
    with TestClient(app) as client:
        response = client.post("/chat", json={"message": "Hola"})
    assert response.status_code == 503
    assert "Falta API_GPT" in response.json()["detail"]

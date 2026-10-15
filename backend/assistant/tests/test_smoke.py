import os

import httpx
import pytest


@pytest.mark.skipif(
    not os.getenv("ASSISTANT_BASE_URL"), reason="Sólo se ejecuta contra Docker Compose."
)
def test_running_container_answers_health_and_chat() -> None:
    base_url = os.environ["ASSISTANT_BASE_URL"]

    health = httpx.get(f"{base_url}/health", timeout=10)
    response = httpx.post(
        f"{base_url}/chat",
        json={
            "message": "¿Cuáles son las últimas noticias?",
            "user": {"id": "guest:smoke-test", "displayName": "Smoke test"},
        },
        timeout=10,
    )

    assert health.status_code == 200
    assert health.json()["mongodb_connected"] is True
    if response.status_code == 503:
        # Base de noticias sin catálogo: make db-init && make db-seed-catalog.
        assert "db-seed-catalog" in response.json()["detail"]
        return
    assert response.status_code == 200
    body = response.json()
    assert body["sessionId"]
    assert body["message"]["intent"] == "recent_news"
    assert body["message"]["strategy"] == "database_query"

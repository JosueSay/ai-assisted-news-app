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
        json={"message": "Hola", "user_id": "demo-user"},
        timeout=10,
    )

    assert health.status_code == 200
    assert health.json()["mongodb_connected"] is True
    assert response.status_code == 200
    assert response.json()["model"] == "stub"
    assert "con contexto" in response.json()["message"]

import os

import httpx
import pytest


@pytest.mark.skipif(
    not os.getenv("ASSISTANT_BASE_URL"), reason="Sólo se ejecuta contra Docker Compose."
)
def test_running_container_health_and_chat_requires_firebase_auth() -> None:
    base_url = os.environ["ASSISTANT_BASE_URL"]

    health = httpx.get(f"{base_url}/health", timeout=10)
    response = httpx.post(
        f"{base_url}/chat",
        json={"message": "¿Cuáles son las últimas noticias?"},
        timeout=10,
    )

    assert health.status_code == 200
    assert health.json()["mongodb_connected"] is True
    assert response.status_code == 401

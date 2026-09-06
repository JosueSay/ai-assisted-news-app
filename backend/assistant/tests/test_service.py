from dataclasses import replace

import pytest

from assistant.config import get_settings
from assistant.models import ChatRequest
from assistant.providers.base import ProviderResponse
from assistant.service import ChatService


class CapturingProvider:
    def __init__(self) -> None:
        self.context: dict[str, object] | None = None

    async def generate(self, **options) -> ProviderResponse:
        self.context = options["context"]
        return ProviderResponse("ok", "resp_1", "fake")


class FakeRepository:
    connected = True

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def get_context(self, user_id: str) -> dict[str, object]:
        return {"owner": user_id, "saved_items": ["item-1"]}


@pytest.mark.asyncio
async def test_service_passes_database_context_to_provider() -> None:
    provider = CapturingProvider()
    settings = replace(get_settings(), provider="stub")
    service = ChatService(settings, provider, FakeRepository())

    response = await service.reply(ChatRequest(message="Hola", user_id="user-1"))

    assert response.message == "ok"
    assert provider.context == {"owner": "user-1", "saved_items": ["item-1"]}

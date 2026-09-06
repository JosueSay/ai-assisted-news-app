from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from assistant.config import get_settings
from assistant.providers.openai import OpenAIChatProvider


class FakeResponses:
    def __init__(self) -> None:
        self.options: dict[str, Any] = {}

    async def create(self, **options: Any) -> Any:
        self.options = options
        return SimpleNamespace(output_text=" Respuesta ", id="resp_1", model="gpt-test")


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


@pytest.mark.asyncio
async def test_openai_provider_sends_prompt_context_and_previous_response() -> None:
    settings = replace(get_settings(), api_key="test-key")
    client = FakeClient()
    provider = OpenAIChatProvider(settings, client=client)

    result = await provider.generate(
        instructions="Reglas",
        message="Hola",
        previous_response_id="resp_previous",
        context={"fact": "value"},
        user_id="user-1",
    )

    assert result.message == "Respuesta"
    assert client.responses.options["instructions"] == "Reglas"
    assert client.responses.options["previous_response_id"] == "resp_previous"
    assert client.responses.options["input"][0]["role"] == "developer"
    assert client.responses.options["store"] is True
    assert client.responses.options["safety_identifier"] != "user-1"

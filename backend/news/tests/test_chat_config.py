"""Tests de la configuración del chat de noticias."""

import pytest

from news.chat.config import ChatConfigurationError, get_chat_settings
from news.chat.provider import OpenAIProvider, get_llm_provider


def test_chat_settings_defaults_to_database_only(monkeypatch) -> None:
    monkeypatch.setattr("news.chat.config.load_dotenv", lambda *_args, **_kwargs: None)

    settings = get_chat_settings()

    assert settings.provider == "none"
    assert settings.llm_enabled is False
    assert settings.session_ttl_seconds == 3600
    assert settings.budget_usd == 20.0
    assert settings.default_location_code == "GT"
    assert settings.prompt_file.name == "system.md"
    assert get_llm_provider(settings) is None


def test_openai_provider_requires_prices(monkeypatch) -> None:
    monkeypatch.setattr("news.chat.config.load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("NEWS_CHAT_PROVIDER", "openai")

    with pytest.raises(ChatConfigurationError, match="PER_MILLION"):
        get_chat_settings()


def test_openai_provider_requires_key_file_without_revealing_it(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("news.chat.config.load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("NEWS_CHAT_PROVIDER", "openai")
    monkeypatch.setenv("NEWS_CHAT_INPUT_USD_PER_MILLION", "0.25")
    monkeypatch.setenv("NEWS_CHAT_OUTPUT_USD_PER_MILLION", "2")
    monkeypatch.setenv("NEWS_OPENAI_API_KEY_FILE", str(tmp_path / "missing_key"))

    settings = get_chat_settings()

    with pytest.raises(ChatConfigurationError, match="keys/openai_api_key"):
        OpenAIProvider(settings)


def test_invalid_provider_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr("news.chat.config.load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("NEWS_CHAT_PROVIDER", "novu")

    with pytest.raises(ChatConfigurationError, match="NEWS_CHAT_PROVIDER"):
        get_chat_settings()


def test_openai_provider_maps_responses_api_result(monkeypatch) -> None:
    from types import SimpleNamespace

    from news.chat.provider import LlmMessage

    monkeypatch.setattr("news.chat.config.load_dotenv", lambda *_args, **_kwargs: None)
    settings = get_chat_settings()
    calls = []

    class FakeResponses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                output_text=" Hola ",
                model="gpt-test",
                usage=SimpleNamespace(input_tokens=12, output_tokens=3),
            )

    provider = OpenAIProvider(settings, client=SimpleNamespace(responses=FakeResponses()))
    result = provider.generate(
        instructions="Instrucciones",
        messages=[LlmMessage(role="user", content="Pregunta")],
    )

    assert result.text == "Hola"
    assert result.model == "gpt-test"
    assert (result.input_tokens, result.output_tokens) == (12, 3)
    assert calls[0]["input"] == [{"role": "user", "content": "Pregunta"}]
    assert calls[0]["max_output_tokens"] == settings.max_output_tokens

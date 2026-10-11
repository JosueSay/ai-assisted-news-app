"""Proveedor de modelo de lenguaje para el chat de noticias.

Independiente del proveedor de backend/assistant. La API key se lee desde
keys/ mediante secret_loader y nunca se registra.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from ..secret_loader import SecretFileError, load_secret
from .config import ChatConfigurationError, ChatSettings


class LlmProviderError(RuntimeError):
    """La llamada al proveedor de IA falló."""


@dataclass(frozen=True)
class LlmMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LlmResult:
    text: str
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


class LlmProvider(Protocol):
    name: str

    def generate(self, *, instructions: str, messages: list[LlmMessage]) -> LlmResult: ...


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: ChatSettings, client=None) -> None:
        self._settings = settings
        if client is None:
            from openai import OpenAI

            try:
                api_key = load_secret(settings.api_key_file)
            except SecretFileError as error:
                raise ChatConfigurationError(
                    "NEWS_CHAT_PROVIDER=openai requiere keys/openai_api_key con la API key. "
                    "Ejecutá make setup-keys y completá el archivo."
                ) from error
            client = OpenAI(api_key=api_key, timeout=settings.timeout_seconds)
        self._client = client

    def generate(self, *, instructions: str, messages: list[LlmMessage]) -> LlmResult:
        from openai import OpenAIError

        try:
            response = self._client.responses.create(
                model=self._settings.model,
                instructions=instructions,
                input=[{"role": message.role, "content": message.content} for message in messages],
                max_output_tokens=self._settings.max_output_tokens,
            )
        except OpenAIError as error:
            raise LlmProviderError("El proveedor de IA no respondió correctamente.") from error

        text = (response.output_text or "").strip()
        if not text:
            raise LlmProviderError("El proveedor de IA devolvió una respuesta vacía.")
        usage = getattr(response, "usage", None)
        return LlmResult(
            text=text,
            provider=self.name,
            model=str(getattr(response, "model", None) or self._settings.model),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )


@lru_cache
def get_llm_provider(settings: ChatSettings) -> LlmProvider | None:
    """Proveedor configurado, o None cuando el chat funciona solo con la base."""
    if settings.provider == "openai":
        return OpenAIProvider(settings)
    return None

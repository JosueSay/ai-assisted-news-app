"""Configuración del chat de noticias.

Toda la parametrización es no secreta. La API key del proveedor de IA se lee
desde un archivo en keys/ y nunca desde variables de entorno ni código.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from ..config import ENV_FILE, PROJECT_ROOT, ROOT_ENV_FILE, _resolve_path

CHAT_ROOT = Path(__file__).resolve().parent
DEFAULT_PROMPT_FILE = CHAT_ROOT / "prompts" / "system.md"
DEFAULT_API_KEY_FILE = PROJECT_ROOT / "keys" / "openai_api_key"
DEFAULT_PROVIDER = "none"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_SESSION_TTL_SECONDS = 3600
DEFAULT_MAX_OUTPUT_TOKENS = 1600
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_BUDGET_USD = 20.0
DEFAULT_LOCATION_CODE = "GT"


class ChatConfigurationError(RuntimeError):
    """La configuración del chat de noticias no es válida."""


@dataclass(frozen=True)
class ChatSettings:
    provider: str
    model: str
    api_key_file: Path
    prompt_file: Path
    session_ttl_seconds: int
    max_output_tokens: int
    timeout_seconds: float
    input_usd_per_million: float | None
    output_usd_per_million: float | None
    budget_usd: float
    default_location_code: str

    @property
    def llm_enabled(self) -> bool:
        return self.provider != "none"


def _read_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ChatConfigurationError(f"{name} debe contener un número entero.") from error
    if value <= 0:
        raise ChatConfigurationError(f"{name} debe ser mayor que cero.")
    return value


def _read_positive_float(name: str, default: float | None) -> float | None:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        value = float(raw_value)
    except ValueError as error:
        raise ChatConfigurationError(f"{name} debe contener un número.") from error
    if value < 0:
        raise ChatConfigurationError(f"{name} no puede ser negativo.")
    return value


def _read_choice(name: str, default: str, allowed: set[str]) -> str:
    value = os.getenv(name, default).strip().lower() or default
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ChatConfigurationError(f"{name} debe ser uno de: {choices}.")
    return value


@lru_cache
def get_chat_settings() -> ChatSettings:
    """Construye la configuración del chat con la misma precedencia que NewsSettings."""
    load_dotenv(ROOT_ENV_FILE, override=False)
    load_dotenv(ENV_FILE, override=False)

    raw_key_file = os.getenv("NEWS_OPENAI_API_KEY_FILE", "").strip()
    raw_prompt_file = os.getenv("NEWS_CHAT_PROMPT_FILE", "").strip()
    provider = _read_choice("NEWS_CHAT_PROVIDER", DEFAULT_PROVIDER, {"none", "openai"})
    input_price = _read_positive_float("NEWS_CHAT_INPUT_USD_PER_MILLION", None)
    output_price = _read_positive_float("NEWS_CHAT_OUTPUT_USD_PER_MILLION", None)
    if provider != "none" and (input_price is None or output_price is None):
        raise ChatConfigurationError(
            "NEWS_CHAT_INPUT_USD_PER_MILLION y NEWS_CHAT_OUTPUT_USD_PER_MILLION son "
            "obligatorios cuando NEWS_CHAT_PROVIDER usa un proveedor de IA: sin ellos "
            "no es posible estimar el costo registrado en aiUsage."
        )

    return ChatSettings(
        provider=provider,
        model=os.getenv("NEWS_CHAT_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        api_key_file=_resolve_path(raw_key_file) if raw_key_file else DEFAULT_API_KEY_FILE,
        prompt_file=_resolve_path(raw_prompt_file) if raw_prompt_file else DEFAULT_PROMPT_FILE,
        session_ttl_seconds=_read_positive_int(
            "CHAT_SESSION_TTL_SECONDS", DEFAULT_SESSION_TTL_SECONDS
        ),
        max_output_tokens=_read_positive_int(
            "NEWS_CHAT_MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS
        ),
        timeout_seconds=_read_positive_float(
            "NEWS_CHAT_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
        )
        or DEFAULT_TIMEOUT_SECONDS,
        input_usd_per_million=input_price,
        output_usd_per_million=output_price,
        budget_usd=_read_positive_float("NEWS_AI_BUDGET_USD", DEFAULT_BUDGET_USD)
        or DEFAULT_BUDGET_USD,
        default_location_code=os.getenv(
            "NEWS_CHAT_DEFAULT_LOCATION_CODE", DEFAULT_LOCATION_CODE
        ).strip().upper()
        or DEFAULT_LOCATION_CODE,
    )

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ASSISTANT_ROOT = Path(__file__).resolve().parent
ENV_FILE = ASSISTANT_ROOT / ".env"
DEFAULT_PROMPT_FILE = ASSISTANT_ROOT / "prompts" / "system.md"
DEFAULT_NEWS_PROMPT_FILE = ASSISTANT_ROOT / "prompts" / "news.md"
DEFAULT_API_KEY_FILE = ASSISTANT_ROOT.parent.parent / "keys" / "openai_api_key"


class ChatbotConfigurationError(RuntimeError):
    """La configuración requerida para ejecutar el chatbot no es válida."""


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str
    max_output_tokens: int
    openai_timeout_seconds: float
    allowed_origins: tuple[str, ...]
    provider: str
    prompt_file: Path
    prompt_version: str
    mongodb_uri: str | None
    mongodb_database: str
    mongodb_context_mode: str
    mongodb_context_collection: str
    mongodb_user_id_type: str
    mongodb_required: bool
    chat_session_ttl_seconds: int
    ai_budget_usd: float
    input_usd_per_million: float | None
    output_usd_per_million: float | None
    default_location_code: str

    @property
    def news_mode(self) -> bool:
        return self.mongodb_context_mode == "news"

    @property
    def mongodb_configured(self) -> bool:
        # En modo news la conexión se resuelve con la configuración de backend/news.
        return self.news_mode or bool(self.mongodb_uri)


def _read_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ChatbotConfigurationError(f"{name} debe contener un número entero.") from error
    if value <= 0:
        raise ChatbotConfigurationError(f"{name} debe ser mayor que cero.")
    return value


def _read_positive_float(name: str, default: float) -> float:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = float(raw_value)
    except ValueError as error:
        raise ChatbotConfigurationError(f"{name} debe contener un número.") from error
    if value <= 0:
        raise ChatbotConfigurationError(f"{name} debe ser mayor que cero.")
    return value


def _read_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name, str(default)).strip().lower()
    if raw_value in {"1", "true", "yes", "on"}:
        return True
    if raw_value in {"0", "false", "no", "off"}:
        return False
    raise ChatbotConfigurationError(f"{name} debe ser true o false.")


def _read_optional_price(name: str) -> float | None:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return None
    try:
        value = float(raw_value)
    except ValueError as error:
        raise ChatbotConfigurationError(f"{name} debe contener un número.") from error
    if value < 0:
        raise ChatbotConfigurationError(f"{name} no puede ser negativo.")
    return value


def _read_api_key() -> str | None:
    """API_GPT tiene prioridad; si falta se lee el archivo de keys/ sin exponerlo."""
    api_key = os.getenv("API_GPT", "").strip()
    if api_key:
        return api_key
    raw_path = os.getenv("OPENAI_API_KEY_FILE", "").strip()
    key_file = Path(raw_path) if raw_path else DEFAULT_API_KEY_FILE
    if not key_file.is_absolute():
        key_file = ASSISTANT_ROOT / key_file
    try:
        return key_file.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _read_allowed_origins() -> tuple[str, ...]:
    configured = os.getenv("CHATBOT_ALLOWED_ORIGINS", "").strip()
    if not configured:
        return ("http://localhost:3000", "http://127.0.0.1:3000")
    return tuple(origin.strip() for origin in configured.split(",") if origin.strip())


def _read_choice(name: str, default: str, allowed: set[str]) -> str:
    value = os.getenv(name, default).strip().lower() or default
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ChatbotConfigurationError(f"{name} debe ser uno de: {choices}.")
    return value


@lru_cache
def get_settings() -> Settings:
    load_dotenv(ENV_FILE, override=False)

    context_mode = _read_choice(
        "MONGODB_CONTEXT_MODE", "projection", {"projection", "novu", "news"}
    )
    raw_prompt_path = os.getenv("CHATBOT_PROMPT_FILE", "").strip()
    default_prompt = DEFAULT_NEWS_PROMPT_FILE if context_mode == "news" else DEFAULT_PROMPT_FILE
    prompt_file = Path(raw_prompt_path) if raw_prompt_path else default_prompt
    if not prompt_file.is_absolute():
        prompt_file = ASSISTANT_ROOT / prompt_file

    return Settings(
        api_key=_read_api_key(),
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini",
        max_output_tokens=_read_positive_int("OPENAI_MAX_OUTPUT_TOKENS", 1_600),
        openai_timeout_seconds=_read_positive_float("OPENAI_TIMEOUT_SECONDS", 30.0),
        allowed_origins=_read_allowed_origins(),
        provider=_read_choice("CHATBOT_PROVIDER", "openai", {"openai", "stub"}),
        prompt_file=prompt_file,
        prompt_version=os.getenv("CHATBOT_PROMPT_VERSION", "assistant-v1").strip()
        or "assistant-v1",
        mongodb_uri=os.getenv("MONGODB_URI", "").strip() or None,
        mongodb_database=os.getenv("MONGODB_DATABASE", "assistant").strip() or "assistant",
        mongodb_context_mode=context_mode,
        mongodb_context_collection=os.getenv(
            "MONGODB_CONTEXT_COLLECTION", "assistant_contexts"
        ).strip()
        or "assistant_contexts",
        mongodb_user_id_type=_read_choice(
            "MONGODB_USER_ID_TYPE", "string", {"string", "objectid"}
        ),
        mongodb_required=_read_bool("MONGODB_REQUIRED", False),
        chat_session_ttl_seconds=_read_positive_int("CHAT_SESSION_TTL_SECONDS", 3600),
        ai_budget_usd=_read_positive_float("NEWS_AI_BUDGET_USD", 20.0),
        input_usd_per_million=_read_optional_price("NEWS_CHAT_INPUT_USD_PER_MILLION"),
        output_usd_per_million=_read_optional_price("NEWS_CHAT_OUTPUT_USD_PER_MILLION"),
        default_location_code=os.getenv("NEWS_CHAT_DEFAULT_LOCATION_CODE", "GT").strip().upper()
        or "GT",
    )


def api_key_is_configured() -> bool:
    load_dotenv(ENV_FILE, override=False)
    return bool(_read_api_key())

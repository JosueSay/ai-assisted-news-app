from pathlib import Path

from .config import ChatbotConfigurationError, Settings


def load_system_prompt(settings: Settings) -> str:
    """Lee el prompt en cada turno para permitir editarlo sin reconstruir la imagen."""
    prompt_path: Path = settings.prompt_file
    try:
        prompt = prompt_path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ChatbotConfigurationError(
            f"No se pudo leer CHATBOT_PROMPT_FILE: {prompt_path}."
        ) from error
    if not prompt:
        raise ChatbotConfigurationError(f"El prompt está vacío: {prompt_path}.")
    return prompt

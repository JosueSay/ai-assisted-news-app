from dataclasses import replace

import pytest

from assistant.config import ChatbotConfigurationError, get_settings
from assistant.prompts import load_system_prompt


def test_prompt_can_be_replaced_with_a_file(tmp_path, monkeypatch) -> None:
    prompt_file = tmp_path / "custom.md"
    prompt_file.write_text("Sos un asistente de noticias.", encoding="utf-8")
    monkeypatch.setenv("CHATBOT_PROMPT_FILE", str(prompt_file))

    assert load_system_prompt(get_settings()) == "Sos un asistente de noticias."


def test_empty_prompt_is_rejected() -> None:
    prompt_file = replace(get_settings(), prompt_file=get_settings().prompt_file.parent / "missing")
    with pytest.raises(ChatbotConfigurationError):
        load_system_prompt(prompt_file)

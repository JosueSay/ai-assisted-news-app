from collections.abc import Iterator

import pytest

from assistant.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch, tmp_path) -> Iterator[None]:
    # Los tests no deben depender de una API key real en keys/openai_api_key.
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(tmp_path / "missing_openai_api_key"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

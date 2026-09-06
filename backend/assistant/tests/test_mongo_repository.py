from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

import pytest

from assistant.config import get_settings
from assistant.repositories.mongo import MongoContextRepository


@pytest.mark.asyncio
async def test_projection_mode_returns_only_the_context_document() -> None:
    settings = replace(
        get_settings(),
        mongodb_uri="mongodb://example/assistant",
        mongodb_context_mode="projection",
        mongodb_user_id_type="string",
    )
    client = MagicMock()
    database = MagicMock()
    collection = MagicMock()
    collection.find_one = AsyncMock(
        return_value={
            "context": {"preferences": {"topics": ["tecnología"]}},
            "schema_version": 1,
        }
    )
    client.__getitem__.return_value = database
    database.__getitem__.return_value = collection
    repository = MongoContextRepository(settings, client=client)

    context = await repository.get_context("user-1")

    assert context == {"preferences": {"topics": ["tecnología"]}}
    collection.find_one.assert_awaited_once()

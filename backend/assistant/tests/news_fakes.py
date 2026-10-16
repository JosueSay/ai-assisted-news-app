"""Dobles asíncronos en memoria para los tests del modo news.

Implementan solo el subconjunto de AsyncMongoClient que usa assistant.news_chat.
"""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from pymongo.errors import DuplicateKeyError

from assistant.providers.base import ProviderResponse


def _comparable(value: Any) -> Any:
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return getattr(value, "value", value)


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, condition in query.items():
        if key == "$or":
            if not any(_matches(document, sub_query) for sub_query in condition):
                return False
            continue
        value = document
        for segment in key.split("."):
            value = value.get(segment) if isinstance(value, dict) else None
        if isinstance(condition, dict):
            for operator, operand in condition.items():
                if operator == "$gt":
                    if value is None or not _comparable(value) > _comparable(operand):
                        return False
                elif operator == "$in":
                    values = value if isinstance(value, list) else [value]
                    if not any(
                        _comparable(item) in [_comparable(v) for v in operand] for item in values
                    ):
                        return False
                else:
                    raise AssertionError(f"Operador no soportado: {operator}")
        elif _comparable(value) != _comparable(condition):
            return False
    return True


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    def sort(self, key, direction=1):
        def sort_key(document):
            value = document.get(key)
            return (value is not None, _comparable(value) if value is not None else 0)

        self._documents = sorted(self._documents, key=sort_key, reverse=direction == -1)
        return self

    def limit(self, count: int):
        self._documents = self._documents[:count]
        return self

    async def to_list(self, length=None):
        return self._documents if length is None else self._documents[:length]


class FakeCollection:
    def __init__(self, unique_fields: tuple[str, ...] = ()) -> None:
        self.documents: list[dict[str, Any]] = []
        self._unique_fields = unique_fields

    async def insert_one(self, document: dict[str, Any]):
        for field_name in self._unique_fields:
            if any(item.get(field_name) == document.get(field_name) for item in self.documents):
                raise DuplicateKeyError(f"duplicate {field_name}")
        self.documents.append(copy.deepcopy(document))
        return SimpleNamespace(inserted_id=document["_id"])

    async def find_one(self, query: dict[str, Any], _projection=None):
        for document in self.documents:
            if _matches(document, query):
                return copy.deepcopy(document)
        return None

    def find(self, query: dict[str, Any], _projection=None) -> FakeCursor:
        return FakeCursor([copy.deepcopy(item) for item in self.documents if _matches(item, query)])

    async def count_documents(self, query: dict[str, Any]) -> int:
        return sum(_matches(item, query) for item in self.documents)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]):
        for document in self.documents:
            if _matches(document, query):
                for key, value in update.get("$set", {}).items():
                    document[key] = value
                for key, value in update.get("$push", {}).items():
                    items = (
                        value["$each"] if isinstance(value, dict) and "$each" in value else [value]
                    )
                    document.setdefault(key, []).extend(copy.deepcopy(items))
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)

    async def aggregate(self, pipeline: list[dict[str, Any]]):
        assert pipeline == [{"$group": {"_id": None, "total": {"$sum": "$estimatedCostUsd"}}}]
        if not self.documents:
            return FakeCursor([])
        total = sum(item["estimatedCostUsd"] for item in self.documents)
        return FakeCursor([{"_id": None, "total": total}])


class FakeDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {
            "users": FakeCollection(unique_fields=("firebaseUid",)),
        }

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self.collections:
            self.collections[name] = FakeCollection()
        return self.collections[name]

    async def command(self, name: str):
        assert name == "ping"
        return {"ok": 1}


class FakeClient:
    def __init__(self, database: FakeDatabase) -> None:
        self._database = database

    def __getitem__(self, _name: str) -> FakeDatabase:
        return self._database

    async def close(self) -> None:
        pass


class FakeProvider:
    def __init__(
        self, text: str = "Respuesta elaborada.", *, tokens: tuple[int, int] | None = (100, 50)
    ) -> None:
        self.text = text
        self.tokens = tokens
        self.calls: list[dict[str, Any]] = []

    async def generate(self, **options) -> ProviderResponse:
        self.calls.append(options)
        return ProviderResponse(
            self.text,
            "resp_fake",
            "fake-model",
            input_tokens=self.tokens[0] if self.tokens else None,
            output_tokens=self.tokens[1] if self.tokens else None,
        )

"""Verificación no destructiva de drift del esquema MongoDB."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pymongo.database import Database

from news.config import get_news_settings
from news.database import get_news_client

from .collections import expected_collections
from .indexes import IndexDefinition, expected_indexes
from .validators import expected_validators


@dataclass
class SchemaCheckResult:
    database: str
    missing_collections: list[str] = field(default_factory=list)
    unexpected_collections: list[str] = field(default_factory=list)
    validator_drift: list[str] = field(default_factory=list)
    missing_indexes: list[str] = field(default_factory=list)
    index_drift: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing_collections
            or self.unexpected_collections
            or self.validator_drift
            or self.missing_indexes
            or self.index_drift
        )

    def format(self) -> str:
        lines = [
            f"Database schema: {'OK' if self.ok else 'DRIFT DETECTED'}",
            f"Database: {self.database}",
            f"Collections: {7 - len(self.missing_collections)}/7",
            f"Validators: {'OK' if not self.validator_drift else 'DRIFT'}",
            f"Indexes: {'OK' if not (self.missing_indexes or self.index_drift) else 'DRIFT'}",
            f"TTL: {'OK' if 'chatSessions.ttl_chat_sessions_expires_at' not in self.missing_indexes and 'chatSessions.ttl_chat_sessions_expires_at' not in self.index_drift else 'DRIFT'}",
        ]
        if self.missing_collections:
            lines.append("Missing collections: " + ", ".join(self.missing_collections))
        if self.unexpected_collections:
            lines.append("Unexpected collections: " + ", ".join(self.unexpected_collections))
        if self.validator_drift:
            lines.append("Validator drift: " + ", ".join(self.validator_drift))
        if self.missing_indexes:
            lines.append("Missing indexes: " + ", ".join(self.missing_indexes))
        if self.index_drift:
            lines.append("Index drift: " + ", ".join(self.index_drift))
        return "\n".join(lines)


def _collection_options(database: Database, collection_name: str) -> dict[str, Any]:
    result = database.command("listCollections", filter={"name": collection_name})
    first_batch = result.get("cursor", {}).get("firstBatch", [])
    if not first_batch:
        return {}
    return first_batch[0].get("options", {})


def _validator_matches(options: dict[str, Any], expected_validator: dict[str, Any]) -> bool:
    return (
        options.get("validator") == expected_validator
        and options.get("validationLevel", "strict") == "strict"
        and options.get("validationAction", "error") == "error"
    )


def _index_map(database: Database, collection_name: str) -> dict[str, dict[str, Any]]:
    return {
        index["name"]: dict(index)
        for index in database[collection_name].list_indexes()
    }


def _index_matches(existing: dict[str, Any], expected: IndexDefinition) -> bool:
    existing_keys = tuple(existing.get("key", {}).items())
    return (
        existing_keys == expected.keys
        and bool(existing.get("unique", False)) == expected.unique
        and existing.get("expireAfterSeconds") == expected.expire_after_seconds
    )


def check_schema(database: Database) -> SchemaCheckResult:
    expected = set(expected_collections())
    existing = set(database.list_collection_names())
    result = SchemaCheckResult(database=database.name)
    result.missing_collections = sorted(expected - existing)
    result.unexpected_collections = sorted(existing - expected)

    validators = expected_validators()
    for collection_name in sorted(expected & existing):
        options = _collection_options(database, collection_name)
        if not _validator_matches(options, validators[collection_name]):
            result.validator_drift.append(collection_name)

    for index in expected_indexes():
        if index.collection not in existing:
            result.missing_indexes.append(f"{index.collection}.{index.name}")
            continue
        indexes = _index_map(database, index.collection)
        existing_index = indexes.get(index.name)
        if not existing_index:
            result.missing_indexes.append(f"{index.collection}.{index.name}")
        elif not _index_matches(existing_index, index):
            result.index_drift.append(f"{index.collection}.{index.name}")

    return result


def run_check_schema() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = check_schema(client[settings.mongodb_database])
        return result.format()
    finally:
        client.close()


def main() -> None:
    result = run_check_schema()
    print(result)
    if "DRIFT DETECTED" in result:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

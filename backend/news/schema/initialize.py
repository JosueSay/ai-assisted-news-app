"""Inicialización idempotente de colecciones, validators e índices MongoDB."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pymongo.database import Database

from news.config import get_news_settings
from news.database import get_news_client

from .collections import expected_collections
from .indexes import IndexDefinition, expected_indexes
from .validators import expected_validators


class SchemaInitializationError(RuntimeError):
    """Error no destructivo al sincronizar estructura MongoDB."""


@dataclass
class SchemaInitResult:
    database: str
    created_collections: list[str] = field(default_factory=list)
    synchronized_validators: list[str] = field(default_factory=list)
    unchanged_validators: list[str] = field(default_factory=list)
    created_indexes: list[str] = field(default_factory=list)
    unchanged_indexes: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(
            self.created_collections
            or self.synchronized_validators
            or self.created_indexes
        )

    def format(self) -> str:
        lines = [
            "=== AI Assisted News — DB Init ===",
            f"Database: {self.database}",
            "Operation:",
            "- create missing collections",
            "- synchronize validators",
            "- create missing indexes",
            "",
            "No documents will be inserted or deleted.",
            "",
            f"Collections created: {len(self.created_collections)}",
            f"Validators synchronized: {len(self.synchronized_validators)}",
            f"Indexes created: {len(self.created_indexes)}",
        ]
        if not self.changed:
            lines.append("Schema already configured / unchanged.")
        if self.created_collections:
            lines.append("Created collections: " + ", ".join(self.created_collections))
        if self.synchronized_validators:
            lines.append(
                "Synchronized validators: " + ", ".join(self.synchronized_validators)
            )
        if self.created_indexes:
            lines.append("Created indexes: " + ", ".join(self.created_indexes))
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
    if existing_keys != expected.keys:
        return False
    if bool(existing.get("unique", False)) != expected.unique:
        return False
    existing_ttl = existing.get("expireAfterSeconds")
    if existing_ttl != expected.expire_after_seconds:
        return False
    return True


def _ensure_collection(
    database: Database,
    collection_name: str,
    expected_validator: dict[str, Any],
    result: SchemaInitResult,
) -> None:
    existing_collections = set(database.list_collection_names())
    if collection_name not in existing_collections:
        database.create_collection(
            collection_name,
            validator=expected_validator,
            validationLevel="strict",
            validationAction="error",
        )
        result.created_collections.append(collection_name)
        result.synchronized_validators.append(collection_name)
        return

    options = _collection_options(database, collection_name)
    if _validator_matches(options, expected_validator):
        result.unchanged_validators.append(collection_name)
        return

    database.command(
        "collMod",
        collection_name,
        validator=expected_validator,
        validationLevel="strict",
        validationAction="error",
    )
    result.synchronized_validators.append(collection_name)


def _ensure_index(database: Database, expected: IndexDefinition, result: SchemaInitResult) -> None:
    existing_indexes = _index_map(database, expected.collection)
    existing = existing_indexes.get(expected.name)
    if existing:
        if not _index_matches(existing, expected):
            raise SchemaInitializationError(
                f"Índice incompatible existente: {expected.collection}.{expected.name}. "
                "No se modifica porque requeriría una operación destructiva/drop."
            )
        result.unchanged_indexes.append(f"{expected.collection}.{expected.name}")
        return

    database[expected.collection].create_index(list(expected.keys), **expected.create_kwargs())
    result.created_indexes.append(f"{expected.collection}.{expected.name}")


def initialize_schema(database: Database) -> SchemaInitResult:
    result = SchemaInitResult(database=database.name)
    validators = expected_validators()

    for collection_name in expected_collections():
        _ensure_collection(database, collection_name, validators[collection_name], result)

    for index in expected_indexes():
        _ensure_index(database, index, result)

    return result


def run_initialize() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = initialize_schema(client[settings.mongodb_database])
        return result.format()
    finally:
        client.close()


def main() -> None:
    print(run_initialize())


if __name__ == "__main__":
    main()

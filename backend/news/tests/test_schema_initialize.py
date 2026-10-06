"""Tests offline para el inicializador de schema."""

import pytest
from types import SimpleNamespace

from news.schema.collections import expected_collections
from news.schema.initialize import SchemaInitializationError, initialize_schema
from news.schema.validators import expected_validators


class FakeCollection:
    def __init__(self, name: str) -> None:
        self.name = name
        self.indexes = {
            "_id_": {
                "name": "_id_",
                "key": {"_id": 1},
            }
        }
        self.insert_calls = 0
        self.drop_calls = 0
        self.documents = {}

    def list_indexes(self):
        return list(self.indexes.values())

    def create_index(self, keys, **kwargs):
        name = kwargs["name"]
        self.indexes[name] = {"name": name, "key": dict(keys)}
        if kwargs.get("unique"):
            self.indexes[name]["unique"] = True
        if "expireAfterSeconds" in kwargs:
            self.indexes[name]["expireAfterSeconds"] = kwargs["expireAfterSeconds"]
        return name

    def insert_one(self, document):
        self.insert_calls += 1
        self.documents[document["_id"]] = document
        return SimpleNamespace(inserted_id=document["_id"])

    def find_one(self, query, _projection=None):
        for document in self.documents.values():
            if all(document.get(key) == value for key, value in query.items()):
                return document
        return None

    def replace_one(self, filter_query, replacement, upsert=False):
        document_id = filter_query["_id"]
        existed = document_id in self.documents
        if existed or upsert:
            self.documents[document_id] = replacement
        return SimpleNamespace(
            upserted_id=None if existed else document_id,
            modified_count=1 if existed else 0,
        )

    def drop(self):
        self.drop_calls += 1


class FakeDatabase:
    def __init__(self) -> None:
        self.name = "fake_news"
        self.collections: dict[str, FakeCollection] = {}
        self.options: dict[str, dict] = {}
        self.commands: list[tuple] = []

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self.collections:
            self.collections[name] = FakeCollection(name)
        return self.collections[name]

    def list_collection_names(self):
        return list(self.collections)

    def create_collection(self, name: str, **options):
        self.collections[name] = FakeCollection(name)
        self.options[name] = options
        return self.collections[name]

    def command(self, command_name, *args, **kwargs):
        self.commands.append((command_name, args, kwargs))
        if command_name == "listCollections":
            name = kwargs["filter"]["name"]
            if name not in self.collections:
                return {"cursor": {"firstBatch": []}}
            return {
                "cursor": {
                    "firstBatch": [
                        {
                            "name": name,
                            "options": self.options.get(name, {}),
                        }
                    ]
                }
            }
        if command_name == "collMod":
            name = args[0]
            self.options[name] = kwargs
            return {"ok": 1}
        raise AssertionError(f"Unexpected command: {command_name}")


def test_initialize_schema_creates_missing_collections_validators_and_indexes() -> None:
    db = FakeDatabase()
    result = initialize_schema(db)

    assert set(db.list_collection_names()) == set(expected_collections())
    assert set(result.created_collections) == set(expected_collections())
    assert result.created_indexes
    for collection in expected_collections():
        assert db.options[collection]["validator"] == expected_validators()[collection]


def test_initialize_schema_is_idempotent_on_second_run() -> None:
    db = FakeDatabase()
    first = initialize_schema(db)
    second = initialize_schema(db)

    assert first.changed is True
    assert second.created_collections == []
    assert second.synchronized_validators == []
    assert second.created_indexes == []
    assert second.changed is False


def test_initialize_schema_does_not_insert_or_drop_documents() -> None:
    db = FakeDatabase()
    initialize_schema(db)

    for collection in db.collections.values():
        assert collection.insert_calls == 0
        assert collection.drop_calls == 0


def test_initialize_schema_refuses_incompatible_existing_index() -> None:
    db = FakeDatabase()
    for collection_name in expected_collections():
        db.create_collection(
            collection_name,
            validator=expected_validators()[collection_name],
            validationLevel="strict",
            validationAction="error",
        )
    db["users"].indexes["uq_users_firebase_uid"] = {
        "name": "uq_users_firebase_uid",
        "key": {"email": 1},
        "unique": True,
    }

    with pytest.raises(SchemaInitializationError):
        initialize_schema(db)

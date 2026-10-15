"""Tests offline para el reseed seguro de datos controlados (Loop 06).

El reseed elimina UNICAMENTE el dataset administrado por los seeders
(16 locations + 32 news demo) identificado por identidades versionadas
(countryCode+_id determinista, slug+_id determinista) y lo reconstruye
desde las fuentes del repositorio.

Toda la suite es offline: usa fakes en memoria, sin Atlas ni Docker.
"""

from types import SimpleNamespace

from bson import ObjectId

from news.demo_news import get_demo_news_documents
from news.news_check import check_news_data
from news.schema.check import check_schema
from news.seed_catalog import CATALOG_LOCATION_IDS, seed_catalog_data
from news.seed_check import check_catalog_data
from news.seed_news import seed_news_data
from news.tests.test_schema_initialize import FakeCollection, FakeDatabase


class TrackedFakeCollection(FakeCollection):
    """FakeCollection que registra inserts/deletes y prohibe borrados amplios."""

    def __init__(self, name: str, database: "TrackedFakeDatabase | None" = None) -> None:
        super().__init__(name)
        self._database = database

    def _record(self, op: str) -> None:
        if self._database is not None:
            self._database.order.append(f"{op}_{self.name}")

    def insert_one(self, document):
        self._record("insert")
        return super().insert_one(document)

    def delete_many(self, filter):
        if not filter:
            raise ValueError("refused broad delete_many({})")
        ids = (filter.get("_id") or {}).get("$in", None)
        if ids is None:
            raise ValueError("only _id $in deletes are supported")
        if self._database is not None:
            self._database.deletes.append((self.name, {"_id": {"$in": list(ids)}}))
        removed = 0
        for doc_id in list(ids):
            if doc_id in self.documents:
                del self.documents[doc_id]
                removed += 1
        self._record("delete")
        return SimpleNamespace(deleted_count=removed)

    def delete_one(self, filter):
        if not filter:
            raise ValueError("refused broad delete_one({})")
        if self._database is not None:
            self._database.deletes.append((self.name, dict(filter)))
        target = filter.get("_id", object())
        if target in self.documents:
            del self.documents[target]
            self._record("delete")
            return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)


class TrackedFakeDatabase(FakeDatabase):
    """FakeDatabase con log global de orden y registro de deletes."""

    def __init__(self) -> None:
        super().__init__()
        self.order: list[str] = []
        self.deletes: list[tuple] = []

    def __getitem__(self, name: str) -> TrackedFakeCollection:
        if name not in self.collections:
            self.collections[name] = TrackedFakeCollection(name, self)
        collection = self.collections[name]
        assert isinstance(collection, TrackedFakeCollection)
        return collection

    def create_collection(self, name: str, **options):
        self.collections[name] = TrackedFakeCollection(name, self)
        self.options[name] = options
        return self.collections[name]


def _seeded_db() -> TrackedFakeDatabase:
    db = TrackedFakeDatabase()
    seed_catalog_data(db)
    seed_news_data(db)
    db.order.clear()
    db.deletes.clear()
    return db


def _snapshot(db: TrackedFakeDatabase) -> dict:
    return {
        name: dict(db.collections[name].documents)
        for name in db.collections
    }


def _add_external_location(db: TrackedFakeDatabase) -> dict:
    doc = {
        "_id": ObjectId(),
        "name": "Estados Unidos",
        "country": "Estados Unidos",
        "countryCode": "US",
        "level": "country",
        "active": True,
    }
    db["locations"].insert_one(doc)
    return doc


def _add_external_news(db: TrackedFakeDatabase) -> dict:
    doc = {"_id": ObjectId(), "slug": "noticia-ajena-fuera-del-dataset"}
    db["news"].insert_one(doc)
    return doc


def _add_other_collection_docs(db: TrackedFakeDatabase) -> dict[str, dict]:
    docs = {}
    for name in ("users", "userInteractions", "chatSessions", "aiUsage", "auditLogs"):
        doc = {"_id": ObjectId(), "marker": f"keep-{name}"}
        db[name].insert_one(doc)
        docs[name] = doc
    return docs


def _replace_location_id(db: TrackedFakeDatabase, code: str) -> None:
    docs = db["locations"].documents
    key = next(k for k, doc in docs.items() if doc.get("countryCode") == code)
    doc = dict(docs.pop(key))
    doc["_id"] = ObjectId()
    docs[doc["_id"]] = doc


# --- Confirmation ---


def test_wrong_confirmation_aborts_with_zero_modifications() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    before = _snapshot(db)

    result = execute_reseed(db, mode="local", database_name=db.name, confirmation="yes")

    assert result.aborted is True
    assert result.deleted_locations == 0
    assert result.deleted_news == 0
    assert result.inserted_locations == 0
    assert result.inserted_news == 0
    assert db.deletes == []
    assert _snapshot(db) == before


def test_empty_confirmation_aborts() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    before = _snapshot(db)

    for confirmation in ("", "y", "yes", "\n", "RESEED wrong_db"):
        result = execute_reseed(
            db, mode="local", database_name=db.name, confirmation=confirmation
        )
        assert result.aborted is True, confirmation
        assert _snapshot(db) == before


def test_exact_local_confirmation_allows_reseed() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()

    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is False
    assert result.deleted_locations == 16
    assert result.deleted_news == 32
    assert result.inserted_locations == 16
    assert result.inserted_news == 32


def test_exact_atlas_confirmation_allows_atlas_reseed() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()

    result = execute_reseed(
        db, mode="atlas", database_name=db.name, confirmation=f"RESEED ATLAS {db.name}"
    )

    assert result.aborted is False
    assert result.deleted_locations == 16
    assert result.deleted_news == 32


def test_local_phrase_never_authorizes_atlas() -> None:
    from news.reseed import execute_reseed, expected_confirmation, is_confirmation_valid

    assert expected_confirmation("db", "local") != expected_confirmation("db", "atlas")
    assert is_confirmation_valid("RESEED db", "db", "local") is True
    assert is_confirmation_valid("RESEED db", "db", "atlas") is False

    db = _seeded_db()
    before = _snapshot(db)
    result = execute_reseed(
        db, mode="atlas", database_name=db.name, confirmation=f"RESEED {db.name}"
    )
    assert result.aborted is True
    assert db.deletes == []
    assert _snapshot(db) == before


# --- Ownership ---


def test_ownership_recognizes_controlled_locations() -> None:
    from news.reseed import classify_controlled

    db = _seeded_db()
    ownership = classify_controlled(db)

    assert len(ownership.location_ids_to_delete) == 16
    assert set(ownership.location_ids_to_delete) == set(CATALOG_LOCATION_IDS.values())
    assert ownership.location_drift == []


def test_ownership_recognizes_controlled_news() -> None:
    from news.reseed import classify_controlled

    db = _seeded_db()
    expected_ids = {doc["_id"] for doc in get_demo_news_documents()}
    ownership = classify_controlled(db)

    assert len(ownership.news_ids_to_delete) == 32
    assert set(ownership.news_ids_to_delete) == expected_ids
    assert ownership.news_drift == []


def test_ownership_never_classifies_externals_as_controlled() -> None:
    from news.reseed import classify_controlled

    db = _seeded_db()
    _add_external_location(db)
    _add_external_news(db)

    ownership = classify_controlled(db)

    assert len(ownership.location_ids_to_delete) == 16
    assert len(ownership.news_ids_to_delete) == 32
    assert ownership.external_locations == 1
    assert ownership.external_news == 1


def test_location_id_mismatch_is_dangerous_drift_and_aborts() -> None:
    from news.reseed import classify_controlled, execute_reseed, preflight

    db = _seeded_db()
    _replace_location_id(db, "GT")

    ownership = classify_controlled(db)
    assert ownership.location_drift

    pre = preflight(db, mode="local", database_name=db.name)
    assert pre.ok is False

    before = _snapshot(db)
    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )
    assert result.aborted is True
    assert db.deletes == []
    assert _snapshot(db) == before


def test_duplicate_country_code_aborts_reseed() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    db["locations"].insert_one(
        {
            "_id": ObjectId(),
            "name": "Guatemala duplicada",
            "country": "Guatemala",
            "countryCode": "GT",
            "level": "country",
            "active": True,
        }
    )
    before = _snapshot(db)

    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is True
    assert db.deletes == []
    assert _snapshot(db) == before


def test_duplicate_slug_aborts_reseed() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    original = get_demo_news_documents()[0]
    duplicate = dict(original)
    duplicate["_id"] = ObjectId()
    db["news"].insert_one(duplicate)
    before = _snapshot(db)

    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is True
    assert db.deletes == []
    assert _snapshot(db) == before


# --- Dry run ---


def test_dry_run_reports_real_counts_and_writes_nothing() -> None:
    from news.reseed import plan_dry_run

    db = _seeded_db()
    before = _snapshot(db)
    inserts_before = {
        name: db.collections[name].insert_calls for name in db.collections
    }

    plan = plan_dry_run(db, mode="local", database_name=db.name)

    assert plan.locations_to_delete == 16
    assert plan.demo_news_to_delete == 32
    assert plan.database == db.name
    assert plan.mode == "local"
    assert _snapshot(db) == before
    assert {
        name: db.collections[name].insert_calls for name in db.collections
    } == inserts_before
    assert db.deletes == []
    assert "No changes performed." in plan.format()
    assert f"Database: {db.name}" in plan.format()
    assert "Mode: local" in plan.format()


def test_dry_run_identifies_externals_and_preserved_collections() -> None:
    from news.reseed import plan_dry_run

    db = _seeded_db()
    _add_external_location(db)
    _add_external_news(db)

    plan = plan_dry_run(db, mode="atlas", database_name=db.name)

    assert plan.locations_to_delete == 16
    assert plan.demo_news_to_delete == 32
    assert plan.external_locations == 1
    assert plan.external_news == 1
    assert plan.mode == "atlas"
    rendered = plan.format()
    for preserved in (
        "users",
        "userInteractions",
        "chatSessions",
        "aiUsage",
        "auditLogs",
        "external locations",
        "external news",
    ):
        assert preserved in rendered


# --- Reseed behavior ---


def test_reseed_deletes_news_first_and_rebuilds_locations_first() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is False
    assert db.order == (
        ["delete_news", "delete_locations"]
        + ["insert_locations"] * 16
        + ["insert_news"] * 32
    )
    assert result.order == [
        "delete_news",
        "delete_locations",
        "seed_locations",
        "seed_news",
        "checks",
    ]


def test_reseed_ends_with_16_locations_and_32_news() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is False
    assert len(db["locations"].documents) == 16
    assert len(db["news"].documents) == 32
    assert check_schema(db).ok is True
    assert check_catalog_data(db).ok is True
    assert check_news_data(db).ok is True
    assert result.inserted_locations == 16
    assert result.inserted_news == 32


def test_reseed_second_run_produces_same_dataset() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    first = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )
    codes_first = sorted(
        doc["countryCode"] for doc in db["locations"].documents.values()
    )
    slugs_first = sorted(doc["slug"] for doc in db["news"].documents.values())

    second = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert first.aborted is False
    assert second.aborted is False
    assert second.deleted_locations == 16
    assert second.deleted_news == 32
    assert second.inserted_locations == 16
    assert second.inserted_news == 32
    assert (
        sorted(doc["countryCode"] for doc in db["locations"].documents.values())
        == codes_first
    )
    assert (
        sorted(doc["slug"] for doc in db["news"].documents.values()) == slugs_first
    )


def test_reseed_preserves_externals() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    ext_location = _add_external_location(db)
    ext_news = _add_external_news(db)

    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is False
    assert db["locations"].documents[ext_location["_id"]] == ext_location
    assert db["news"].documents[ext_news["_id"]] == ext_news
    assert len(db["locations"].documents) == 17
    assert len(db["news"].documents) == 33
    assert result.preserved_external == 2


def test_reseed_preserves_other_five_collections() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    kept = _add_other_collection_docs(db)

    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is False
    for name, doc in kept.items():
        assert db[name].documents[doc["_id"]] == doc


def test_reseed_never_uses_broad_deletes() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    expected_ids = set(CATALOG_LOCATION_IDS.values()) | {
        doc["_id"] for doc in get_demo_news_documents()
    }

    execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert db.deletes
    for _collection, filt in db.deletes:
        assert set(filt) == {"_id"}
        ids = filt["_id"]["$in"]
        assert ids
        assert set(ids) <= expected_ids


def test_reseed_never_drops() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert not hasattr(db, "drop_database")
    for collection in db.collections.values():
        assert collection.drop_calls == 0


# --- Failures ---


def test_failed_preflight_means_zero_deletes() -> None:
    from news.reseed import execute_reseed

    db = TrackedFakeDatabase()
    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is True
    assert "schema" in result.abort_reason.lower()
    assert db.deletes == []
    assert all(
        collection.documents == {} for collection in db.collections.values()
    )


def test_intermediate_failure_reports_incomplete_state_honestly(
    monkeypatch,
) -> None:
    from news import reseed as reseed_module
    from news.reseed import execute_reseed

    def _boom(_database):
        raise RuntimeError("boom-seed-news")

    monkeypatch.setattr(reseed_module, "seed_news_data", _boom)

    db = _seeded_db()
    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is False
    assert result.incomplete is True
    assert "boom-seed-news" in result.error
    assert result.deleted_news == 32
    assert result.deleted_locations == 16
    assert result.inserted_locations == 16
    assert result.inserted_news == 0
    assert len(db["locations"].documents) == 16
    assert len(db["news"].documents) == 0
    # Honesto: declara que NO hubo rollback en vez de afirmarlo.
    assert "No rollback was performed" in result.format()
    assert "rolled back" not in result.format().lower()


def test_post_check_failure_is_reported_without_hiding() -> None:
    from news.reseed import execute_reseed

    db = _seeded_db()
    _add_external_news(db)

    result = execute_reseed(
        db, mode="local", database_name=db.name, confirmation=f"RESEED {db.name}"
    )

    assert result.aborted is False
    assert result.incomplete is False
    assert result.verification_failed is True
    assert result.checks["news_ok"] is False
    assert len(db["news"].documents) == 33

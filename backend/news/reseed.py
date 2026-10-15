"""Reseed seguro del dataset controlado (Loop 06).

`reseed` significa: eliminar UNICAMENTE el dataset administrado por
nuestros seeders (16 `locations` + 32 `news` demo) y reconstruirlo desde
las fuentes versionadas del repositorio.

NO significa vaciar la base, borrar users/interacciones/chats/aiUsage/
auditLogs, ni borrar locations o noticias externas.

Reglas de seguridad implementadas:

- Ownership explicito: una location solo se elimina si su `countryCode`
  esperado existe con el `_id` determinista esperado; una noticia solo si
  su `slug` esperado existe con el `_id` determinista esperado.
- Cualquier drift peligroso (duplicados o `_id` inesperado en una
  identidad controlada) aborta con cero modificaciones.
- Deletes exclusivamente con ``delete_many({"_id": {"$in": [...]}})``
  derivados del dataset versionado. Nunca ``delete_many({})``, nunca
  filtros amplios (status/level/topics), nunca `drop`.
- Confirmacion humana exacta y diferenciada por modo:
  local ``RESEED <db>``, Atlas ``RESEED ATLAS <db>``. Sin ``--force``.
- Orden: elimina news antes que locations; reconstruye locations antes
  que news.
- Sin atomicidad multi-coleccion asumida: los fallos intermedios se
  reportan como estado incompleto, nunca como rollback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from pymongo.database import Database

from .config import get_news_settings
from .database import get_news_client
from .demo_news import get_demo_news_documents
from .news_check import check_news_data
from .schema.check import check_schema
from .seed_catalog import CATALOG_LOCATION_IDS, seed_catalog_data
from .seed_check import check_catalog_data
from .seed_news import seed_news_data

LOCAL_MODE = "local"
ATLAS_MODE = "atlas"
KNOWN_MODES = (LOCAL_MODE, ATLAS_MODE)


def expected_confirmation(database_name: str, mode: str) -> str:
    """Frase exacta requerida para autorizar el reseed en un modo dado."""
    if mode == ATLAS_MODE:
        return f"RESEED ATLAS {database_name}"
    return f"RESEED {database_name}"


def is_confirmation_valid(
    provided: str | None, database_name: str, mode: str
) -> bool:
    """Coincidencia exacta contra la frase del modo; lo demas aborta."""
    if not provided:
        return False
    return provided == expected_confirmation(database_name, mode)


@dataclass
class Ownership:
    location_ids_to_delete: list = field(default_factory=list)
    news_ids_to_delete: list = field(default_factory=list)
    location_drift: list[str] = field(default_factory=list)
    news_drift: list[str] = field(default_factory=list)
    missing_locations: list[str] = field(default_factory=list)
    missing_news: list[str] = field(default_factory=list)
    external_locations: int = 0
    external_news: int = 0


def classify_controlled(database: Database) -> Ownership:
    """Clasifica el dataset controlado sin escribir nada.

    Solo reconoce como controlados los documentos cuya identidad
    versionada coincide por completo (codigo+_id, slug+_id). Los
    externos se cuentan como preservados, nunca como eliminables.
    """
    ownership = Ownership()

    expected_locations = dict(CATALOG_LOCATION_IDS)
    by_code: dict = {}
    for document in database["locations"].find({}):
        by_code.setdefault(document.get("countryCode"), []).append(document)
    for code, expected_id in expected_locations.items():
        docs = by_code.get(code, [])
        if len(docs) > 1:
            ownership.location_drift.append(
                f"locations:{code}:duplicate:{len(docs)}"
            )
        elif len(docs) == 1:
            if docs[0].get("_id") != expected_id:
                ownership.location_drift.append(
                    f"locations:{code}:id-mismatch"
                )
            else:
                ownership.location_ids_to_delete.append(expected_id)
        else:
            ownership.missing_locations.append(code)
    ownership.external_locations = sum(
        len(docs) for code, docs in by_code.items() if code not in expected_locations
    )

    expected_news = {doc["slug"]: doc["_id"] for doc in get_demo_news_documents()}
    by_slug: dict = {}
    for document in database["news"].find({}):
        by_slug.setdefault(document.get("slug"), []).append(document)
    for slug, expected_id in expected_news.items():
        docs = by_slug.get(slug, [])
        if len(docs) > 1:
            ownership.news_drift.append(f"news:{slug}:duplicate:{len(docs)}")
        elif len(docs) == 1:
            if docs[0].get("_id") != expected_id:
                ownership.news_drift.append(f"news:{slug}:id-mismatch")
            else:
                ownership.news_ids_to_delete.append(expected_id)
        else:
            ownership.missing_news.append(slug)
    ownership.external_news = sum(
        len(docs) for slug, docs in by_slug.items() if slug not in expected_news
    )

    return ownership


@dataclass
class PreflightResult:
    database: str
    mode: str
    ok: bool = False
    reasons: list[str] = field(default_factory=list)
    schema_ok: bool = False
    locations_to_delete: int = 0
    demo_news_to_delete: int = 0
    drift: list[str] = field(default_factory=list)


def preflight(database: Database, mode: str, database_name: str) -> PreflightResult:
    """Guard no destructivo previo a cualquier delete."""
    result = PreflightResult(database=database_name, mode=mode)
    if mode not in KNOWN_MODES:
        result.reasons.append(f"unknown target mode: {mode!r}")
    if not database_name:
        result.reasons.append("unknown database")
    schema = check_schema(database)
    result.schema_ok = schema.ok
    if not schema.ok:
        result.reasons.append("schema check failed")
    ownership = classify_controlled(database)
    result.locations_to_delete = len(ownership.location_ids_to_delete)
    result.demo_news_to_delete = len(ownership.news_ids_to_delete)
    result.drift = ownership.location_drift + ownership.news_drift
    if result.drift:
        result.reasons.append("ownership drift: " + "; ".join(result.drift))
    result.ok = not result.reasons
    return result


@dataclass
class DryRunResult:
    database: str
    mode: str
    locations_to_delete: int = 0
    demo_news_to_delete: int = 0
    external_locations: int = 0
    external_news: int = 0
    drift: list[str] = field(default_factory=list)

    def format(self) -> str:
        lines = [
            "=== AI Assisted News — Reseed Dry Run ===",
            f"Database: {self.database}",
            f"Mode: {self.mode}",
            "",
            "Controlled data:",
            f"- locations to delete: {self.locations_to_delete}",
            f"- demo news to delete: {self.demo_news_to_delete}",
            "",
            "Preserved:",
            "- users",
            "- userInteractions",
            "- chatSessions",
            "- aiUsage",
            "- auditLogs",
            "- external locations",
            "- external news",
            "",
            f"External (preserved, not deleted): locations={self.external_locations} news={self.external_news}",
            "",
            "No changes performed.",
        ]
        if self.drift:
            lines.append("")
            lines.append("Warnings (reseed would abort):")
            for item in self.drift:
                lines.append(f"- {item}")
        return "\n".join(lines)


def plan_dry_run(database: Database, mode: str, database_name: str) -> DryRunResult:
    """Inspeccion real no destructiva del plan de reseed."""
    ownership = classify_controlled(database)
    return DryRunResult(
        database=database_name,
        mode=mode,
        locations_to_delete=len(ownership.location_ids_to_delete),
        demo_news_to_delete=len(ownership.news_ids_to_delete),
        external_locations=ownership.external_locations,
        external_news=ownership.external_news,
        drift=ownership.location_drift + ownership.news_drift,
    )


@dataclass
class ReseedResult:
    database: str
    mode: str
    aborted: bool = False
    abort_reason: str = ""
    deleted_news: int = 0
    deleted_locations: int = 0
    inserted_locations: int = 0
    inserted_news: int = 0
    preserved_external_locations: int = 0
    preserved_external_news: int = 0
    preserved_external: int = 0
    order: list[str] = field(default_factory=list)
    incomplete: bool = False
    error: str = ""
    verification_failed: bool = False
    checks: dict = field(default_factory=dict)

    def format(self) -> str:
        if self.aborted:
            return "\n".join(
                [
                    "=== AI Assisted News — Reseed ABORTED ===",
                    f"Database: {self.database}",
                    f"Mode: {self.mode}",
                    f"Reason: {self.abort_reason}",
                    "Zero modifications performed.",
                ]
            )
        lines = [
            "=== AI Assisted News — Reseed ===",
            f"Database: {self.database}",
            f"Mode: {self.mode}",
            f"Deleted demo news: {self.deleted_news}",
            f"Deleted locations: {self.deleted_locations}",
            f"Inserted locations: {self.inserted_locations}",
            f"Inserted news: {self.inserted_news}",
            f"Preserved external: {self.preserved_external}",
            f"Order: {', '.join(self.order) if self.order else 'none'}",
        ]
        if self.incomplete:
            lines.append(f"INCOMPLETE: {self.error}")
            lines.append("No rollback was performed; re-run db-bootstrap to recover.")
        elif self.verification_failed:
            lines.append("Reseed completed but verification failed:")
            for key, value in sorted(self.checks.items()):
                lines.append(f"- {key}: {'OK' if value else 'DRIFT'}")
        else:
            lines.append("Verification: OK (schema, catalogs, demo news).")
        return "\n".join(lines)


def execute_reseed(
    database: Database,
    mode: str,
    database_name: str,
    confirmation: str | None = None,
) -> ReseedResult:
    """Ejecuta el reseed autorizado. Interfaz programatica para tests.

    El CLI humano (`python -m news.reseed` / `make db-reseed`) lee la
    confirmacion de la variable `CONFIRM`; los tests llaman aqui con la
    frase exacta, sin confirmacion interactiva real.
    """
    result = ReseedResult(database=database_name, mode=mode)

    if not is_confirmation_valid(confirmation or "", database_name, mode):
        result.aborted = True
        result.abort_reason = "confirmation mismatch: reseed aborted"
        return result
    if mode not in KNOWN_MODES:
        result.aborted = True
        result.abort_reason = f"unknown target mode: {mode!r}"
        return result
    if not database_name:
        result.aborted = True
        result.abort_reason = "unknown database"
        return result

    pre = preflight(database, mode, database_name)
    if not pre.ok:
        result.aborted = True
        result.abort_reason = "; ".join(pre.reasons)
        return result

    ownership = classify_controlled(database)
    result.preserved_external_locations = ownership.external_locations
    result.preserved_external_news = ownership.external_news
    result.preserved_external = (
        ownership.external_locations + ownership.external_news
    )

    try:
        if ownership.news_ids_to_delete:
            deletion = database["news"].delete_many(
                {"_id": {"$in": list(ownership.news_ids_to_delete)}}
            )
            result.deleted_news = deletion.deleted_count
            result.order.append("delete_news")
        if ownership.location_ids_to_delete:
            deletion = database["locations"].delete_many(
                {"_id": {"$in": list(ownership.location_ids_to_delete)}}
            )
            result.deleted_locations = deletion.deleted_count
            result.order.append("delete_locations")
        catalog = seed_catalog_data(database)
        result.inserted_locations = catalog.inserted
        result.order.append("seed_locations")
        news = seed_news_data(database)
        result.inserted_news = news.inserted
        result.order.append("seed_news")
    except Exception as error:
        result.incomplete = True
        result.error = f"reseed incomplete after partial writes: {error}"
        return result

    result.order.append("checks")
    try:
        schema_ok = check_schema(database).ok
        catalog_ok = check_catalog_data(database).ok
        news_ok = check_news_data(database).ok
        result.checks = {
            "schema_ok": schema_ok,
            "catalog_ok": catalog_ok,
            "news_ok": news_ok,
        }
        result.verification_failed = not (schema_ok and catalog_ok and news_ok)
    except Exception as error:
        result.verification_failed = True
        result.error = f"post checks failed to run: {error}"
    return result


def run_reseed(confirmation: str) -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = execute_reseed(
            client[settings.mongodb_database],
            settings.mongodb_mode,
            settings.mongodb_database,
            confirmation,
        )
        return result.format()
    finally:
        client.close()


def main() -> None:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = execute_reseed(
            client[settings.mongodb_database],
            settings.mongodb_mode,
            settings.mongodb_database,
            os.environ.get("CONFIRM", ""),
        )
        print(result.format())
        if result.aborted or result.incomplete or result.verification_failed:
            raise SystemExit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()

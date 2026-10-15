"""Bootstrap idempotente no destructivo (Loop 06).

Equivale a `db-init` + `db-seed-catalogs` + `db-seed-news` + checks.
Nunca elimina datos, por eso no requiere confirmacion. Sirve para:
clonar repo -> configurar keys/env -> levantar DB -> obtener estructura
+ dataset demo.
"""

from __future__ import annotations

from dataclasses import dataclass

from pymongo.database import Database

from .config import get_news_settings
from .database import get_news_client
from .news_check import check_news_data
from .schema.check import check_schema
from .schema.initialize import initialize_schema
from .seed_catalog import seed_catalog_data
from .seed_check import check_catalog_data
from .seed_news import seed_news_data


@dataclass
class BootstrapResult:
    database: str
    inserted_locations: int = 0
    unchanged_locations: int = 0
    inserted_news: int = 0
    unchanged_news: int = 0
    schema_ok: bool = False
    catalog_ok: bool = False
    news_ok: bool = False

    @property
    def ok(self) -> bool:
        return self.schema_ok and self.catalog_ok and self.news_ok

    def format(self) -> str:
        return "\n".join(
            [
                "=== AI Assisted News — DB Bootstrap ===",
                f"Database: {self.database}",
                "Steps: db-init, db-seed-catalogs, db-seed-news, checks",
                "No collections, documents or indexes will be dropped or deleted.",
                "",
                f"Locations inserted: {self.inserted_locations}",
                f"Locations unchanged: {self.unchanged_locations}",
                f"News inserted: {self.inserted_news}",
                f"News unchanged: {self.unchanged_news}",
                f"Schema: {'OK' if self.schema_ok else 'DRIFT'}",
                f"Catalogs: {'OK' if self.catalog_ok else 'DRIFT'}",
                f"Demo news: {'OK' if self.news_ok else 'DRIFT'}",
                f"Bootstrap: {'OK' if self.ok else 'FAILED'}",
            ]
        )


def bootstrap_data(database: Database) -> BootstrapResult:
    """Ejecuta init + seeds + checks sin eliminar nada."""
    result = BootstrapResult(database=database.name)
    initialize_schema(database)
    catalog = seed_catalog_data(database)
    result.inserted_locations = catalog.inserted
    result.unchanged_locations = catalog.unchanged
    news = seed_news_data(database)
    result.inserted_news = news.inserted
    result.unchanged_news = news.unchanged
    result.schema_ok = check_schema(database).ok
    result.catalog_ok = check_catalog_data(database).ok
    result.news_ok = check_news_data(database).ok
    return result


def run_bootstrap() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        return bootstrap_data(client[settings.mongodb_database]).format()
    finally:
        client.close()


def main() -> None:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = bootstrap_data(client[settings.mongodb_database])
        print(result.format())
        if not result.ok:
            raise SystemExit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()

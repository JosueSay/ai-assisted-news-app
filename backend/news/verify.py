"""Verificacion integral no destructiva (Loop 06).

Ejecuta schema check + catalog check + news check. Solo lee, nunca
escribe ni reseed. Documenta exactamente que verifica: estructura
fisica (colecciones, validators, indices, TTL), catalogo locations
(16/16 sin faltantes/duplicados/ajenos) y dataset demo (32/32 con
cobertura, topics, estados y coherencia).
"""

from __future__ import annotations

from dataclasses import dataclass

from pymongo.database import Database

from .config import get_news_settings
from .database import get_news_client
from .news_check import check_news_data
from .schema.check import check_schema
from .seed_check import check_catalog_data


@dataclass
class VerifyResult:
    database: str
    mode: str
    schema_ok: bool = False
    catalog_ok: bool = False
    news_ok: bool = False

    @property
    def ok(self) -> bool:
        return self.schema_ok and self.catalog_ok and self.news_ok

    def format(self) -> str:
        return "\n".join(
            [
                f"Database verification: {'OK' if self.ok else 'FAILED'}",
                f"Database: {self.database}",
                f"Mode: {self.mode}",
                "Checks: schema (collections, validators, indexes, TTL),",
                "catalogs (16 locations), demo news (32 news).",
                f"Schema: {'OK' if self.schema_ok else 'DRIFT'}",
                f"Catalogs: {'OK' if self.catalog_ok else 'DRIFT'}",
                f"Demo news: {'OK' if self.news_ok else 'DRIFT'}",
            ]
        )


def verify_data(
    database: Database, mode: str = "unknown", database_name: str | None = None
) -> VerifyResult:
    """Solo lectura: no inserta, modifica ni elimina."""
    return VerifyResult(
        database=database_name or database.name,
        mode=mode,
        schema_ok=check_schema(database).ok,
        catalog_ok=check_catalog_data(database).ok,
        news_ok=check_news_data(database).ok,
    )


def run_verify() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        return verify_data(
            client[settings.mongodb_database],
            settings.mongodb_mode,
            settings.mongodb_database,
        ).format()
    finally:
        client.close()


def main() -> None:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = verify_data(
            client[settings.mongodb_database],
            settings.mongodb_mode,
            settings.mongodb_database,
        )
        print(result.format())
        if not result.ok:
            raise SystemExit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()

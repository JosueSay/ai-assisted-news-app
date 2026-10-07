"""Seeder idempotente para catálogos controlados de la app de noticias."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from bson import ObjectId
from pymongo.database import Database

from .config import get_news_settings
from .database import get_news_client
from .models import LocationLevel
from .models.location import Location
from .schema.initialize import initialize_schema

CATALOG_CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)

CATALOG_LOCATION_IDS = {
    "CA": ObjectId("670000000000000000001001"),
    "MX": ObjectId("670000000000000000001002"),
    "GT": ObjectId("670000000000000000000001"),
    "CR": ObjectId("670000000000000000001004"),
    "AR": ObjectId("670000000000000000001005"),
    "BR": ObjectId("670000000000000000001006"),
    "CU": ObjectId("670000000000000000001007"),
    "JM": ObjectId("670000000000000000001008"),
    "ES": ObjectId("670000000000000000001009"),
    "FR": ObjectId("670000000000000000001010"),
    "JP": ObjectId("670000000000000000001011"),
    "CN": ObjectId("670000000000000000001012"),
    "EG": ObjectId("670000000000000000001013"),
    "ZA": ObjectId("670000000000000000001014"),
    "AU": ObjectId("670000000000000000001015"),
    "NZ": ObjectId("670000000000000000001016"),
}

CATALOG_LOCATIONS = [
    {"code": "CA", "name": "Canadá", "country": "Canadá"},
    {"code": "MX", "name": "México", "country": "México"},
    {"code": "GT", "name": "Guatemala", "country": "Guatemala"},
    {"code": "CR", "name": "Costa Rica", "country": "Costa Rica"},
    {"code": "AR", "name": "Argentina", "country": "Argentina"},
    {"code": "BR", "name": "Brasil", "country": "Brasil"},
    {"code": "CU", "name": "Cuba", "country": "Cuba"},
    {"code": "JM", "name": "Jamaica", "country": "Jamaica"},
    {"code": "ES", "name": "España", "country": "España"},
    {"code": "FR", "name": "Francia", "country": "Francia"},
    {"code": "JP", "name": "Japón", "country": "Japón"},
    {"code": "CN", "name": "China", "country": "China"},
    {"code": "EG", "name": "Egipto", "country": "Egipto"},
    {"code": "ZA", "name": "Sudáfrica", "country": "Sudáfrica"},
    {"code": "AU", "name": "Australia", "country": "Australia"},
    {"code": "NZ", "name": "Nueva Zelanda", "country": "Nueva Zelanda"},
]


@dataclass
class CatalogSeedResult:
    database: str
    locations_upserted: int = 0
    locations_modified: int = 0

    def format(self) -> str:
        return "\n".join(
            [
                "=== AI Assisted News — Catalog Seed ===",
                f"Database: {self.database}",
                "Operation:",
                "- upsert controlled locations catalog",
                "",
                "No collections, documents or indexes will be dropped.",
                "",
                f"Locations expected: {len(CATALOG_LOCATIONS)}",
                f"Locations upserted: {self.locations_upserted}",
                f"Locations modified: {self.locations_modified}",
            ]
        )


def catalog_location_document(item: dict[str, str]) -> dict:
    code = item["code"]
    return Location(
        _id=CATALOG_LOCATION_IDS[code],
        name=item["name"],
        city=None,
        region=None,
        country=item["country"],
        countryCode=code,
        level=LocationLevel.country,
        active=True,
        createdAt=CATALOG_CREATED_AT,
    ).model_dump_mongo()


def seed_catalog_data(database: Database) -> CatalogSeedResult:
    initialize_schema(database)
    result = CatalogSeedResult(database=database.name)

    for item in CATALOG_LOCATIONS:
        document = catalog_location_document(item)
        upsert_result = database["locations"].replace_one(
            {"_id": document["_id"]},
            document,
            upsert=True,
        )
        if upsert_result.upserted_id:
            result.locations_upserted += 1
        else:
            result.locations_modified += upsert_result.modified_count

    return result


def run_seed_catalog() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = seed_catalog_data(client[settings.mongodb_database])
        return result.format()
    finally:
        client.close()


def main() -> None:
    print(run_seed_catalog())


if __name__ == "__main__":
    main()

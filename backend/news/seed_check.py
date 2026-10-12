"""Inspección no destructiva del catálogo de locations.

Solo lee la colección `locations` y reporta diferencias contra
`CATALOG_LOCATIONS` usando `countryCode` como identidad natural.
Nunca inserta, modifica ni elimina documentos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pymongo.database import Database

from .config import get_news_settings
from .database import get_news_client
from .seed_catalog import CATALOG_LOCATIONS


@dataclass
class CatalogCheckResult:
    database: str
    expected: int = len(CATALOG_LOCATIONS)
    found: int = 0
    missing: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.missing or self.duplicates or self.unexpected)

    def format(self) -> str:
        lines = [
            f"Catalog check: {'OK' if self.ok else 'DRIFT DETECTED'}",
            f"Database: {self.database}",
            f"Locations: {self.found}/{self.expected}",
            f"Duplicates: {len(self.duplicates)}",
        ]
        if self.missing:
            lines.append("Missing locations: " + ", ".join(self.missing))
        if self.duplicates:
            lines.append("Duplicated locations: " + ", ".join(self.duplicates))
        if self.unexpected:
            lines.append("Unexpected locations: " + ", ".join(self.unexpected))
        return "\n".join(lines)


def check_catalog_data(database: Database) -> CatalogCheckResult:
    expected_codes = [item["code"] for item in CATALOG_LOCATIONS]
    counts: dict[str, int] = {}
    for document in database["locations"].find({}):
        code = document.get("countryCode")
        counts[code] = counts.get(code, 0) + 1

    result = CatalogCheckResult(database=database.name, found=sum(counts.values()))
    result.missing = sorted(set(expected_codes) - set(counts))
    result.duplicates = sorted(code for code, total in counts.items() if total > 1)
    result.unexpected = sorted(set(counts) - set(expected_codes))
    return result


def run_seed_check() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = check_catalog_data(client[settings.mongodb_database])
        return result.format()
    finally:
        client.close()


def main() -> None:
    result = run_seed_check()
    print(result)
    if "DRIFT DETECTED" in result:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

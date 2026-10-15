"""Seeder idempotente para las noticias demo del Loop 05.

DEMO / SYNTHETIC DATA: persiste únicamente las fixtures sintéticas
generadas por `demo_news.py`. Solo escribe en la colección `news`:

- nunca crea documentos en `users` (Loop 05 lo prohíbe);
- nunca escribe en `locations` ni en ninguna otra colección;
- nunca modifica ni elimina documentos existentes;
- la identidad natural es `slug`: lo existente queda intacto.

`news.authorId` usa el identificador sintético determinista definido en
`demo_news.py`. MongoDB no impone foreign keys y tanto el modelo como el
validator solo exigen tipo ObjectId, por lo que la persistencia no requiere
insertar ningún user. La correspondencia con un usuario real queda pendiente
de decisión humana (ver documentación del generador).
"""

from __future__ import annotations

from dataclasses import dataclass

from pymongo.database import Database

from .config import get_news_settings
from .database import get_news_client
from .demo_news import EXPECTED_NEWS_COUNT, get_demo_news_documents
from .models.news import News
from .schema.initialize import initialize_schema


@dataclass
class NewsSeedResult:
    database: str
    inserted: int = 0
    unchanged: int = 0

    def format(self) -> str:
        return "\n".join(
            [
                "=== AI Assisted News — News Seed ===",
                f"Database: {self.database}",
                "Operation:",
                "- insert missing demo news by slug",
                "",
                "No collections, documents or indexes will be dropped.",
                "Existing documents are never modified nor deleted.",
                "No users are created by this seeder.",
                "",
                f"News expected: {EXPECTED_NEWS_COUNT}",
                f"News inserted: {self.inserted}",
                f"News unchanged: {self.unchanged}",
            ]
        )


def seed_news_data(
    database: Database, documents: list[dict] | None = None
) -> NewsSeedResult:
    initialize_schema(database)
    raw = documents if documents is not None else get_demo_news_documents()
    # Validar todo antes de escribir: un documento inválido aborta sin
    # persistir nada.
    validated = [News.model_validate(document) for document in raw]
    result = NewsSeedResult(database=database.name)

    for news in validated:
        existing = database["news"].find_one({"slug": news.slug})
        if existing is not None:
            result.unchanged += 1
            continue
        database["news"].insert_one(news.model_dump_mongo())
        result.inserted += 1

    return result


def run_seed_news() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = seed_news_data(client[settings.mongodb_database])
        return result.format()
    finally:
        client.close()


def main() -> None:
    print(run_seed_news())


if __name__ == "__main__":
    main()

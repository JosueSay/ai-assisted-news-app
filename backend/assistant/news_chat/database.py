"""Conexión asíncrona a la base de noticias.

Usa la misma configuración que backend/news (NEWS_DB_MODE, NEWS_MONGODB_*), de
modo que la URI de Atlas solo se lee desde keys/mongodb_uri y nunca desde .env.
"""

from __future__ import annotations

from typing import Any

from news.config import get_news_settings
from news.secret_loader import SecretFileError, load_secret
from pymongo import AsyncMongoClient

from ..config import ChatbotConfigurationError


def open_news_client() -> tuple[AsyncMongoClient[dict[str, Any]], str]:
    """Crea el cliente de la base de noticias y devuelve también el nombre de la base."""
    settings = get_news_settings()
    if settings.mongodb_mode == "local":
        uri = settings.mongodb_local_uri
    else:
        try:
            uri = load_secret(settings.mongodb_uri_file)
        except SecretFileError as error:
            raise ChatbotConfigurationError(
                "Falta keys/mongodb_uri para leer la base de noticias en modo Atlas."
            ) from error
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        uri,
        appname="assistant-news-chat",
        serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
        uuidRepresentation="standard",
    )
    return client, settings.mongodb_database

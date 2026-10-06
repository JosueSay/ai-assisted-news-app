"""Índices físicos esperados para la base de noticias."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymongo import ASCENDING, DESCENDING


@dataclass(frozen=True)
class IndexDefinition:
    collection: str
    name: str
    keys: tuple[tuple[str, int], ...]
    unique: bool = False
    expire_after_seconds: int | None = None
    access_pattern: str = ""

    def create_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"name": self.name}
        if self.unique:
            kwargs["unique"] = True
        if self.expire_after_seconds is not None:
            kwargs["expireAfterSeconds"] = self.expire_after_seconds
        return kwargs


INDEXES: tuple[IndexDefinition, ...] = (
    IndexDefinition(
        collection="users",
        name="uq_users_firebase_uid",
        keys=(("firebaseUid", ASCENDING),),
        unique=True,
        access_pattern="lookup de usuario por Firebase Authentication",
    ),
    IndexDefinition(
        collection="news",
        name="uq_news_slug",
        keys=(("slug", ASCENDING),),
        unique=True,
        access_pattern="detalle de noticia por slug compartible",
    ),
    IndexDefinition(
        collection="chatSessions",
        name="ttl_chat_sessions_expires_at",
        keys=(("expiresAt", ASCENDING),),
        expire_after_seconds=0,
        access_pattern="expiración automática de sesiones temporales",
    ),
    IndexDefinition(
        collection="news",
        name="idx_news_status_published_at",
        keys=(("status", ASCENDING), ("publishedAt", DESCENDING)),
        access_pattern="feed general de noticias publicadas recientes",
    ),
    IndexDefinition(
        collection="news",
        name="idx_news_location_status_published_at",
        keys=(
            ("geographicScope.locationIds", ASCENDING),
            ("status", ASCENDING),
            ("publishedAt", DESCENDING),
        ),
        access_pattern="feed geográfico por ubicación simulada",
    ),
    IndexDefinition(
        collection="news",
        name="idx_news_topics_status_published_at",
        keys=(("topics", ASCENDING), ("status", ASCENDING), ("publishedAt", DESCENDING)),
        access_pattern="feed y búsqueda por tema",
    ),
    IndexDefinition(
        collection="userInteractions",
        name="idx_interactions_user_created_at",
        keys=(("userId", ASCENDING), ("createdAt", DESCENDING)),
        access_pattern="historial reciente para inferir intereses",
    ),
    IndexDefinition(
        collection="userInteractions",
        name="idx_interactions_user_news_type",
        keys=(("userId", ASCENDING), ("newsId", ASCENDING), ("type", ASCENDING)),
        access_pattern="deduplicación/consulta de interacción por usuario y noticia",
    ),
    IndexDefinition(
        collection="aiUsage",
        name="idx_ai_usage_feature_created_at",
        keys=(("feature", ASCENDING), ("createdAt", DESCENDING)),
        access_pattern="consumo de IA por funcionalidad",
    ),
    IndexDefinition(
        collection="auditLogs",
        name="idx_audit_entity_created_at",
        keys=(("entityId", ASCENDING), ("createdAt", DESCENDING)),
        access_pattern="historial administrativo por noticia",
    ),
)


def expected_indexes() -> tuple[IndexDefinition, ...]:
    return INDEXES


def indexes_by_collection() -> dict[str, list[IndexDefinition]]:
    grouped: dict[str, list[IndexDefinition]] = {}
    for index in INDEXES:
        grouped.setdefault(index.collection, []).append(index)
    return grouped

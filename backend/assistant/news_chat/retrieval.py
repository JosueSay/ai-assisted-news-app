"""Lectura de noticias publicadas y cálculo del nivel de confianza.

Solo se leen noticias con `status = "published"`: son las únicas que pueden
citarse en `citedNewsIds`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from news.models import ConfidenceLevel, VerificationStatus

from .intent import ClassifiedQuery, normalize_text

# Ventana de noticias recientes sobre la que se filtra en memoria.
RECENT_NEWS_WINDOW = 200
LISTING_LIMIT = 5
ELABORATION_LIMIT = 3
CONTENT_MAX_CHARS = 4000

STRONG_SOURCE_TYPES = {"official", "primary_source"}

VERIFICATION_LABELS = {
    VerificationStatus.confirmed.value: "Confirmada",
    VerificationStatus.developing.value: "En desarrollo",
    VerificationStatus.insufficient_sources.value: "Fuentes insuficientes",
    VerificationStatus.conflicting_sources.value: "Fuentes contradictorias",
}

NEWS_PROJECTION = {
    "slug": 1,
    "title": 1,
    "summary": 1,
    "content": 1,
    "topics": 1,
    "keywords": 1,
    "geographicScope": 1,
    "verification": 1,
    "sources": 1,
    "estimatedReadingMinutes": 1,
    "publishedAt": 1,
}


@dataclass(frozen=True)
class Confidence:
    level: ConfidenceLevel
    uncertainty: str | None


def _plain(value: Any) -> str:
    """Valor textual de un enum o string leído de MongoDB."""
    return str(getattr(value, "value", value))


def verification_status(document: dict[str, Any]) -> str:
    verification = document.get("verification") or {}
    return _plain(verification.get("status") or VerificationStatus.developing.value)


def verification_label(document: dict[str, Any]) -> str:
    status = verification_status(document)
    return VERIFICATION_LABELS.get(status, status)


async def find_published_news(database, news_id: ObjectId) -> dict[str, Any] | None:
    return await database["news"].find_one({"_id": news_id, "status": "published"}, NEWS_PROJECTION)


async def find_published_news_by_ids(database, news_ids: list[ObjectId]) -> list[dict[str, Any]]:
    if not news_ids:
        return []
    documents = await (
        database["news"]
        .find({"_id": {"$in": news_ids}, "status": "published"}, NEWS_PROJECTION)
        .to_list(length=len(news_ids))
    )
    order = {news_id: index for index, news_id in enumerate(news_ids)}
    return sorted(documents, key=lambda document: order.get(document["_id"], len(order)))


async def recent_published_news(database) -> list[dict[str, Any]]:
    return await (
        database["news"]
        .find({"status": "published"}, NEWS_PROJECTION)
        .sort("publishedAt", -1)
        .limit(RECENT_NEWS_WINDOW)
        .to_list(length=RECENT_NEWS_WINDOW)
    )


def news_filters(query: ClassifiedQuery, location_ids: set[ObjectId]) -> dict[str, Any]:
    """Filtros estructurados del catálogo, sin ejecutar instrucciones del usuario."""
    filters: dict[str, Any] = {}
    if query.country_codes or query.wants_user_location:
        filters["geographicScope.locationIds"] = {"$in": list(location_ids)}
    if query.topics:
        filters["topics"] = {"$in": list(query.topics)}
    return filters


async def count_news(database, filters: dict[str, Any] | None = None) -> dict[str, int]:
    """Cuenta toda la selección en MongoDB, sin aplicar límites del listado."""
    filters = filters or {}
    return {
        "total": await database["news"].count_documents(filters),
        "published": await database["news"].count_documents({**filters, "status": "published"}),
        "draft": await database["news"].count_documents({**filters, "status": "draft"}),
    }


async def published_news_matching(
    database, filters: dict[str, Any], *, limit: int = LISTING_LIMIT
) -> list[dict[str, Any]]:
    return await (
        database["news"]
        .find({**filters, "status": "published"}, NEWS_PROJECTION)
        .sort("publishedAt", -1)
        .limit(limit)
        .to_list(length=limit)
    )


async def resolve_news_locations(database, documents: list[dict[str, Any]]) -> dict[ObjectId, dict]:
    ids = {
        ref
        for document in documents
        for ref in (document.get("geographicScope") or {}).get("locationIds") or []
    }
    if not ids:
        return {}
    locations = (
        await database["locations"]
        .find(
            {"_id": {"$in": list(ids)}},
            {"name": 1, "country": 1, "countryCode": 1, "region": 1, "city": 1},
        )
        .to_list(length=None)
    )
    return {location["_id"]: location for location in locations}


def _searchable_text(document: dict[str, Any]) -> str:
    parts = [
        str(document.get("title") or ""),
        str(document.get("summary") or ""),
        " ".join(str(item) for item in document.get("topics") or []),
        " ".join(str(item) for item in document.get("keywords") or []),
    ]
    return f" {normalize_text(' '.join(parts))} "


def _matches_location(document: dict[str, Any], location_ids: set[ObjectId]) -> bool:
    scope = document.get("geographicScope") or {}
    return any(location_id in location_ids for location_id in scope.get("locationIds") or [])


def _matches_topic(document: dict[str, Any], topics: tuple[str, ...]) -> bool:
    document_topics = {normalize_text(str(topic)) for topic in document.get("topics") or []}
    return any(normalize_text(topic) in document_topics for topic in topics)


def _term_score(document: dict[str, Any], terms: tuple[str, ...]) -> int:
    searchable = _searchable_text(document)
    return sum(1 for term in terms if f" {term}" in searchable)


def select_news(
    news: list[dict[str, Any]],
    query: ClassifiedQuery,
    location_ids: set[ObjectId],
    *,
    use_terms: bool,
) -> list[dict[str, Any]]:
    """Filtra la ventana reciente según ubicación, tema y términos.

    Ubicación y tema se combinan con AND. Los términos solo ordenan y filtran
    cuando `use_terms` es verdadero y no hay otro filtro, para no exigir que una
    consulta regional repita palabras exactas del título.
    """
    selected = news
    if query.country_codes or query.wants_user_location:
        selected = [document for document in selected if _matches_location(document, location_ids)]
    if query.topics:
        selected = [document for document in selected if _matches_topic(document, query.topics)]
    if use_terms and query.terms and not query.has_filters:
        scored = [(document, _term_score(document, query.terms)) for document in selected]
        scored = [item for item in scored if item[1] > 0]
        # sorted es estable: a igual puntaje se conserva el orden por fecha.
        selected = [document for document, _score in sorted(scored, key=lambda item: -item[1])]
    return selected


def compute_confidence(cited: list[dict[str, Any]]) -> Confidence:
    """Nivel de confianza basado en verificación y fuentes de las noticias citadas.

    - low: no hay noticias citadas o alguna no está confirmada.
    - high: todas confirmadas y cada una tiene dos o más fuentes, o al menos una
      fuente oficial o primaria.
    - medium: todas confirmadas pero alguna se apoya en una sola fuente secundaria
      o en ninguna.
    """
    if not cited:
        return Confidence(
            ConfidenceLevel.low,
            "No hay noticias publicadas en la base que respalden esta respuesta.",
        )

    unconfirmed = [
        document
        for document in cited
        if verification_status(document) != VerificationStatus.confirmed.value
    ]
    if unconfirmed:
        details = "; ".join(
            f"«{document.get('title')}» ({verification_label(document).lower()})"
            for document in unconfirmed
        )
        return Confidence(
            ConfidenceLevel.low,
            f"Hay noticias citadas que no están confirmadas: {details}.",
        )

    def well_sourced(document: dict[str, Any]) -> bool:
        sources = document.get("sources") or []
        return len(sources) >= 2 or any(
            _plain(source.get("sourceType")) in STRONG_SOURCE_TYPES for source in sources
        )

    if all(well_sourced(document) for document in cited):
        return Confidence(ConfidenceLevel.high, None)
    return Confidence(
        ConfidenceLevel.medium,
        "Algunas noticias citadas se apoyan en una sola fuente secundaria o no declaran fuentes.",
    )


def _format_date(value: datetime | None) -> str:
    if value is None:
        return "sin fecha"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.strftime("%d/%m/%Y")


def _status_note(document: dict[str, Any]) -> str:
    if verification_status(document) == VerificationStatus.confirmed.value:
        return ""
    return f" [{verification_label(document)}]"


def format_listing(intro: str, documents: list[dict[str, Any]]) -> str:
    lines = [intro, ""]
    for index, document in enumerate(documents, start=1):
        lines.append(
            f"{index}. {document.get('title')}{_status_note(document)} — "
            f"{_format_date(document.get('publishedAt'))}"
        )
        lines.append(f"   {document.get('summary')}")
    return "\n".join(lines)


def format_detail(document: dict[str, Any]) -> str:
    sources = document.get("sources") or []
    source_names = (
        ", ".join(str(source.get("name")) for source in sources) or "sin fuentes declaradas"
    )
    return "\n".join(
        [
            str(document.get("title")),
            "",
            str(document.get("summary")),
            "",
            f"Verificación: {verification_label(document)}",
            f"Fuentes: {source_names}",
            (
                f"Publicada: {_format_date(document.get('publishedAt'))} · "
                f"{int(document.get('estimatedReadingMinutes') or 1)} min de lectura"
            ),
        ]
    )


def news_context(
    documents: list[dict[str, Any]],
    *,
    include_content: bool,
    locations: dict[ObjectId, dict] | None = None,
) -> list[dict[str, Any]]:
    """Proyección de noticias que se entrega al modelo como datos."""
    context = []
    locations = locations or {}
    for document in documents:
        scope = document.get("geographicScope") or {}
        location_ids = scope.get("locationIds") or []
        item: dict[str, Any] = {
            "id": str(document["_id"]),
            "title": document.get("title"),
            "summary": document.get("summary"),
            "topics": document.get("topics") or [],
            "geographicScope": {
                "level": _plain(scope["level"]) if scope.get("level") else None,
                "locationIds": [str(ref) for ref in location_ids],
                "locations": [
                    {
                        "id": str(ref),
                        **{
                            key: locations[ref].get(key)
                            for key in ("name", "country", "countryCode", "region", "city")
                        },
                    }
                    for ref in location_ids
                    if ref in locations
                ],
                "unresolvedLocationIds": [str(ref) for ref in location_ids if ref not in locations],
            },
            "verificationStatus": verification_status(document),
            "sources": [
                {"name": source.get("name"), "sourceType": _plain(source.get("sourceType"))}
                for source in document.get("sources") or []
            ],
            "publishedAt": _format_date(document.get("publishedAt")),
        }
        if include_content:
            content = str(document.get("content") or "")
            item["content"] = content[:CONTENT_MAX_CHARS]
            item["contentTruncated"] = len(content) > CONTENT_MAX_CHARS
        context.append(item)
    return context

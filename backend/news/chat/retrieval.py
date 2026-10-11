"""Lectura de noticias publicadas para el chat y cálculo del nivel de confianza.

Solo se leen noticias con `status = "published"`: son las únicas que pueden
citarse en `citedNewsIds`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from ..models import ConfidenceLevel, VerificationStatus
from .intent import ClassifiedQuery, normalize_text

# Ventana de noticias recientes sobre la que se filtra en memoria.
RECENT_NEWS_WINDOW = 200
LISTING_LIMIT = 5
LLM_CONTEXT_LIMIT = 3
LLM_CONTENT_MAX_CHARS = 4000

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


def find_published_news(database, news_id: ObjectId) -> dict[str, Any] | None:
    return database["news"].find_one({"_id": news_id, "status": "published"}, NEWS_PROJECTION)


def recent_published_news(database) -> list[dict[str, Any]]:
    cursor = (
        database["news"]
        .find({"status": "published"}, NEWS_PROJECTION)
        .sort("publishedAt", -1)
        .limit(RECENT_NEWS_WINDOW)
    )
    return list(cursor)


def location_ids_for_codes(database, country_codes: tuple[str, ...]) -> set[ObjectId]:
    if not country_codes:
        return set()
    cursor = database["locations"].find(
        {"countryCode": {"$in": list(country_codes)}, "active": True},
        {"_id": 1},
    )
    return {document["_id"] for document in cursor}


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
    return any(topic in document_topics for topic in topics)


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
        value = value.replace(tzinfo=timezone.utc)
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
    source_names = ", ".join(str(source.get("name")) for source in sources) or "sin fuentes declaradas"
    return "\n".join(
        [
            str(document.get("title")),
            "",
            str(document.get("summary")),
            "",
            f"Verificación: {verification_label(document)}",
            f"Fuentes: {source_names}",
            f"Publicada: {_format_date(document.get('publishedAt'))} · "
            f"{int(document.get('estimatedReadingMinutes') or 1)} min de lectura",
        ]
    )


def llm_context(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Proyección de noticias que se entrega al modelo como datos."""
    context = []
    for document in documents[:LLM_CONTEXT_LIMIT]:
        content = str(document.get("content") or "")
        context.append(
            {
                "id": str(document["_id"]),
                "title": document.get("title"),
                "summary": document.get("summary"),
                "content": content[:LLM_CONTENT_MAX_CHARS],
                "contentTruncated": len(content) > LLM_CONTENT_MAX_CHARS,
                "verificationStatus": verification_status(document),
                "sources": [
                    {"name": source.get("name"), "sourceType": _plain(source.get("sourceType"))}
                    for source in document.get("sources") or []
                ],
                "publishedAt": _format_date(document.get("publishedAt")),
            }
        )
    return context

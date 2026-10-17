"""Clasificación de alcance y routing determinista del turno conversacional."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum

from news.models import ResponseIntent

from .capabilities import CAPABILITIES, CAPABILITY_CATALOG, Capability
from .intent import ClassifiedQuery, normalize_text


class Scope(StrEnum):
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    PARTIAL = "PARTIAL"
    BUSINESS = "BUSINESS"


@dataclass(frozen=True)
class BusinessContext:
    """Datos disponibles que condicionan la interpretación del turno."""

    has_news_context: bool = False


@dataclass(frozen=True)
class TurnState:
    """Estado interno del turno; no se persiste en MongoDB."""

    original_message: str
    business_message: str
    query: ClassifiedQuery
    scope: Scope
    capability: Capability | None
    scope_note: str | None = None


_OUT_OF_SCOPE_PATTERNS = (
    re.compile(r"\b(?:haz|realiza|inicia|ejecuta|ordena)\s+(?:una\s+)?transferencia\b"),
    re.compile(r"\btransfiere(?:me)?\b|\btransferir\s+dinero\b"),
    re.compile(
        r"\b(?:haz|realiza|procesa)\s+(?:un\s+)?pago\b|"
        r"\bpaga\s+(?:la|el|mi|mis|una|un)\s+\w+"
    ),
    re.compile(r"\breceta\b|\b(?:cocina|cocinar|prepara)\s+(?:una\s+)?receta\b"),
    re.compile(r"\b(?:pronostico del tiempo|que tiempo hace|clima en)\b"),
    re.compile(
        r"\b(?:dame|necesito|recomiendame)\s+(?:un\s+)?(?:diagnostico|tratamiento)\b|"
        r"\bque dosis\s+(?:debo|puedo|tengo)\b"
    ),
)
_CONNECTORS = re.compile(r"\b(?:y|tambien|ademas|pero)\b", re.IGNORECASE)

_CAPABILITY_BY_INTENT = {
    item.intent: item
    for item in CAPABILITY_CATALOG
    if item.intent is not None and item.key != "news.group_by_country"
}


def _matches_out_of_scope(segment: str) -> bool:
    normalized = normalize_text(segment)
    return any(pattern.search(normalized) for pattern in _OUT_OF_SCOPE_PATTERNS)


def _has_business_signal(query: ClassifiedQuery, context: BusinessContext) -> bool:
    return bool(
        context.has_news_context
        or query.intent is not None
        or query.has_filters
        or query.group_by_country
        or query.wants_count
    )


def _segments(message: str) -> list[str]:
    return [part.strip(" ,;:.") for part in _CONNECTORS.split(message) if part.strip(" ,;:.")]


def _select_capability(query: ClassifiedQuery) -> Capability | None:
    if query.intent == ResponseIntent.unsupported:
        return None
    if query.group_by_country:
        return CAPABILITIES["news.group_by_country"]
    if query.wants_count:
        return CAPABILITIES["news.count"]
    if query.intent is not None:
        capability = _CAPABILITY_BY_INTENT.get(query.intent)
        if capability is not None:
            return capability
    if query.use_previous_citations:
        return CAPABILITIES["news.explain"]
    if query.terms:
        return CAPABILITIES["news.search"]
    return None


def resolve_turn(
    message: str,
    query: ClassifiedQuery,
    *,
    has_news_context: bool = False,
) -> TurnState:
    """Clasifica alcance, separa fragmentos ajenos y resuelve catálogo cerrado."""
    context = BusinessContext(has_news_context=has_news_context)
    all_segments = _segments(message)
    outside_segments = [segment for segment in all_segments if _matches_out_of_scope(segment)]
    business_segments = [segment for segment in all_segments if segment not in outside_segments]

    has_business = _has_business_signal(query, context)
    if not has_business:
        has_business = any(
            bool(query.terms) and not _matches_out_of_scope(segment)
            for segment in business_segments
        )

    if outside_segments and business_segments and has_business:
        business_message = " y ".join(business_segments).strip()
        outside_terms = {
            word for segment in outside_segments for word in normalize_text(segment).split()
        }
        query = replace(
            query, terms=tuple(term for term in query.terms if term not in outside_terms)
        )
        scope = Scope.PARTIAL
        scope_note = (
            "Puedo atender la parte relacionada con noticias; no puedo realizar acciones "
            "externas a la aplicación."
        )
    elif outside_segments or not (has_business or query.terms or query.use_previous_citations):
        business_message = ""
        scope = Scope.OUT_OF_SCOPE
        scope_note = None
    else:
        business_message = message
        scope = Scope.BUSINESS
        scope_note = None

    capability = _select_capability(query) if scope != Scope.OUT_OF_SCOPE else None
    if scope != Scope.OUT_OF_SCOPE and capability is None:
        scope = Scope.OUT_OF_SCOPE

    return TurnState(
        original_message=message,
        business_message=business_message,
        query=query,
        scope=scope,
        capability=capability,
        scope_note=scope_note,
    )

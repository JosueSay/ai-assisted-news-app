"""Resuelve seguimientos a partir de los mensajes de la sesión vigente.

El estado se reconstruye en memoria; no añade campos al esquema de chatSessions.
"""

import re
from dataclasses import replace
from typing import Any

from news.models import ResponseIntent

from .intent import ClassifiedQuery, classify_message, normalize_text

ELABORATIONS = {ResponseIntent.summarize, ResponseIntent.explain, ResponseIntent.news_detail}
ACKNOWLEDGMENTS = {"si", "ok", "okay", "hazlo", "dale", "adelante", "vale", "procede"}
ACK_WORDS = ACKNOWLEDGMENTS | {
    "claro",
    "por",
    "favor",
    "esta",
    "bien",
    "de",
    "acuerdo",
    "bueno",
    "perfecto",
}
ORDINALS = {
    "primera": 0,
    "primero": 0,
    "segunda": 1,
    "segundo": 1,
    "tercera": 2,
    "tercero": 2,
    "cuarta": 3,
    "cuarto": 3,
    "quinta": 4,
    "quinto": 4,
}


def _resolve(
    message: str, previous: ClassifiedQuery | None, *, has_news_context: bool
) -> ClassifiedQuery:
    query = classify_message(message, has_news_context=has_news_context)
    if previous is None:
        return query
    text = normalize_text(message)
    words = set(text.split())
    affirmative = bool(words & ACKNOWLEDGMENTS) and words <= ACK_WORDS
    ordinal = next((index for word, index in ORDINALS.items() if word in words), None)
    country_reference = bool(re.search(r"\bde que pais(?:es)?\b", text))
    reference = country_reference or (
        query.intent in ELABORATIONS
        and not query.has_filters
        and (
            ordinal is not None
            or not query.terms
            or bool(
                words
                & {
                    "esas",
                    "esos",
                    "esa",
                    "ese",
                    "esto",
                    "eso",
                    "estas",
                    "estos",
                    "resumelas",
                    "resumela",
                    "explicala",
                    "explicalas",
                }
            )
        )
    )
    short_count = bool(words & {"cuantas", "cuantos"}) and not words & {"noticias", "articulos"}
    connector = text.startswith(("y ", "tambien ", "ahora ", "en cambio "))
    global_request = any(
        phrase in text for phrase in ("base de datos", "en total", "todo el mundo")
    )
    followup = not global_request and (
        affirmative
        or reference
        or short_count
        or connector
        and (query.has_filters or query.group_by_country)
        or query.wants_count
        and not query.has_filters
    )
    if not followup:
        return query

    generic_group = (
        query.group_by_country and not query.country_codes and not query.wants_user_location
    )
    countries = query.country_codes or (
        previous.country_codes if not query.wants_user_location and not generic_group else ()
    )
    topics = query.topics or previous.topics
    user_location = query.wants_user_location or (
        previous.wants_user_location and not query.country_codes and not generic_group
    )
    wants_count = (
        query.wants_count
        or short_count
        or (previous.wants_count and query.intent not in ELABORATIONS and not affirmative)
    )
    group = query.group_by_country
    use_citations = (reference or affirmative) and not query.has_filters and not wants_count
    if use_citations:
        intent = query.intent if query.intent in ELABORATIONS else ResponseIntent.explain
    else:
        intent = (
            ResponseIntent.regional_news
            if countries or user_location or group
            else ResponseIntent.topic_news
            if topics
            else ResponseIntent.recent_news
        )
    return replace(
        query,
        intent=intent,
        country_codes=countries,
        topics=topics,
        wants_user_location=user_location,
        wants_count=wants_count,
        group_by_country=group,
        use_previous_citations=use_citations,
        citation_index=ordinal if use_citations else None,
    )


def resolve_message(
    message: str, messages: list[dict[str, Any]], *, has_news_context: bool
) -> ClassifiedQuery:
    previous = None
    before_turn = None
    for stored in messages:
        if stored.get("role") == "user":
            before_turn = previous
            previous = _resolve(stored["content"], previous, has_news_context=False)
        elif stored.get("role") == "assistant":
            intent = (stored.get("responseMetadata") or {}).get("intent")
            if intent == ResponseIntent.unsupported:
                previous = before_turn
            elif previous is not None and intent is not None:
                previous = replace(previous, intent=ResponseIntent(intent))
    return _resolve(message, previous, has_news_context=has_news_context)

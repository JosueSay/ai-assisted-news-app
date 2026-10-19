"""Contratos del catálogo y routing interno del modo news."""

from dataclasses import replace

import pytest
from news.models import ResponseIntent

from assistant.news_chat.capabilities import (
    CAPABILITY_CATALOG,
    ExecutionMode,
    validate_capability_catalog,
)
from assistant.news_chat.intent import classify_message
from assistant.news_chat.routing import Scope, resolve_turn


def route(message: str, *, has_news_context: bool = False):
    query = classify_message(message, has_news_context=has_news_context)
    return resolve_turn(message, query, has_news_context=has_news_context)


def test_capability_catalog_is_complete_and_references_registered_handlers():
    assert validate_capability_catalog() == ()
    assert len({item.key for item in CAPABILITY_CATALOG}) == len(CAPABILITY_CATALOG)
    assert {item.key for item in CAPABILITY_CATALOG} >= {
        "news.list_recent",
        "news.list_by_country",
        "news.list_by_topic",
        "news.detail",
        "news.count",
        "news.group_by_country",
        "news.summarize",
        "news.explain",
    }


@pytest.mark.parametrize(
    ("message", "capability", "execution"),
    [
        ("noticias recientes", "news.list_recent", ExecutionMode.CODE),
        ("noticias de México", "news.list_by_country", ExecutionMode.CODE),
        ("noticias de tecnología", "news.list_by_topic", ExecutionMode.CODE),
        ("dame más detalle sobre México", "news.detail", ExecutionMode.CODE),
        ("¿cuántas noticias hay?", "news.count", ExecutionMode.CODE),
        ("¿qué noticias tienes por país?", "news.group_by_country", ExecutionMode.CODE),
        ("¿de qué países son?", "news.group_by_country", ExecutionMode.CODE),
        ("resume las noticias de México", "news.summarize", ExecutionMode.LLM),
        ("explica las noticias de México", "news.explain", ExecutionMode.LLM),
    ],
)
def test_capability_selection_uses_the_explicit_execution_matrix(message, capability, execution):
    result = route(message)

    assert result.scope == Scope.BUSINESS
    assert result.capability.key == capability
    assert result.capability.execution == execution


def test_article_detail_context_routes_to_explanation_capability():
    result = route("¿qué significa esto?", has_news_context=True)

    assert result.capability.key == "news.explain"
    assert result.capability.intent == ResponseIntent.explain


def test_explicitly_unsupported_request_routes_without_a_capability():
    result = route("Haz una transferencia")

    assert result.scope == Scope.OUT_OF_SCOPE
    assert result.capability is None


def test_mixed_request_keeps_only_news_text_for_execution_and_marks_partial_scope():
    result = route("Noticias de México y haz una transferencia")

    assert result.scope == Scope.PARTIAL
    assert result.business_message == "Noticias de México"
    assert result.capability.key == "news.list_by_country"
    assert result.scope_note


def test_ambiguous_free_text_uses_registered_safe_search_capability():
    result = route("algo sobre lo digital")

    assert result.scope == Scope.BUSINESS
    assert result.capability.key == "news.search"
    assert result.capability.execution == ExecutionMode.CODE


def test_greeting_without_news_action_falls_back_without_capability():
    result = route("hola")

    assert result.scope == Scope.OUT_OF_SCOPE
    assert result.capability is None


def test_unsupported_intent_cannot_fall_through_to_free_text_search():
    query = classify_message("receta de pastel", has_news_context=False)
    query = replace(query, intent=ResponseIntent.unsupported, terms=("pastel",))

    result = resolve_turn("receta de pastel", query)

    assert result.scope == Scope.OUT_OF_SCOPE
    assert result.capability is None

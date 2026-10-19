"""Catálogo cerrado de capacidades y matriz de ejecución del chat de noticias.

Los identificadores son contratos internos versionados en código; no se ejecutan
recursos ni presentaciones proporcionados por el usuario o por un modelo.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from news.models import ResponseIntent


class ExecutionMode(StrEnum):
    CODE = "CODE"
    LLM = "LLM"


@dataclass(frozen=True)
class Capability:
    key: str
    intent: ResponseIntent | None
    execution: ExecutionMode
    resource: str
    presentation: str


CAPABILITY_CATALOG = (
    Capability(
        "news.list_recent",
        ResponseIntent.recent_news,
        ExecutionMode.CODE,
        "recent_published_news",
        "listing",
    ),
    Capability(
        "news.list_by_country",
        ResponseIntent.regional_news,
        ExecutionMode.CODE,
        "published_news_matching",
        "listing",
    ),
    Capability(
        "news.list_by_topic",
        ResponseIntent.topic_news,
        ExecutionMode.CODE,
        "published_news_matching",
        "listing",
    ),
    Capability(
        "news.search",
        None,
        ExecutionMode.CODE,
        "search_published_news",
        "search",
    ),
    Capability(
        "news.detail",
        ResponseIntent.news_detail,
        ExecutionMode.CODE,
        "find_published_news",
        "detail",
    ),
    Capability(
        "news.count",
        None,
        ExecutionMode.CODE,
        "count_news",
        "count",
    ),
    Capability(
        "news.group_by_country",
        ResponseIntent.regional_news,
        ExecutionMode.CODE,
        "group_news_by_country",
        "country_groups",
    ),
    Capability(
        "news.summarize",
        ResponseIntent.summarize,
        ExecutionMode.LLM,
        "published_news_context",
        "summary",
    ),
    Capability(
        "news.explain",
        ResponseIntent.explain,
        ExecutionMode.LLM,
        "published_news_context",
        "explanation",
    ),
)

CAPABILITIES = MappingProxyType({item.key: item for item in CAPABILITY_CATALOG})

REGISTERED_RESOURCES = frozenset(
    {
        "recent_published_news",
        "published_news_matching",
        "search_published_news",
        "find_published_news",
        "count_news",
        "group_news_by_country",
        "published_news_context",
    }
)
REGISTERED_PRESENTATIONS = frozenset(
    {"listing", "search", "detail", "count", "country_groups", "summary", "explanation"}
)


def validate_capability_catalog() -> tuple[str, ...]:
    """Devuelve problemas del catálogo antes de admitirlo en el flujo del chat."""
    errors: list[str] = []
    keys = [item.key for item in CAPABILITY_CATALOG]
    if len(keys) != len(set(keys)):
        errors.append("capability keys must be unique")
    for item in CAPABILITY_CATALOG:
        if item.resource not in REGISTERED_RESOURCES:
            errors.append(f"{item.key}: unknown resource {item.resource}")
        if item.presentation not in REGISTERED_PRESENTATIONS:
            errors.append(f"{item.key}: unknown presentation {item.presentation}")
        if item.execution not in ExecutionMode:
            errors.append(f"{item.key}: unknown execution mode {item.execution}")
        if item.execution == ExecutionMode.LLM and item.intent not in {
            ResponseIntent.summarize,
            ResponseIntent.explain,
        }:
            errors.append(f"{item.key}: LLM execution is reserved for summary and explanation")
        if item.execution == ExecutionMode.CODE and item.intent in {
            ResponseIntent.summarize,
            ResponseIntent.explain,
        }:
            errors.append(f"{item.key}: summary and explanation must use LLM execution")
    return tuple(errors)

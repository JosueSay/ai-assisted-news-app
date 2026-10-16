"""Consultas del chat contra el dataset aprobado, sin keys ni llamadas a IA."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from bson import ObjectId
from news.demo_news import get_demo_news_documents
from news.models import ResponseIntent, ResponseStrategy
from news.models.chat_session import ChatSession
from news.seed_catalog import CATALOG_LOCATION_IDS, CATALOG_LOCATIONS, catalog_location_document
from news.seed_demo import DEMO_NEWS, _demo_news_document

from assistant.config import get_settings
from assistant.news_chat.intent import classify_message
from assistant.news_chat.schemas import ChatRequest
from assistant.news_chat.service import NewsChatService
from assistant.tests.news_fakes import FakeDatabase, FakeProvider

NOW = datetime(2026, 10, 15, 18, tzinfo=UTC)


@pytest.fixture
def database():
    db = FakeDatabase()
    db["locations"].documents.extend(catalog_location_document(c) for c in CATALOG_LOCATIONS)
    db["news"].documents.extend(get_demo_news_documents())
    db["news"].documents.extend(_demo_news_document(item) for item in DEMO_NEWS)
    return db


@pytest.fixture
def settings():
    return replace(
        get_settings(),
        provider="openai",
        api_key="fixture-only",
        mongodb_context_mode="news",
        prompt_file=Path(__file__).resolve().parents[1] / "prompts/news.md",
        input_usd_per_million=1.0,
        output_usd_per_million=4.0,
    )


def request(message, **kwargs):
    return ChatRequest(
        message=message,
        user={"id": "guest:db-queries", "displayName": "Fixture"},
        **kwargs,
    )


def service(database, settings, provider):
    return NewsChatService(settings, lambda: provider, database, clock=lambda: NOW)


@pytest.mark.parametrize(
    "message",
    ["que noticias tienes por pais", "¿Qué noticias hay por países?", "noticias de cada país"],
)
def test_country_overview_is_a_regional_request(message):
    query = classify_message(message, has_news_context=False)
    assert query.intent == ResponseIntent.regional_news
    assert query.group_by_country is True
    assert query.country_codes == ()
    assert query.wants_user_location is False


@pytest.mark.parametrize(
    "message",
    [
        "dame la cantidad de noticias que tienes tu en tu base de datos de este ai news",
        "¿Cuántas noticias hay?",
        "Dime el total de noticias",
        "Número de noticias de Guatemala",
    ],
)
def test_news_count_is_recognized(message):
    query = classify_message(message, has_news_context=False)
    assert query.wants_count is True


async def test_count_reads_the_database_instead_of_the_five_citations(database, settings):
    provider = FakeProvider("Respuesta incorrecta: solo hay cinco.")
    before = deepcopy(database["news"].documents)
    reply = await service(database, settings, provider).reply(
        request("dame la cantidad de noticias que tienes tu en tu base de datos de este ai news")
    )
    assert "37 noticias" in reply.message.content
    assert "33 publicadas" in reply.message.content
    assert "4 borradores" in reply.message.content
    assert reply.message.strategy == ResponseStrategy.database_query
    assert reply.message.aiUsed is False
    assert provider.calls == []
    assert database["aiUsage"].documents == []
    assert database["news"].documents == before
    published_ids = {str(d["_id"]) for d in before if d["status"] == "published"}
    assert {c.id for c in reply.message.citedNews} <= published_ids
    ChatSession.model_validate(database["chatSessions"].documents[0])


async def test_count_is_not_limited_to_the_recent_window(database, settings):
    original = database["news"].documents[0]
    for index in range(205):
        document = deepcopy(original)
        document.update(_id=ObjectId(), slug=f"extra-{index}")
        database["news"].documents.append(document)
    reply = await service(database, settings, FakeProvider()).reply(request("cuántas noticias hay"))
    assert "242 noticias" in reply.message.content
    assert "238 publicadas" in reply.message.content
    assert "4 borradores" in reply.message.content


async def test_count_honors_country_and_topic_filters(database, settings):
    gt = CATALOG_LOCATION_IDS["GT"]
    docs = [
        d
        for d in database["news"].documents
        if gt in d["geographicScope"]["locationIds"] and "tecnologia" in d["topics"]
    ]
    reply = await service(database, settings, FakeProvider()).reply(
        request("Cuántas noticias de tecnología tienes de Guatemala")
    )
    assert f"{len(docs)} noticias" in reply.message.content
    assert "Guatemala" in reply.message.content
    assert "Tecnología" in reply.message.content
    assert reply.message.strategy == ResponseStrategy.database_query


async def test_country_overview_covers_the_catalog_despite_five_newer_legacy_articles(
    database, settings
):
    provider = FakeProvider("No puedo listar por país.")
    reply = await service(database, settings, provider).reply(
        request("que noticias tienes por pais")
    )
    published = [d for d in database["news"].documents if d["status"] == "published"]
    by_id = {str(d["_id"]): d for d in published}
    expected_locations = {ref for d in published for ref in d["geographicScope"]["locationIds"]}
    cited_locations = {
        ref
        for cited in reply.message.citedNews
        for ref in by_id[cited.id]["geographicScope"]["locationIds"]
    }
    assert cited_locations == expected_locations
    for location in database["locations"].documents:
        if location["_id"] in expected_locations:
            assert location["country"] in reply.message.content
    assert "33 noticias publicadas" in reply.message.content
    assert reply.message.intent == ResponseIntent.regional_news
    assert reply.message.strategy == ResponseStrategy.database_query
    assert provider.calls == []
    assert database["aiUsage"].documents == []


async def test_count_by_country_honors_topic_and_never_cites_drafts(database, settings):
    provider = FakeProvider()
    reply = await service(database, settings, provider).reply(
        request("Cuántas noticias de tecnología tienes por país")
    )
    expected = [
        d
        for d in database["news"].documents
        if d["status"] == "published" and "tecnologia" in d["topics"]
    ]
    by_id = {str(d["_id"]): d for d in expected}
    assert {c.id for c in reply.message.citedNews} <= set(by_id)
    assert len(reply.message.citedNews) > 0
    assert "Tecnología" in reply.message.content
    assert f"{len(expected)} noticias publicadas" in reply.message.content
    assert provider.calls == []


async def test_llm_receives_real_inventory_and_resolved_countries(database, settings):
    provider = FakeProvider()
    await service(database, settings, provider).reply(request("Noticias de México"))
    context = provider.calls[0]["context"]
    assert context["inventario"] == {"total": 37, "published": 33, "draft": 4}
    assert context["seleccion"]["mostradas"] == len(context["noticias"])
    for article in context["noticias"]:
        scope = article["geographicScope"]
        assert scope["locations"][0]["countryCode"] == "MX"
        assert scope["locations"][0]["country"] == "México"
        assert article["topics"]


async def test_unresolved_location_is_explicit_instead_of_using_the_user_country(
    database, settings
):
    document = database["news"].documents[0]
    missing = ObjectId()
    document["geographicScope"]["locationIds"] = [missing]
    provider = FakeProvider()
    await service(database, settings, provider).reply(
        request("Dame más detalle", newsId=str(document["_id"]))
    )
    scope = provider.calls[0]["context"]["noticias"][0]["geographicScope"]
    assert scope["locationIds"] == [str(missing)]
    assert scope["locations"] == []
    assert scope["unresolvedLocationIds"] == [str(missing)]


async def test_counts_are_recomputed_after_new_documents(database, settings):
    provider = FakeProvider()
    chat = service(database, settings, provider)
    first = await chat.reply(request("Cuántas noticias hay"))
    database["news"].documents.append(
        {**database["news"].documents[0], "_id": ObjectId(), "slug": "new-publication"}
    )
    second = await chat.reply(request("Cuántas noticias hay", sessionId=first.sessionId))
    assert "37 noticias" in first.message.content
    assert "38 noticias" in second.message.content
    assert "34 publicadas" in second.message.content
    assert provider.calls == []


async def test_zero_published_news_reports_counts_without_exposing_draft_content(
    database, settings
):
    database["news"].documents[:] = [
        d for d in database["news"].documents if d["status"] == "draft"
    ]
    provider = FakeProvider()
    reply = await service(database, settings, provider).reply(request("Cuántas noticias hay"))
    assert "4 noticias" in reply.message.content
    assert "0 publicadas" in reply.message.content
    assert "4 borradores" in reply.message.content
    assert reply.message.citedNews == []
    assert provider.calls == []
    for draft in database["news"].documents:
        assert draft["title"] not in reply.message.content


async def test_location_selection_applies_to_counts(database, settings):
    mx = CATALOG_LOCATION_IDS["MX"]
    expected = [d for d in database["news"].documents if mx in d["geographicScope"]["locationIds"]]
    reply = await service(database, settings, FakeProvider()).reply(
        request("Cuántas noticias hay de mi país", locationId=str(mx))
    )
    assert f"{len(expected)} noticias" in reply.message.content
    assert "México" in reply.message.content


async def test_named_country_search_can_find_news_older_than_the_recent_window(database, settings):
    for index in range(205):
        document = deepcopy(database["news"].documents[0])
        document.update(_id=ObjectId(), slug=f"newer-{index}", publishedAt=NOW)
        database["news"].documents.append(document)
    provider = FakeProvider()
    reply = await service(database, settings, provider).reply(request("Noticias de México"))
    assert reply.message.citedNews
    for article in provider.calls[0]["context"]["noticias"]:
        assert article["geographicScope"]["locations"][0]["countryCode"] == "MX"


async def test_country_overview_can_be_requested_while_an_article_is_open(database, settings):
    provider = FakeProvider()
    reply = await service(database, settings, provider).reply(
        request("Qué noticias tienes por país", newsId=str(database["news"].documents[0]["_id"]))
    )
    assert reply.message.intent == ResponseIntent.regional_news
    assert "Guatemala" in reply.message.content
    assert "México" in reply.message.content
    assert provider.calls == []


async def test_llm_knows_five_recent_examples_are_a_partial_selection(database, settings):
    provider = FakeProvider()
    await service(database, settings, provider).reply(request("noticias recientes"))
    context = provider.calls[0]["context"]
    assert len(context["noticias"]) == 5
    assert context["seleccion"] == {
        "mostradas": 5,
        "coincidenciasPublicadas": 33,
        "esMuestra": True,
    }
    assert context["inventario"]["total"] == 37
    assert {
        loc["countryCode"]
        for article in context["noticias"]
        for loc in article["geographicScope"]["locations"]
    } == {"GT"}

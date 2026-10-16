"""Seguimientos de la misma sesión, sin usar historial real ni credenciales."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from news.models import ResponseIntent, ResponseStrategy

from assistant.config import get_settings
from assistant.news_chat.schemas import ChatRequest
from assistant.news_chat.service import NewsChatService
from assistant.tests.news_fakes import FakeDatabase, FakeProvider
from assistant.tests.test_news_chat import MX, NOW, make_news


@pytest.fixture
def database():
    from news.seed_catalog import CATALOG_LOCATIONS, catalog_location_document

    db = FakeDatabase()
    db["locations"].documents.extend(catalog_location_document(c) for c in CATALOG_LOCATIONS)
    db["news"].documents.extend(
        [
            make_news("gt-tech", "Sensores de Guatemala", topic="tecnologia", days_ago=0),
            make_news(
                "mx-tech", "Sensores de México", topic="tecnologia", location_id=MX, days_ago=3
            ),
            make_news("mx-sports", "Liga de México", topic="deportes", location_id=MX, days_ago=2),
            make_news("gt-sports", "Liga de Guatemala", topic="deportes", days_ago=1),
        ]
    )
    return db


@pytest.fixture
def settings():
    return replace(
        get_settings(),
        provider="stub",
        mongodb_context_mode="news",
        prompt_file=Path(__file__).resolve().parents[1] / "prompts/news.md",
        input_usd_per_million=1.0,
        output_usd_per_million=4.0,
    )


def request(message, session_id=None, *, user="guest:conversation"):
    return ChatRequest(
        message=message, sessionId=session_id, user={"id": user, "displayName": "Fixture"}
    )


def chat(db, settings, provider=None, *, now=NOW):
    return NewsChatService(settings, lambda: provider, db, clock=lambda: now)


async def test_affirmative_followup_reaches_llm_with_the_previous_offer_and_citations(
    database, settings
):
    offer = "Si quieres, puedo listar las noticias publicadas o filtrarlas por país."
    provider = FakeProvider(offer)
    service = chat(database, replace(settings, provider="openai", api_key="fixture"), provider)
    first = await service.reply(request("Noticias de México"))
    second = await service.reply(request("ok si hazlo", first.sessionId))
    assert second.sessionId == first.sessionId
    assert second.message.intent != ResponseIntent.unsupported
    assert second.message.strategy == ResponseStrategy.llm
    assert len(provider.calls) == 2
    assert provider.calls[1]["history"][-1] == {"role": "assistant", "content": offer}
    assert {d["id"] for d in provider.calls[1]["context"]["noticias"]} == {
        c.id for c in first.message.citedNews
    }
    assert len(database["chatSessions"].documents) == 1
    assert len(database["chatSessions"].documents[0]["messages"]) == 4


@pytest.mark.parametrize("followup", ["de que paises son", "resúmelas", "explica esas noticias"])
async def test_followup_uses_the_previous_selection_instead_of_newer_unrelated_news(
    database, settings, followup
):
    provider = FakeProvider()
    service = chat(database, replace(settings, provider="openai", api_key="fixture"), provider)
    first = await service.reply(request("Noticias de México"))
    second = await service.reply(request(followup, first.sessionId))
    assert second.message.intent != ResponseIntent.unsupported
    assert {c.id for c in second.message.citedNews} == {c.id for c in first.message.citedNews}
    assert {
        loc["countryCode"]
        for article in provider.calls[-1]["context"]["noticias"]
        for loc in article["geographicScope"]["locations"]
    } == {"MX"}


async def test_followup_keeps_count_operation_when_country_changes(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Cuántas noticias tienes de Guatemala"))
    second = await service.reply(request("¿Y de México?", first.sessionId))
    assert "2 noticias" in second.message.content
    assert "México" in second.message.content
    assert "publicadas" in second.message.content
    assert second.message.strategy == ResponseStrategy.database_query


async def test_followup_keeps_topic_when_changing_country(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de tecnología de Guatemala"))
    second = await service.reply(request("¿Y de México?", first.sessionId))
    assert [c.slug for c in second.message.citedNews] == ["mx-tech"]


async def test_short_count_refers_to_the_previous_country(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de México"))
    second = await service.reply(request("¿Y cuántas hay?", first.sessionId))
    assert "2 noticias" in second.message.content
    assert "México" in second.message.content
    assert second.message.strategy == ResponseStrategy.database_query


async def test_explicit_new_request_replaces_previous_country_and_topic(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de tecnología de Guatemala"))
    second = await service.reply(request("Noticias de deportes de México", first.sessionId))
    assert [c.slug for c in second.message.citedNews] == ["mx-sports"]


async def test_ordinal_detail_selects_the_previous_second_article(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de México"))
    second = await service.reply(request("Dame detalles de la segunda", first.sessionId))
    assert [c.id for c in second.message.citedNews] == [first.message.citedNews[1].id]


async def test_followups_never_reuse_another_users_or_expired_session(database, settings):
    first = await chat(database, settings).reply(request("Noticias de México"))
    other = await chat(database, settings).reply(
        request("ok si hazlo", first.sessionId, user="guest:other")
    )
    expired = await chat(database, settings, now=NOW + timedelta(seconds=3601)).reply(
        request("ok si hazlo", first.sessionId)
    )
    assert other.sessionId != first.sessionId
    assert expired.sessionId != first.sessionId
    assert other.message.citedNews == []
    assert expired.message.citedNews == []


async def test_off_topic_request_does_not_inherit_the_news_selection(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de México"))
    second = await service.reply(request("Dame una receta de pastel de chocolate", first.sessionId))
    assert second.message.intent == ResponseIntent.unsupported
    assert second.message.citedNews == []


async def test_previous_citations_are_rechecked_for_publication(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de México"))
    for document in database["news"].documents:
        if str(document["_id"]) == first.message.citedNews[0].id:
            document["status"] = "draft"
    second = await service.reply(request("resúmelas", first.sessionId))
    assert [c.id for c in second.message.citedNews] == [first.message.citedNews[1].id]


async def test_out_of_range_ordinal_does_not_choose_an_unrelated_article(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de México"))
    second = await service.reply(request("Explica la quinta", first.sessionId))
    assert second.message.citedNews == []
    assert "no" in second.message.content.lower()


async def test_exact_three_turn_sequence_keeps_the_last_offer_and_selection(database, settings):
    provider = FakeProvider("Estas son las noticias de México.")
    service = chat(database, replace(settings, provider="openai", api_key="fixture"), provider)
    first = await service.reply(request("Noticias de México"))
    offer = "Si quieres, puedo listar solo las noticias publicadas o filtrar por país."
    provider.text = offer
    second = await service.reply(request("de que paises son", first.sessionId))
    provider.text = "¿Prefieres listar las noticias o elegir un país?"
    third = await service.reply(request("ok si hazlo", second.sessionId))
    assert first.sessionId == second.sessionId == third.sessionId
    assert third.message.intent != ResponseIntent.unsupported
    assert provider.calls[-1]["history"][-1]["content"] == offer
    assert {c.id for c in third.message.citedNews} == {c.id for c in first.message.citedNews}


async def test_returning_to_news_after_an_unsupported_turn_keeps_the_news_context(
    database, settings
):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de México"))
    unrelated = await service.reply(request("Receta de pastel de chocolate", first.sessionId))
    assert unrelated.message.intent == ResponseIntent.unsupported
    again = await service.reply(request("resúmelas", first.sessionId))
    assert {c.id for c in again.message.citedNews} == {c.id for c in first.message.citedNews}


async def test_followup_preserves_the_whole_previous_selection_after_recreating_the_service(
    database, settings
):
    first = await chat(database, settings).reply(request("Noticias recientes"))
    assert len(first.message.citedNews) == 4
    second = await chat(database, settings).reply(request("de que paises son", first.sessionId))
    assert [c.id for c in second.message.citedNews] == [c.id for c in first.message.citedNews]


async def test_empty_country_results_do_not_reuse_older_citations(database, settings):
    service = chat(database, settings)
    first = await service.reply(request("Noticias de México"))
    empty = await service.reply(request("Noticias de Canadá", first.sessionId))
    assert empty.message.citedNews == []
    followup = await service.reply(request("resúmelas", first.sessionId))
    assert followup.message.citedNews == []

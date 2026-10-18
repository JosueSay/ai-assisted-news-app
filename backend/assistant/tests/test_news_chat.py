"""Tests offline del modo news del assistant."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from bson import ObjectId
from news.firebase_auth import FirebaseIdentity
from news.models import (
    ConfidenceLevel,
    ImageType,
    LocationLevel,
    NewsStatus,
    ResponseIntent,
    ResponseStrategy,
    SourceType,
    VerificationStatus,
)
from news.models.chat_session import ChatSession
from news.models.news import GeographicScope, Image, News, Source, Verification
from news.models.reading_time import compute_reading_time
from news.seed_catalog import CATALOG_LOCATION_IDS, catalog_location_document

from assistant.config import ChatbotConfigurationError, get_settings
from assistant.news_chat.intent import classify_message, normalize_text
from assistant.news_chat.retrieval import compute_confidence
from assistant.news_chat.schemas import ChatRequest
from assistant.news_chat.service import NewsChatRequestError, NewsChatService
from assistant.providers.openai import OpenAIProviderError
from assistant.tests.news_fakes import FakeDatabase, FakeProvider

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)
AUTHOR_ID = ObjectId("670000000000000000000002")
GT = CATALOG_LOCATION_IDS["GT"]
MX = CATALOG_LOCATION_IDS["MX"]
TEST_IDENTITY = FirebaseIdentity(
    "guest-abc-123", "invitado@example.test", "Invitado"
)


@pytest.fixture
def stub_settings():
    return replace(
        get_settings(),
        provider="stub",
        mongodb_context_mode="news",
        chat_session_ttl_seconds=3600,
        ai_budget_usd=20.0,
        input_usd_per_million=1.0,
        output_usd_per_million=4.0,
        default_location_code="GT",
        max_output_tokens=500,
    )


@pytest.fixture
def llm_settings(stub_settings):
    return replace(stub_settings, provider="openai", api_key="test-key")


def make_news(
    slug: str,
    title: str,
    *,
    topic: str = "actualidad",
    location_id: ObjectId = GT,
    status: NewsStatus = NewsStatus.published,
    verification: VerificationStatus = VerificationStatus.confirmed,
    sources: int = 2,
    days_ago: int = 0,
) -> dict:
    published_at = NOW - timedelta(days=days_ago)
    content = f"Contenido completo de {title}."
    word_count, reading_minutes = compute_reading_time(content)
    return News(
        slug=slug,
        title=title,
        summary=f"Resumen de {title}.",
        content=content,
        wordCount=word_count,
        estimatedReadingMinutes=reading_minutes,
        authorId=AUTHOR_ID,
        status=status,
        topics=[topic],
        keywords=[topic],
        geographicScope=GeographicScope(level=LocationLevel.country, locationIds=[location_id]),
        verification=Verification(status=verification),
        sources=[
            Source(
                name=f"Medio {index}",
                url=f"https://medio{index}.example.com/nota",
                sourceType=SourceType.media,
                accessedAt=published_at,
            )
            for index in range(sources)
        ],
        image=Image(type=ImageType.none),
        publishedAt=published_at if status == NewsStatus.published else None,
        createdAt=published_at,
        updatedAt=published_at,
    ).model_dump_mongo()


@pytest.fixture
async def db() -> FakeDatabase:
    database = FakeDatabase()
    for code, name in (("GT", "Guatemala"), ("MX", "México")):
        await database["locations"].insert_one(
            catalog_location_document({"code": code, "name": name, "country": name})
        )
    await database["news"].insert_one(
        make_news("mercado-gt", "Mercado digital en Guatemala", topic="economia")
    )
    await database["news"].insert_one(
        make_news(
            "liga-mx", "Liga comunitaria en México", topic="deportes", location_id=MX, days_ago=1
        )
    )
    await database["news"].insert_one(
        make_news("borrador", "Borrador sin publicar", status=NewsStatus.draft)
    )
    return database


def chat_request(message: str, **overrides) -> ChatRequest:
    payload = {
        "message": message,
    }
    payload.update(overrides)
    return ChatRequest.model_validate(payload)


class _ServiceWithDefaultTestIdentity(NewsChatService):
    async def reply(self, request, *, identity=TEST_IDENTITY):
        return await super().reply(request, identity=identity)


def service(db, settings, provider=None, clock=lambda: NOW) -> NewsChatService:
    return _ServiceWithDefaultTestIdentity(settings, lambda: provider, db, clock=clock)


# ----------------------------------------------------------------------
# Intención
# ----------------------------------------------------------------------


def test_normalize_text_removes_accents_and_symbols() -> None:
    assert normalize_text("¿Qué pasó en Japón HOY?") == "que paso en japon hoy"


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("¿Cuáles son las últimas noticias?", ResponseIntent.recent_news),
        ("Noticias de Guatemala", ResponseIntent.regional_news),
        ("¿Qué pasa en mi país?", ResponseIntent.regional_news),
        ("Noticias de tecnología", ResponseIntent.topic_news),
        ("Resume las noticias de México", ResponseIntent.summarize),
        ("Explícame por qué subió el precio", ResponseIntent.explain),
        ("Dame más detalle sobre el mercado digital", ResponseIntent.news_detail),
    ],
)
def test_classify_message_detects_intent(message: str, intent: ResponseIntent) -> None:
    assert classify_message(message, has_news_context=False).intent == intent


def test_unmatched_message_has_no_intent() -> None:
    query = classify_message("receta de pastel de chocolate", has_news_context=False)
    assert query.intent is None
    assert query.terms == ("receta", "pastel", "chocolate")


# ----------------------------------------------------------------------
# Respuestas sin proveedor real (stub)
# ----------------------------------------------------------------------


async def test_recent_news_without_llm_uses_database_and_persists_session(db, stub_settings):
    reply = await service(db, stub_settings).reply(
        chat_request("¿Cuáles son las últimas noticias?")
    )

    assert reply.message.strategy == ResponseStrategy.database_query
    assert reply.message.intent == ResponseIntent.recent_news
    assert reply.message.aiUsed is False
    assert [news.slug for news in reply.message.citedNews] == ["mercado-gt", "liga-mx"]
    assert "Borrador" not in reply.message.content
    assert reply.message.confidence == ConfidenceLevel.high
    assert reply.expiresAt == (NOW + timedelta(seconds=3600)).isoformat()
    assert reply.locationId == str(GT)

    stored = ChatSession.model_validate(db["chatSessions"].documents[0])
    assert [message.role.value for message in stored.messages] == ["user", "assistant"]
    assert len(stored.messages[1].responseMetadata.citedNewsIds) == 2
    assert db["aiUsage"].documents == []

    user = db["users"].documents[0]
    assert user["firebaseUid"] == TEST_IDENTITY.uid
    assert user["simulatedLocationId"] == GT


async def test_regional_and_topic_filters(db, stub_settings):
    regional = await service(db, stub_settings).reply(chat_request("Noticias de México"))
    topic = await service(db, stub_settings).reply(chat_request("Noticias de economía"))

    assert regional.message.content.startswith("Noticias de México:")
    assert [news.slug for news in regional.message.citedNews] == ["liga-mx"]
    assert [news.slug for news in topic.message.citedNews] == ["mercado-gt"]


@pytest.mark.parametrize(
    "message",
    [
        "noticias recientes",
        "noticias de México",
        "noticias de economía",
        "dame más detalle sobre mercado digital",
        "algo sobre lo digital",
        "¿cuántas noticias hay?",
        "¿qué noticias tienes por país?",
    ],
)
async def test_code_capabilities_do_not_call_llm_even_when_provider_is_enabled(
    db, llm_settings, message
):
    provider = FakeProvider()

    reply = await service(db, llm_settings, provider).reply(chat_request(message))

    assert reply.message.strategy == ResponseStrategy.database_query
    assert provider.calls == []
    assert db["aiUsage"].documents == []


async def test_mixed_request_executes_news_part_and_reports_unsupported_part(db, stub_settings):
    reply = await service(db, stub_settings).reply(
        chat_request("Noticias de México y haz una transferencia")
    )

    assert [news.slug for news in reply.message.citedNews] == ["liga-mx"]
    assert "no puedo realizar acciones externas" in reply.message.content


async def test_out_of_scope_request_is_template_without_news_citations(db, llm_settings):
    provider = FakeProvider()

    async def fail_if_news_is_read(*_args, **_kwargs):
        raise AssertionError("out-of-scope request must not query news")

    db["news"].find_one = fail_if_news_is_read

    reply = await service(db, llm_settings, provider).reply(
        chat_request("Haz una transferencia", newsId=str(ObjectId()))
    )

    assert reply.message.intent == ResponseIntent.unsupported
    assert reply.message.strategy == ResponseStrategy.template
    assert reply.message.citedNews == []
    assert provider.calls == []
    assert db["aiUsage"].documents == []


async def test_selected_location_is_used_for_local_news(db, stub_settings):
    reply = await service(db, stub_settings).reply(
        chat_request("noticias locales", locationId=str(MX))
    )

    assert db["users"].documents[0]["simulatedLocationId"] == MX
    assert reply.locationId == str(MX)
    assert [news.slug for news in reply.message.citedNews] == ["liga-mx"]


async def test_free_text_search_and_follow_up(db, stub_settings):
    first = await service(db, stub_settings).reply(chat_request("¿Algo sobre lo digital?"))
    follow_up = await service(db, stub_settings).reply(
        chat_request("¿y eso?", sessionId=first.sessionId)
    )

    assert first.message.intent == ResponseIntent.news_detail
    assert [news.slug for news in first.message.citedNews] == ["mercado-gt"]
    assert follow_up.message.intent == ResponseIntent.explain
    assert [news.slug for news in follow_up.message.citedNews] == ["mercado-gt"]

    off_topic = await service(db, stub_settings).reply(
        chat_request("¿Quién ganó el mundial?", sessionId=first.sessionId)
    )
    assert off_topic.message.intent == ResponseIntent.unsupported
    assert off_topic.message.citedNews == []


async def test_unsupported_request_uses_template(db, stub_settings):
    reply = await service(db, stub_settings).reply(chat_request("receta de pastel de chocolate"))

    assert reply.message.strategy == ResponseStrategy.template
    assert reply.message.intent == ResponseIntent.unsupported
    assert reply.message.citedNews == []


async def test_summarize_with_stub_explains_ai_is_disabled(db, stub_settings):
    reply = await service(db, stub_settings).reply(chat_request("Resume las noticias"))

    assert reply.message.strategy == ResponseStrategy.database_query
    assert "no está habilitada" in reply.message.content


async def test_sessions_are_reused_only_while_valid_and_by_owner(db, stub_settings):
    first = await service(db, stub_settings).reply(chat_request("noticias"))
    second = await service(db, stub_settings).reply(
        chat_request("noticias", sessionId=first.sessionId)
    )
    expired = await service(db, stub_settings, clock=lambda: NOW + timedelta(seconds=3601)).reply(
        chat_request("noticias", sessionId=first.sessionId)
    )
    other = await service(db, stub_settings).reply(
        chat_request("noticias", sessionId=first.sessionId),
        identity=FirebaseIdentity("other-firebase-uid", display_name="Otra persona"),
    )

    assert second.sessionId == first.sessionId
    assert expired.sessionId != first.sessionId
    assert other.sessionId != first.sessionId


# ----------------------------------------------------------------------
# Respuestas con proveedor real
# ----------------------------------------------------------------------


async def test_llm_reply_records_ai_usage_and_sends_history(db, llm_settings):
    provider = FakeProvider("Respuesta del modelo.", tokens=(1000, 500))
    first = await service(db, llm_settings, provider).reply(chat_request("noticias"))
    reply = await service(db, llm_settings, provider).reply(
        chat_request("Resume las noticias de Guatemala", sessionId=first.sessionId)
    )

    assert reply.message.strategy == ResponseStrategy.llm
    assert reply.message.aiUsed is True
    assert reply.message.content == "Respuesta del modelo."
    assert [news.slug for news in reply.message.citedNews] == ["mercado-gt"]

    call = provider.calls[0]
    assert [item["role"] for item in call["history"]] == ["user", "assistant"]
    assert call["previous_response_id"] is None
    assert call["context"]["noticias"][0]["title"] == "Mercado digital en Guatemala"
    assert "content" in call["context"]["noticias"][0]

    usage = db["aiUsage"].documents
    assert len(usage) == 1
    assert usage[0]["feature"].value == "chat"
    assert usage[0]["provider"] == "openai"
    assert usage[0]["chatSessionId"] == ObjectId(reply.sessionId)
    assert usage[0]["estimatedCostUsd"] == pytest.approx(1000 * 1.0 / 1e6 + 500 * 4.0 / 1e6)
    stored = ChatSession.model_validate(db["chatSessions"].documents[0])
    assert stored.messages[-1].responseMetadata.aiUsed is True


async def test_llm_on_open_article_attributes_usage_to_news(db, llm_settings):
    news_id = db["news"].documents[0]["_id"]
    provider = FakeProvider("Explicación de la noticia.")

    reply = await service(db, llm_settings, provider).reply(
        chat_request(
            "Explícame esta noticia: Mercado digital en Guatemala", newsId=str(news_id)
        )
    )

    assert reply.message.intent == ResponseIntent.explain
    assert db["aiUsage"].documents[0]["newsId"] == news_id
    assert provider.calls[0]["message"].endswith("Mercado digital en Guatemala")
    assert provider.calls[0]["context"]["noticias"][0]["title"] == (
        "Mercado digital en Guatemala"
    )


async def test_unsupported_and_not_found_do_not_call_llm(db, llm_settings):
    provider = FakeProvider()
    await service(db, llm_settings, provider).reply(chat_request("receta de pastel de chocolate"))
    not_found = await service(db, llm_settings, provider).reply(chat_request("Noticias de Japón"))

    assert provider.calls == []
    assert not_found.message.strategy == ResponseStrategy.database_query
    assert db["aiUsage"].documents == []


async def test_missing_token_usage_records_worst_case_cost(db, llm_settings):
    await service(db, llm_settings, FakeProvider(tokens=None)).reply(
        chat_request("Resume las noticias")
    )

    usage = db["aiUsage"].documents[0]
    assert usage["inputTokens"] is None
    assert usage["estimatedCostUsd"] > 500 * 4.0 / 1e6


async def test_exhausted_budget_skips_provider(db, llm_settings):
    await db["aiUsage"].insert_one({"_id": ObjectId(), "estimatedCostUsd": 20.0})
    provider = FakeProvider()

    reply = await service(db, llm_settings, provider).reply(chat_request("Resume las noticias"))

    assert provider.calls == []
    assert reply.message.strategy == ResponseStrategy.database_query
    assert "presupuesto" in reply.message.content


async def test_provider_error_falls_back_without_usage(db, llm_settings):
    class FailingProvider(FakeProvider):
        async def generate(self, **options):
            raise OpenAIProviderError("fallo")

    reply = await service(db, llm_settings, FailingProvider()).reply(
        chat_request("Resume las noticias")
    )

    assert reply.message.strategy == ResponseStrategy.database_query
    assert db["aiUsage"].documents == []


async def test_real_provider_requires_prices(db, llm_settings):
    settings = replace(llm_settings, input_usd_per_million=None)

    with pytest.raises(ChatbotConfigurationError, match="PER_MILLION"):
        await service(db, settings, FakeProvider()).reply(chat_request("Resume las noticias"))


async def test_unconfirmed_news_is_flagged_in_llm_reply(db, llm_settings):
    await db["news"].insert_one(
        make_news("sismo-gt", "Sismo en desarrollo", verification=VerificationStatus.developing)
    )
    news_id = db["news"].documents[-1]["_id"]

    reply = await service(db, llm_settings, FakeProvider("Explicación.")).reply(
        chat_request("explícame esto", newsId=str(news_id))
    )

    assert reply.message.confidence == ConfidenceLevel.low
    assert "en desarrollo" in reply.message.uncertainty
    assert "Aviso:" in reply.message.content


# ----------------------------------------------------------------------
# Errores de petición y confianza
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "status_code"),
    [
        ({"newsId": str(ObjectId())}, 404),
        ({"sessionId": "no-es-id"}, 400),
        ({"locationId": str(ObjectId())}, 400),
    ],
)
async def test_request_errors(db, stub_settings, overrides, status_code):
    with pytest.raises(NewsChatRequestError) as error:
        await service(db, stub_settings).reply(chat_request("explica", **overrides))
    assert error.value.status_code == status_code


async def test_draft_news_cannot_be_used_as_context(db, stub_settings):
    draft_id = db["news"].documents[2]["_id"]
    with pytest.raises(NewsChatRequestError) as error:
        await service(db, stub_settings).reply(chat_request("explica", newsId=str(draft_id)))
    assert error.value.status_code == 404


async def test_empty_catalog_returns_503(stub_settings):
    with pytest.raises(NewsChatRequestError) as error:
        await service(FakeDatabase(), stub_settings).reply(chat_request("noticias"))
    assert error.value.status_code == 503


def test_confidence_levels() -> None:
    two_sources = make_news("a", "A", sources=2)
    one_source = make_news("b", "B", sources=1)
    conflicting = make_news("c", "C", verification=VerificationStatus.conflicting_sources)
    official = make_news("d", "D", sources=1)
    official["sources"][0]["sourceType"] = SourceType.official

    assert compute_confidence([two_sources]).level == ConfidenceLevel.high
    assert compute_confidence([official]).level == ConfidenceLevel.high
    assert compute_confidence([one_source]).level == ConfidenceLevel.medium
    assert compute_confidence([two_sources, conflicting]).level == ConfidenceLevel.low
    assert compute_confidence([]).level == ConfidenceLevel.low


def test_chat_request_rejects_client_supplied_identity() -> None:
    with pytest.raises(ValueError):
        ChatRequest.model_validate({"message": "hola", "user": {"id": "admin", "role": "admin"}})

"""Regresión de integración con las fixtures aprobadas del PR 4228506."""

from dataclasses import replace

import pytest
from news.demo_news import get_demo_news_documents
from news.models import ResponseIntent, UserRole
from news.models.chat_session import ChatSession
from news.seed_catalog import CATALOG_LOCATIONS, catalog_location_document
from news.topics import TOPICS

from assistant.config import get_settings
from assistant.news_chat.intent import classify_message
from assistant.news_chat.schemas import ChatRequest
from assistant.news_chat.service import NewsChatRequestError, NewsChatService
from assistant.tests.news_fakes import FakeDatabase


@pytest.mark.parametrize("topic", TOPICS)
async def test_chat_filters_canonical_dataset_by_every_catalog_topic(topic):
    database = FakeDatabase()
    database["locations"].documents.extend(catalog_location_document(c) for c in CATALOG_LOCATIONS)
    documents = get_demo_news_documents()
    database["news"].documents.extend(documents)
    settings = replace(get_settings(), provider="stub", mongodb_context_mode="news")
    query = classify_message(f"Noticias de {topic.replace('_', ' ')}", has_news_context=False)
    assert query.intent == ResponseIntent.topic_news
    assert query.topics == (topic,)
    response = await NewsChatService(settings, lambda: None, database).reply(
        ChatRequest(
            message=f"Noticias de {topic.replace('_', ' ')}",
            user={"id": "guest:canonical", "displayName": "Fixture"},
        )
    )
    cited_ids = {citation.id for citation in response.message.citedNews}
    expected = [d for d in documents if d["status"] == "published" and topic in d["topics"]]
    assert cited_ids
    assert cited_ids <= {str(d["_id"]) for d in expected}
    assert len(cited_ids) == min(5, len(expected))
    ChatSession.model_validate(database["chatSessions"].documents[0])
    assert database["aiUsage"].documents == []


async def test_chat_reuses_admin_author_identity_without_replacing_profile():
    from news.api import _stable_admin_author_id
    from news.models.user import User
    from news.seed_catalog import CATALOG_LOCATION_IDS

    database = FakeDatabase()
    author = User(
        _id=_stable_admin_author_id("admin"),
        firebaseUid="local-admin:admin",
        email="admin@local.admin",
        displayName="Redacción",
        role=UserRole.admin,
        simulatedLocationId=CATALOG_LOCATION_IDS["GT"],
    ).model_dump_mongo()
    database["users"].documents.append(author)
    request = ChatRequest(message="noticias", user={"id": "admin:admin", "displayName": "Admin"})
    settings = replace(get_settings(), provider="stub")
    response = await NewsChatService(settings, lambda: None, database).reply(
        request, admin_username="admin"
    )
    assert len(database["users"].documents) == 1
    assert database["users"].documents[0]["displayName"] == "Redacción"
    assert database["users"].documents[0]["role"] == UserRole.admin
    assert database["chatSessions"].documents[0]["userId"] == author["_id"]
    assert response.sessionId


@pytest.mark.parametrize("external_id", ["admin:admin", "local-admin:admin"])
async def test_client_cannot_claim_admin_identity_without_verified_token(external_id):
    database = FakeDatabase()
    request = ChatRequest(message="noticias", user={"id": external_id, "displayName": "Admin"})
    with pytest.raises(NewsChatRequestError) as error:
        await NewsChatService(get_settings(), lambda: None, database).reply(request)
    assert error.value.status_code == 401
    assert database["users"].documents == []

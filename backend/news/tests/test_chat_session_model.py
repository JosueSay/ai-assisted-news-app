"""Tests para el modelo ChatSession (incluye Message y ResponseMetadata)."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import ValidationError

from news.models import (
    ConfidenceLevel,
    MessageRole,
    ResponseIntent,
    ResponseStrategy,
)
from news.models.chat_session import ChatSession, Message, ResponseMetadata


def test_valid_session():
    session = ChatSession(
        userId=ObjectId(),
        simulatedLocationId=ObjectId(),
    )
    assert session.messages == []
    assert isinstance(session.id, ObjectId)


def test_message_roles():
    msg_user = Message(role=MessageRole.user, content="Hello")
    msg_assistant = Message(role=MessageRole.assistant, content="Hi there")
    assert msg_user.role == MessageRole.user
    assert msg_assistant.role == MessageRole.assistant


def test_invalid_role():
    try:
        Message(role="bot", content="test")
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_response_strategies():
    for strategy in ResponseStrategy:
        meta = ResponseMetadata(
            strategy=strategy,
            intent=ResponseIntent.recent_news,
            confidence=ConfidenceLevel.high,
            aiUsed=strategy == ResponseStrategy.llm,
        )
        assert meta.strategy == strategy


def test_response_intents():
    for intent in ResponseIntent:
        meta = ResponseMetadata(
            strategy=ResponseStrategy.database_query,
            intent=intent,
            confidence=ConfidenceLevel.high,
        )
        assert meta.intent == intent


def test_confidence_levels():
    for level in ConfidenceLevel:
        meta = ResponseMetadata(
            strategy=ResponseStrategy.template,
            intent=ResponseIntent.topic_news,
            confidence=level,
        )
        assert meta.confidence == level


def test_response_metadata_on_assistant():
    meta = ResponseMetadata(
        strategy=ResponseStrategy.llm,
        intent=ResponseIntent.explain,
        citedNewsIds=[ObjectId(), ObjectId()],
        confidence=ConfidenceLevel.medium,
        uncertainty="Some uncertainty",
        aiUsed=True,
    )
    msg = Message(role=MessageRole.assistant, content="Explanation", responseMetadata=meta)
    assert msg.responseMetadata is not None
    assert msg.responseMetadata.strategy == ResponseStrategy.llm
    assert msg.responseMetadata.intent == ResponseIntent.explain
    assert len(msg.responseMetadata.citedNewsIds) == 2
    assert msg.responseMetadata.aiUsed is True
    assert msg.responseMetadata.uncertainty == "Some uncertainty"


def test_response_metadata_requires_consistent_ai_used():
    for strategy, ai_used in (
        (ResponseStrategy.database_query, True),
        (ResponseStrategy.template, True),
        (ResponseStrategy.llm, False),
    ):
        try:
            ResponseMetadata(
                strategy=strategy,
                intent=ResponseIntent.recent_news,
                confidence=ConfidenceLevel.high,
                aiUsed=ai_used,
            )
            assert False, "Expected ValidationError"
        except ValidationError:
            pass


def test_user_message_without_metadata():
    msg = Message(role=MessageRole.user, content="Just a question")
    assert msg.responseMetadata is None


def test_user_message_rejects_response_metadata():
    metadata = ResponseMetadata(
        strategy=ResponseStrategy.template,
        intent=ResponseIntent.unsupported,
        confidence=ConfidenceLevel.low,
    )
    try:
        Message(role=MessageRole.user, content="Question", responseMetadata=metadata)
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_default_expires_at_is_3600_seconds_ahead():
    session = ChatSession(
        userId=ObjectId(),
        simulatedLocationId=ObjectId(),
    )
    diff = (session.expiresAt - session.createdAt).total_seconds()
    assert abs(diff - 3600) < 2


def test_model_dump_mongo_includes_id():
    session = ChatSession(
        userId=ObjectId(),
        simulatedLocationId=ObjectId(),
    )
    dumped = session.model_dump_mongo()
    assert "_id" in dumped
    assert isinstance(dumped["_id"], ObjectId)

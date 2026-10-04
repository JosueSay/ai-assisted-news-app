"""Tests para el modelo AiUsage."""

from bson import ObjectId
from pydantic import ValidationError

from news.models import AiFeature
from news.models.ai_usage import AiUsage


def test_valid_usage():
    usage = AiUsage(
        feature=AiFeature.chat,
        provider="openai",
        model="gpt-4",
        estimatedCostUsd=0.05,
    )
    assert usage.feature == AiFeature.chat
    assert usage.estimatedCostUsd == 0.05


def test_all_features():
    for feature in AiFeature:
        usage = AiUsage(
            feature=feature,
            provider="test",
            model="test-model",
            estimatedCostUsd=0.0,
        )
        assert usage.feature == feature


def test_negative_cost():
    try:
        AiUsage(
            feature=AiFeature.summary,
            provider="test",
            model="test",
            estimatedCostUsd=-0.01,
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_zero_cost_allowed():
    usage = AiUsage(
        feature=AiFeature.classification,
        provider="test",
        model="test",
        estimatedCostUsd=0.0,
    )
    assert usage.estimatedCostUsd == 0.0


def test_negative_input_tokens():
    try:
        AiUsage(
            feature=AiFeature.chat,
            provider="test",
            model="test",
            inputTokens=-1,
            estimatedCostUsd=0.0,
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_negative_output_tokens():
    try:
        AiUsage(
            feature=AiFeature.chat,
            provider="test",
            model="test",
            outputTokens=-10,
            estimatedCostUsd=0.0,
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_null_tokens_allowed():
    usage = AiUsage(
        feature=AiFeature.image_generation,
        provider="test",
        model="test",
        inputTokens=None,
        outputTokens=None,
        estimatedCostUsd=0.05,
    )
    assert usage.inputTokens is None
    assert usage.outputTokens is None


def test_null_references_allowed():
    usage = AiUsage(
        feature=AiFeature.chat,
        provider="test",
        model="test",
        userId=None,
        newsId=None,
        chatSessionId=None,
        estimatedCostUsd=0.01,
    )
    assert usage.userId is None
    assert usage.newsId is None
    assert usage.chatSessionId is None


def test_model_dump_mongo_includes_id():
    usage = AiUsage(
        feature=AiFeature.chat,
        provider="openai",
        model="gpt-4",
        estimatedCostUsd=0.0,
    )
    dumped = usage.model_dump_mongo()
    assert "_id" in dumped
    assert isinstance(dumped["_id"], ObjectId)
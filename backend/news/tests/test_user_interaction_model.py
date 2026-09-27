"""Tests para el modelo UserInteraction."""

from bson import ObjectId
from pydantic import ValidationError

from news.models import InteractionType
from news.models.user_interaction import InteractionContext, UserInteraction


def test_opened_type():
    interaction = UserInteraction(
        userId=ObjectId(),
        newsId=ObjectId(),
        type=InteractionType.opened,
        context=InteractionContext(simulatedLocationId=ObjectId()),
    )
    assert interaction.type == InteractionType.opened


def test_read_type():
    interaction = UserInteraction(
        userId=ObjectId(),
        newsId=ObjectId(),
        type=InteractionType.read,
        dwellTimeSeconds=30,
        context=InteractionContext(simulatedLocationId=ObjectId()),
    )
    assert interaction.type == InteractionType.read


def test_invalid_type():
    try:
        UserInteraction(
            userId=ObjectId(),
            newsId=ObjectId(),
            type="shared",
            context=InteractionContext(simulatedLocationId=ObjectId()),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_dwell_time_negative():
    try:
        UserInteraction(
            userId=ObjectId(),
            newsId=ObjectId(),
            type=InteractionType.read,
            dwellTimeSeconds=-1,
            context=InteractionContext(simulatedLocationId=ObjectId()),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_dwell_time_none_allowed():
    interaction = UserInteraction(
        userId=ObjectId(),
        newsId=ObjectId(),
        type=InteractionType.opened,
        dwellTimeSeconds=None,
        context=InteractionContext(simulatedLocationId=ObjectId()),
    )
    assert interaction.dwellTimeSeconds is None


def test_feed_position_negative():
    try:
        UserInteraction(
            userId=ObjectId(),
            newsId=ObjectId(),
            type=InteractionType.opened,
            context=InteractionContext(
                simulatedLocationId=ObjectId(), feedPosition=-1
            ),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_feed_position_none_allowed():
    ctx = InteractionContext(simulatedLocationId=ObjectId(), feedPosition=None)
    assert ctx.feedPosition is None


def test_context_required():
    try:
        UserInteraction(
            userId=ObjectId(),
            newsId=ObjectId(),
            type=InteractionType.opened,
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_model_dump_mongo_includes_id():
    interaction = UserInteraction(
        userId=ObjectId(),
        newsId=ObjectId(),
        type=InteractionType.opened,
        context=InteractionContext(simulatedLocationId=ObjectId()),
    )
    dumped = interaction.model_dump_mongo()
    assert "_id" in dumped
    assert isinstance(dumped["_id"], ObjectId)
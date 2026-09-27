"""Tests para el modelo AuditLog."""

from bson import ObjectId
from pydantic import ValidationError

from news.models import AuditAction
from news.models.audit_log import AuditLog


def test_valid_audit_log():
    log = AuditLog(
        actorId=ObjectId(),
        action=AuditAction.news_created,
        entityId=ObjectId(),
    )
    assert log.action == AuditAction.news_created
    assert log.entityType == "news"


def test_all_actions():
    for action in AuditAction:
        log = AuditLog(
            actorId=ObjectId(),
            action=action,
            entityId=ObjectId(),
        )
        assert log.action == action


def test_entity_type_news():
    log = AuditLog(
        actorId=ObjectId(),
        action=AuditAction.news_updated,
        entityId=ObjectId(),
        entityType="news",
    )
    assert log.entityType == "news"


def test_entity_type_not_news():
    try:
        AuditLog(
            actorId=ObjectId(),
            action=AuditAction.news_published,
            entityType="user",
            entityId=ObjectId(),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_details_empty_dict_default():
    log = AuditLog(
        actorId=ObjectId(),
        action=AuditAction.image_generated,
        entityId=ObjectId(),
    )
    assert log.details == {}


def test_model_dump_mongo_includes_id():
    log = AuditLog(
        actorId=ObjectId(),
        action=AuditAction.news_created,
        entityId=ObjectId(),
    )
    dumped = log.model_dump_mongo()
    assert "_id" in dumped
    assert isinstance(dumped["_id"], ObjectId)
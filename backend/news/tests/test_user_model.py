"""Tests para el modelo User (incluye InferredInterest y Onboarding)."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import ValidationError

from news.models import UserRole
from news.models.user import InferredInterest, Onboarding, User


def test_valid_user():
    user = User(
        firebaseUid="abc123",
        email="test@example.com",
        displayName="Test User",
        simulatedLocationId=ObjectId(),
    )
    assert user.role == UserRole.user
    assert user.firebaseUid == "abc123"


def test_invalid_role():
    try:
        User(
            firebaseUid="abc123",
            email="test@example.com",
            displayName="Test",
            simulatedLocationId=ObjectId(),
            role="superadmin",
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_valid_inferred_interest():
    interest = InferredInterest(
        topic="technology",
        score=0.75,
        updatedAt=datetime.now(timezone.utc),
    )
    assert interest.topic == "technology"
    assert interest.score == 0.75


def test_inferred_interest_score_below_0():
    try:
        InferredInterest(
            topic="technology",
            score=-0.1,
            updatedAt=datetime.now(timezone.utc),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_inferred_interest_score_above_1():
    try:
        InferredInterest(
            topic="technology",
            score=1.5,
            updatedAt=datetime.now(timezone.utc),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_score_at_boundaries():
    i1 = InferredInterest(
        topic="a", score=0.0, updatedAt=datetime.now(timezone.utc)
    )
    i2 = InferredInterest(
        topic="b", score=1.0, updatedAt=datetime.now(timezone.utc)
    )
    assert i1.score == 0.0
    assert i2.score == 1.0


def test_onboarding_defaults():
    ob = Onboarding()
    assert ob.completed is False
    assert ob.completedAt is None
    assert ob.selectedTopics == []


def test_user_without_interests():
    user = User(
        firebaseUid="xyz789",
        email="nointerest@example.com",
        displayName="No Interest",
        simulatedLocationId=ObjectId(),
    )
    assert user.inferredInterests == []


def test_model_dump_mongo_includes_id():
    user = User(
        firebaseUid="id123",
        email="dump@example.com",
        displayName="Dump Test",
        simulatedLocationId=ObjectId(),
    )
    dumped = user.model_dump_mongo()
    assert "_id" in dumped
    assert isinstance(dumped["_id"], ObjectId)
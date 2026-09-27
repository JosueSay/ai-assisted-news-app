"""Modelo User — Cuenta de la persona usuaria con preferencias e intereses."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from . import UserRole


class InferredInterest(BaseModel):
    topic: str
    score: float
    updatedAt: datetime

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("score debe estar entre 0 y 1")
        return v


class Onboarding(BaseModel):
    completed: bool = False
    completedAt: datetime | None = None
    selectedTopics: list[str] = []


class User(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    firebaseUid: str
    email: str
    displayName: str
    photoUrl: str = ""
    role: UserRole = UserRole.user
    simulatedLocationId: ObjectId
    onboarding: Onboarding = Field(default_factory=Onboarding)
    inferredInterests: list[InferredInterest] = []
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lastLoginAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

    def model_dump_mongo(self) -> dict:
        return self.model_dump(by_alias=True, mode="python")

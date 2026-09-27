"""Modelo UserInteraction — Registro de interacciones de lectura."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from . import InteractionType


class InteractionContext(BaseModel):
    simulatedLocationId: ObjectId
    feedPosition: int | None = None

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("feedPosition")
    @classmethod
    def validate_feed_position(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("feedPosition no puede ser negativo")
        return v


class UserInteraction(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    userId: ObjectId
    newsId: ObjectId
    type: InteractionType
    dwellTimeSeconds: int | None = None
    context: InteractionContext
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

    @field_validator("dwellTimeSeconds")
    @classmethod
    def validate_dwell_time(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("dwellTimeSeconds no puede ser negativo")
        return v

    def model_dump_mongo(self) -> dict:
        return self.model_dump(by_alias=True, mode="python")
"""Modelo AiUsage — Registro de consumo de llamadas de IA y costo estimado."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from . import AiFeature


class AiUsage(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    feature: AiFeature
    provider: str
    model: str
    userId: ObjectId | None = None
    newsId: ObjectId | None = None
    chatSessionId: ObjectId | None = None
    inputTokens: int | None = None
    outputTokens: int | None = None
    estimatedCostUsd: float
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

    @field_validator("inputTokens")
    @classmethod
    def validate_input_tokens(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("inputTokens no puede ser negativo")
        return v

    @field_validator("outputTokens")
    @classmethod
    def validate_output_tokens(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("outputTokens no puede ser negativo")
        return v

    @field_validator("estimatedCostUsd")
    @classmethod
    def validate_cost(cls, v: float) -> float:
        if v < 0:
            raise ValueError("estimatedCostUsd no puede ser negativo")
        return v

    def model_dump_mongo(self) -> dict:
        return self.model_dump(by_alias=True, mode="python")
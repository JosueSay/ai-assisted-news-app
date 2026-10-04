"""Modelo ChatSession — Conversación temporal del usuario con el asistente."""

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pydantic import BaseModel, Field, model_validator

from . import ConfidenceLevel, MessageRole, ResponseIntent, ResponseStrategy


class ResponseMetadata(BaseModel):
    strategy: ResponseStrategy
    intent: ResponseIntent
    citedNewsIds: list[ObjectId] = []
    confidence: ConfidenceLevel
    uncertainty: str | None = None
    aiUsed: bool = False

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_ai_usage(self) -> "ResponseMetadata":
        if self.aiUsed != (self.strategy == ResponseStrategy.llm):
            raise ValueError("aiUsed solo puede ser true cuando strategy es llm")
        return self


class Message(BaseModel):
    role: MessageRole
    content: str
    responseMetadata: ResponseMetadata | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_response_metadata(self) -> "Message":
        if self.role == MessageRole.user and self.responseMetadata is not None:
            raise ValueError("responseMetadata solo aplica a mensajes assistant")
        return self


class ChatSession(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    userId: ObjectId
    simulatedLocationId: ObjectId
    messages: list[Message] = []
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiresAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(seconds=3600)
    )

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

    def model_dump_mongo(self) -> dict:
        return self.model_dump(by_alias=True, mode="python")

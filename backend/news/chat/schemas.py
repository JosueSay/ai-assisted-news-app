"""Modelos HTTP del endpoint POST /chat."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from ..models import ConfidenceLevel, ResponseIntent, ResponseStrategy

# Identificador externo provisional mientras Firebase Authentication no esté
# implementado: "<proveedor>:<id>", por ejemplo "google:1234" o "guest:<uuid>".
EXTERNAL_ID_PATTERN = r"^[a-z][a-z0-9-]*:[A-Za-z0-9._@:-]{1,160}$"


class ChatUserPayload(BaseModel):
    id: str = Field(pattern=EXTERNAL_ID_PATTERN)
    displayName: str = Field(min_length=1, max_length=120)
    email: str = Field(default="", max_length=254)
    photoUrl: str = Field(default="", max_length=2000)

    @field_validator("id", "displayName", "email", "photoUrl", mode="before")
    @classmethod
    def strip_value(cls, value):
        return value.strip() if isinstance(value, str) else value


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    sessionId: str | None = Field(default=None, max_length=24)
    newsId: str | None = Field(default=None, max_length=24)
    locationId: str | None = Field(default=None, max_length=24)
    user: ChatUserPayload

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("sessionId", "newsId", "locationId", mode="before")
    @classmethod
    def empty_as_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ChatCitedNews(BaseModel):
    id: str
    slug: str
    title: str
    verificationStatus: str


class ChatAssistantMessage(BaseModel):
    content: str
    strategy: ResponseStrategy
    intent: ResponseIntent
    confidence: ConfidenceLevel
    uncertainty: str | None
    aiUsed: bool
    citedNews: list[ChatCitedNews]
    createdAt: str


class ChatReply(BaseModel):
    sessionId: str
    expiresAt: str
    locationId: str
    message: ChatAssistantMessage

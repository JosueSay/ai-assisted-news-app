"""Contrato HTTP de POST /chat en modo news."""

from __future__ import annotations

from news.models import ConfidenceLevel, ResponseIntent, ResponseStrategy
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    sessionId: str | None = Field(default=None, max_length=24)
    newsId: str | None = Field(default=None, max_length=24)
    locationId: str | None = Field(default=None, max_length=24)

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

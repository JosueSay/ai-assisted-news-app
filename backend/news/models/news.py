"""Modelo News — Noticia publicable con metadatos completos."""

from datetime import datetime, timezone
from urllib.parse import urlparse

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, model_validator

from . import (
    ImageType,
    LocationLevel,
    NewsStatus,
    SourceType,
    VerificationStatus,
)
from .reading_time import compute_reading_time


def _validate_http_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url debe ser una URL HTTP(S) con host")
    return value


class GeographicScope(BaseModel):
    level: LocationLevel
    locationIds: list[ObjectId] = []

    model_config = {"arbitrary_types_allowed": True}


class Verification(BaseModel):
    status: VerificationStatus
    reviewedBy: ObjectId | None = None
    reviewedAt: datetime | None = None
    notes: str | None = None

    model_config = {"arbitrary_types_allowed": True}


class Source(BaseModel):
    name: str
    url: str
    sourceType: SourceType
    publishedAt: datetime | None = None
    accessedAt: datetime
    supports: str | None = None

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_http_url(v)


class Image(BaseModel):
    url: str | None = None
    alt: str | None = None
    type: ImageType
    credit: str | None = None
    rights: str | None = None
    aiDisclosure: str | None = None

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_http_url(v)

    @model_validator(mode="after")
    def validate_image_rules(self) -> "Image":
        if self.type == ImageType.none and (self.url is not None or self.alt is not None):
            raise ValueError("image.type 'none' requiere url y alt nulos")
        if self.type in {ImageType.ai_generated, ImageType.ai_modified} and not (
            self.aiDisclosure and self.aiDisclosure.strip()
        ):
            raise ValueError("las imágenes asistidas por IA requieren aiDisclosure")
        return self


class AiAssistance(BaseModel):
    summaryGenerated: bool = False
    topicsGenerated: bool = False
    imageGenerated: bool = False
    humanReviewed: bool = False


class News(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    slug: str
    title: str
    summary: str
    content: str
    authorId: ObjectId
    status: NewsStatus = NewsStatus.draft
    topics: list[str] = []
    keywords: list[str] = []
    geographicScope: GeographicScope
    verification: Verification
    sources: list[Source] = []
    image: Image
    aiAssistance: AiAssistance = Field(default_factory=AiAssistance)
    wordCount: int = 0
    estimatedReadingMinutes: int = 1
    publishedAt: datetime | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

    @field_validator("wordCount")
    @classmethod
    def validate_word_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("wordCount no puede ser negativo")
        return v

    @field_validator("estimatedReadingMinutes")
    @classmethod
    def validate_reading_minutes(cls, v: int) -> int:
        if v < 0:
            raise ValueError("estimatedReadingMinutes no puede ser negativo")
        return v

    @model_validator(mode="after")
    def validate_publication_rules(self) -> "News":
        if self.status == NewsStatus.draft and self.publishedAt is not None:
            raise ValueError("publishedAt debe ser nulo mientras status sea draft")
        if self.status == NewsStatus.published:
            if self.publishedAt is None:
                raise ValueError("publishedAt es obligatorio cuando status sea published")
            expected_word_count, expected_minutes = compute_reading_time(self.content)
            if self.wordCount != expected_word_count:
                raise ValueError("wordCount debe coincidir con content al publicar")
            if self.estimatedReadingMinutes != expected_minutes:
                raise ValueError(
                    "estimatedReadingMinutes debe coincidir con wordCount al publicar"
                )
        if self.aiAssistance.imageGenerated != (self.image.type == ImageType.ai_generated):
            raise ValueError(
                "aiAssistance.imageGenerated debe coincidir con image.type ai_generated"
            )
        return self

    def recompute_reading_time(self) -> None:
        self.wordCount, self.estimatedReadingMinutes = compute_reading_time(
            self.content
        )
        self.updatedAt = datetime.now(timezone.utc)

    def model_dump_mongo(self) -> dict:
        return self.model_dump(by_alias=True, mode="python")

"""Enums compartidos entre los modelos de la base de datos de noticias."""

from enum import Enum


class LocationLevel(str, Enum):
    city = "city"
    region = "region"
    country = "country"
    international = "international"


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class NewsStatus(str, Enum):
    draft = "draft"
    published = "published"


class VerificationStatus(str, Enum):
    confirmed = "confirmed"
    developing = "developing"
    insufficient_sources = "insufficient_sources"
    conflicting_sources = "conflicting_sources"


class SourceType(str, Enum):
    official = "official"
    media = "media"
    primary_source = "primary_source"
    witness = "witness"
    other = "other"


class ImageType(str, Enum):
    photograph = "photograph"
    illustration = "illustration"
    ai_generated = "ai_generated"
    ai_modified = "ai_modified"
    none = "none"


class InteractionType(str, Enum):
    opened = "opened"
    read = "read"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ResponseStrategy(str, Enum):
    database_query = "database_query"
    template = "template"
    llm = "llm"


class ResponseIntent(str, Enum):
    recent_news = "recent_news"
    regional_news = "regional_news"
    topic_news = "topic_news"
    news_detail = "news_detail"
    summarize = "summarize"
    explain = "explain"
    unsupported = "unsupported"


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class AiFeature(str, Enum):
    chat = "chat"
    summary = "summary"
    image_generation = "image_generation"
    classification = "classification"


class AuditAction(str, Enum):
    news_created = "news.created"
    news_updated = "news.updated"
    news_published = "news.published"
    image_generated = "image.generated"
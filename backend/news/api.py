"""API HTTP local para exponer noticias desde MongoDB."""

from __future__ import annotations

import os
import re
import unicodedata
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Any

from bson import ObjectId
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from pymongo.errors import DuplicateKeyError, PyMongoError

from .config import NewsDatabaseConfigurationError, get_news_settings
from .database import NewsDatabaseError, get_news_client
from .firebase_auth import (
    FirebaseAuthenticationError,
    FirebaseConfigurationError,
    FirebaseIdentity,
    verify_firebase_bearer,
)
from .models import (
    AuditAction,
    ImageType,
    LocationLevel,
    NewsStatus,
    SourceType,
    UserRole,
    VerificationStatus,
)
from .models.audit_log import AuditLog
from .models.news import (
    AiAssistance,
    GeographicScope,
    Image,
    News,
    Source,
    Verification,
)
from .models.reading_time import compute_reading_time
from .topics import TOPICS
from .user_accounts import UserAccountError, ensure_news_user

CATEGORY_IDS = set(TOPICS)
DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:8081,"
    "http://127.0.0.1:8081,"
    "http://localhost:19006,"
    "http://127.0.0.1:19006"
)


class ArticleImageResponse(BaseModel):
    src: str | None
    alt: str
    width: int
    height: int
    credit: str
    sourceUrl: str
    license: str
    type: ImageType = ImageType.none
    aiDisclosure: str | None = None


class GeographicScopeResponse(BaseModel):
    level: LocationLevel
    locationIds: list[str]


class VerificationResponse(BaseModel):
    status: VerificationStatus
    reviewedBy: str | None = None
    reviewedAt: datetime | None = None
    notes: str | None = None


class NewsArticleResponse(BaseModel):
    id: str
    slug: str
    title: str
    summary: str
    category: str
    author: str
    publishedAt: str
    body: list[str]
    readingMinutes: int
    source: str
    image: ArticleImageResponse
    topics: list[str] = Field(default_factory=list)
    geographicScope: GeographicScopeResponse | None = None
    verification: VerificationResponse | None = None
    sources: list[Source] = Field(default_factory=list)
    aiAssistance: AiAssistance = Field(default_factory=AiAssistance)


class HealthResponse(BaseModel):
    status: str
    database: str
    mongodbMode: str
    mongodbConnected: bool


class LocationResponse(BaseModel):
    id: str
    name: str
    country: str
    countryCode: str
    level: str


class AuthenticatedUserResponse(BaseModel):
    id: str
    firebaseUid: str
    email: str
    displayName: str
    photoUrl: str
    role: UserRole


class AdminNewsCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    slug: str = Field(default="", max_length=160)
    summary: str = Field(min_length=1, max_length=600)
    content: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    locationId: str = Field(min_length=24, max_length=24)
    status: NewsStatus = NewsStatus.published
    verificationStatus: VerificationStatus = VerificationStatus.confirmed
    sourceName: str | None = None
    sourceUrl: str | None = None
    sourceType: SourceType = SourceType.other
    imageUrl: str | None = None
    imageAlt: str | None = None
    imageCredit: str | None = None
    imageRights: str | None = None

    @field_validator(
        "title",
        "slug",
        "summary",
        "content",
        "topic",
        "locationId",
        "sourceName",
        "sourceUrl",
        "imageUrl",
        "imageAlt",
        "imageCredit",
        "imageRights",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value):
        if value is None:
            return value
        return str(value).strip()

    @field_validator("keywords", mode="before")
    @classmethod
    def normalize_keywords(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_source_pair(self) -> AdminNewsCreateRequest:
        has_source_name = bool(self.sourceName)
        has_source_url = bool(self.sourceUrl)
        if has_source_name != has_source_url:
            raise ValueError("sourceName y sourceUrl deben enviarse juntos.")
        return self


def _allowed_origins() -> list[str]:
    raw_value = os.getenv("NEWS_API_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def _isoformat(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _body_from_content(content: str) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in content.split("\n\n")]
    paragraphs = [paragraph for paragraph in paragraphs if paragraph]
    if paragraphs:
        return paragraphs
    return [content.strip()] if content.strip() else []


def _category_from_topics(topics: list[Any]) -> str:
    for topic in topics:
        normalized = str(topic).strip().lower()
        if normalized in CATEGORY_IDS:
            return normalized
    return "actualidad"


def _image_from_document(document: dict[str, Any]) -> ArticleImageResponse:
    image = document.get("image") or {}
    title = str(document.get("title") or "noticia")
    credit = image.get("credit") or "Imagen ilustrativa pendiente"
    return ArticleImageResponse(
        src=image.get("url"),
        type=image.get("type") or ImageType.none,
        aiDisclosure=image.get("aiDisclosure"),
        alt=image.get("alt") or f"Imagen no disponible para {title}.",
        width=960,
        height=540,
        credit=credit,
        sourceUrl="",
        license=image.get("rights")
        or "Placeholder local; requiere reemplazo por foto con licencia verificada.",
    )


def _location_to_response(document: dict[str, Any]) -> LocationResponse:
    return LocationResponse(
        id=str(document["_id"]),
        name=str(document["name"]),
        country=str(document["country"]),
        countryCode=str(document["countryCode"]),
        level=str(document["level"]),
    )


def _author_name(database, author_id: ObjectId | None) -> str:
    if author_id is None:
        return "Redacción AI News"
    author = database["users"].find_one({"_id": author_id}, {"displayName": 1})
    return (
        str(author.get("displayName"))
        if author and author.get("displayName")
        else "Redacción AI News"
    )


def document_to_article(database, document: dict[str, Any]) -> NewsArticleResponse:
    sources = document.get("sources") or []
    first_source = sources[0] if sources else {}
    return NewsArticleResponse(
        id=str(document["_id"]),
        slug=str(document["slug"]),
        title=str(document["title"]),
        summary=str(document["summary"]),
        category=_category_from_topics(document.get("topics") or []),
        author=_author_name(database, document.get("authorId")),
        publishedAt=_isoformat(document.get("publishedAt")),
        body=_body_from_content(str(document.get("content") or "")),
        readingMinutes=int(document.get("estimatedReadingMinutes") or 1),
        source=str(first_source.get("name") or "Base local"),
        image=_image_from_document(document),
        topics=document.get("topics") or [],
        geographicScope=(
            GeographicScopeResponse(
                level=document["geographicScope"]["level"],
                locationIds=[
                    str(value) for value in document["geographicScope"]["locationIds"]
                ],
            )
            if document.get("geographicScope")
            else None
        ),
        verification=(
            VerificationResponse(
                **{
                    **document["verification"],
                    "reviewedBy": str(document["verification"]["reviewedBy"])
                    if document["verification"].get("reviewedBy")
                    else None,
                }
            )
            if document.get("verification")
            else None
        ),
        sources=[Source.model_validate(source) for source in sources],
        aiAssistance=AiAssistance.model_validate(document.get("aiAssistance") or {}),
    )


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    without_marks = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", without_marks).strip("-").lower()
    return slug or "noticia"


def _parse_object_id(value: str, field_name: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=400, detail=f"{field_name} debe ser ObjectId válido."
        )
    return ObjectId(value)


def _authenticated_firebase_identity(
    request: Request, authorization: str | None
) -> FirebaseIdentity:
    try:
        return verify_firebase_bearer(
            authorization,
            request.app.state.news_settings.firebase_project_id,
        )
    except FirebaseAuthenticationError as error:
        raise HTTPException(status_code=401, detail="Firebase ID token inválido o vencido.") from error
    except FirebaseConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


def get_authenticated_user(
    request: Request, authorization: str | None = Header(default=None)
) -> dict[str, Any]:
    identity = _authenticated_firebase_identity(request, authorization)
    settings = request.app.state.news_settings
    database = request.app.state.news_client[settings.mongodb_database]
    try:
        return ensure_news_user(
            database,
            identity,
            default_location_code=os.getenv("NEWS_CHAT_DEFAULT_LOCATION_CODE", "GT"),
        )
    except UserAccountError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except PyMongoError as error:
        raise HTTPException(
            status_code=503, detail="No fue posible resolver tu usuario en MongoDB."
        ) from error


AuthenticatedUser = Annotated[dict[str, Any], Depends(get_authenticated_user)]


def _source_from_request(
    payload: AdminNewsCreateRequest, now: datetime
) -> list[Source]:
    if not payload.sourceName or not payload.sourceUrl:
        return []
    return [
        Source(
            name=payload.sourceName,
            url=payload.sourceUrl,
            sourceType=payload.sourceType,
            publishedAt=None,
            accessedAt=now,
            supports=None,
        )
    ]


def _image_from_request(payload: AdminNewsCreateRequest) -> Image:
    if not payload.imageUrl:
        return Image(
            url=None,
            alt=None,
            type=ImageType.none,
            credit=None,
            rights=None,
            aiDisclosure=None,
        )
    return Image(
        url=payload.imageUrl,
        alt=payload.imageAlt or payload.title,
        type=ImageType.photograph,
        credit=payload.imageCredit,
        rights=payload.imageRights,
        aiDisclosure=None,
    )


def _create_news_document(
    database,
    payload: AdminNewsCreateRequest,
    actor: dict[str, Any],
) -> dict[str, Any]:
    location_id = _parse_object_id(payload.locationId, "locationId")
    location = database["locations"].find_one(
        {"_id": location_id, "active": True},
        {"level": 1},
    )
    if not location:
        raise HTTPException(
            status_code=400, detail="La ubicación seleccionada no existe."
        )

    now = datetime.now(timezone.utc)
    author_id = actor["_id"]
    content = payload.content.strip()
    word_count, reading_minutes = compute_reading_time(content)
    published_at = now if payload.status == NewsStatus.published else None
    slug = _slugify(payload.slug or payload.title)
    topic = payload.topic.strip().lower()
    keywords = sorted(
        {item.strip().lower() for item in payload.keywords if item.strip()}
    )
    if topic not in keywords:
        keywords.insert(0, topic)

    raw_level = location.get("level") or LocationLevel.country.value
    location_level = (
        raw_level
        if isinstance(raw_level, LocationLevel)
        else LocationLevel(str(raw_level))
    )

    news = News(
        slug=slug,
        title=payload.title,
        summary=payload.summary,
        content=content,
        authorId=author_id,
        status=payload.status,
        topics=[topic],
        keywords=keywords,
        geographicScope=GeographicScope(
            level=location_level,
            locationIds=[location_id],
        ),
        verification=Verification(
            status=payload.verificationStatus,
            reviewedBy=author_id,
            reviewedAt=now,
            notes="Creada desde el panel administrativo autenticado con Firebase.",
        ),
        sources=_source_from_request(payload, now),
        image=_image_from_request(payload),
        aiAssistance=AiAssistance(humanReviewed=True),
        wordCount=word_count,
        estimatedReadingMinutes=reading_minutes,
        publishedAt=published_at,
        createdAt=now,
        updatedAt=now,
    )
    document = news.model_dump_mongo()
    try:
        database["news"].insert_one(document)
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=409, detail="Ya existe una noticia con ese slug."
        ) from error

    audit = AuditLog(
        actorId=author_id,
        action=AuditAction.news_created,
        entityId=document["_id"],
        details={"slug": slug, "status": payload.status.value},
        createdAt=now,
    )
    database["auditLogs"].insert_one(audit.model_dump_mongo())
    return document


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_news_settings()
    client = get_news_client(settings)
    application.state.news_settings = settings
    application.state.news_client = client
    try:
        yield
    finally:
        client.close()


def create_app() -> FastAPI:
    application = FastAPI(
        title="AI Assisted News API",
        version="0.1.0",
        description="API local para servir noticias desde MongoDB.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @application.get("/health", response_model=HealthResponse)
    async def health(request: Request) -> HealthResponse:
        settings = request.app.state.news_settings
        database = request.app.state.news_client[settings.mongodb_database]
        connected = False
        try:
            database.command("ping")
            connected = True
        except PyMongoError:
            connected = False
        return HealthResponse(
            status="ok" if connected else "degraded",
            database=settings.mongodb_database,
            mongodbMode=settings.mongodb_mode,
            mongodbConnected=connected,
        )

    @application.get("/news", response_model=list[NewsArticleResponse])
    async def news_feed(request: Request) -> list[NewsArticleResponse]:
        settings = request.app.state.news_settings
        database = request.app.state.news_client[settings.mongodb_database]
        try:
            cursor = (
                database["news"]
                .find({"status": "published"})
                .sort("publishedAt", -1)
                .limit(50)
            )
            return [document_to_article(database, document) for document in cursor]
        except PyMongoError as error:
            raise HTTPException(
                status_code=503,
                detail="No fue posible leer noticias desde MongoDB.",
            ) from error

    @application.get("/locations", response_model=list[LocationResponse])
    async def locations(request: Request) -> list[LocationResponse]:
        settings = request.app.state.news_settings
        database = request.app.state.news_client[settings.mongodb_database]
        try:
            cursor = (
                database["locations"]
                .find({"active": True})
                .sort([("country", 1), ("name", 1)])
            )
            return [_location_to_response(document) for document in cursor]
        except PyMongoError as error:
            raise HTTPException(
                status_code=503,
                detail="No fue posible leer ubicaciones desde MongoDB.",
            ) from error

    @application.get("/news/{slug}", response_model=NewsArticleResponse)
    async def news_detail(slug: str, request: Request) -> NewsArticleResponse:
        settings = request.app.state.news_settings
        database = request.app.state.news_client[settings.mongodb_database]
        try:
            document = database["news"].find_one({"slug": slug, "status": "published"})
        except PyMongoError as error:
            raise HTTPException(
                status_code=503,
                detail="No fue posible leer la noticia desde MongoDB.",
            ) from error
        if not document:
            raise HTTPException(status_code=404, detail="Noticia no encontrada.")
        return document_to_article(database, document)

    @application.get("/auth/me", response_model=AuthenticatedUserResponse)
    async def current_user(user: AuthenticatedUser):
        return AuthenticatedUserResponse(
            id=str(user["_id"]),
            firebaseUid=user["firebaseUid"],
            email=user["email"],
            displayName=user["displayName"],
            photoUrl=user["photoUrl"],
            role=user["role"],
        )

    @application.post(
        "/admin/news", response_model=NewsArticleResponse, status_code=201
    )
    async def admin_create_news(
        payload: AdminNewsCreateRequest,
        request: Request,
        user: AuthenticatedUser,
    ) -> NewsArticleResponse:
        if user.get("role") != UserRole.admin and user.get("role") != UserRole.admin.value:
            raise HTTPException(status_code=403, detail="Se requiere rol administrador.")
        settings = request.app.state.news_settings
        database = request.app.state.news_client[settings.mongodb_database]
        try:
            document = _create_news_document(database, payload, user)
        except HTTPException:
            raise
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except PyMongoError as error:
            raise HTTPException(
                status_code=503,
                detail="No fue posible crear la noticia en MongoDB.",
            ) from error
        return document_to_article(database, document)

    @application.exception_handler(NewsDatabaseConfigurationError)
    async def configuration_error_handler(_request: Request, error: Exception):
        return JSONResponse(status_code=503, content={"detail": str(error)})

    @application.exception_handler(NewsDatabaseError)
    async def database_error_handler(_request: Request, error: Exception):
        return JSONResponse(status_code=503, content={"detail": str(error)})

    return application


app = create_app()

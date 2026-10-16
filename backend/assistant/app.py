from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from news.auth import AdminAuthenticationError, authorized_admin_username
from news.config import get_news_settings
from news.secret_loader import SecretFileError
from pymongo.errors import PyMongoError

from .config import ChatbotConfigurationError, api_key_is_configured, get_settings
from .models import ChatRequest, ChatResponse, HealthResponse
from .news_chat import schemas as news_schemas
from .news_chat.database import open_news_client
from .news_chat.service import NewsChatRequestError, NewsChatService
from .providers.openai import OpenAIChatProvider
from .providers.stub import StubChatProvider
from .repositories.base import EmptyContextRepository
from .repositories.mongo import MongoContextRepository
from .service import ChatbotServiceError, ChatService


def _build_provider(settings):
    if settings.provider == "stub":
        return StubChatProvider()
    return OpenAIChatProvider(settings)


class _UnavailableProvider:
    """Difiere el error de configuración al turno para que FastAPI valide antes el cuerpo."""

    def __init__(self, error: ChatbotConfigurationError) -> None:
        self._error = error

    async def generate(self, **_options):
        raise self._error


def _provider_or_unavailable(settings):
    try:
        return _build_provider(settings)
    except ChatbotConfigurationError as error:
        return _UnavailableProvider(error)


async def get_chat_service(request: Request) -> ChatService:
    settings = get_settings()
    return ChatService(
        settings, _provider_or_unavailable(settings), request.app.state.context_repository
    )


ChatServiceDependency = Annotated[ChatService, Depends(get_chat_service)]


async def get_news_chat_service(request: Request) -> NewsChatService:
    settings = get_settings()
    return NewsChatService(
        settings,
        lambda: _build_provider(settings),
        request.app.state.news_database,
    )


NewsChatServiceDependency = Annotated[NewsChatService, Depends(get_news_chat_service)]


class NewsDatabaseRepository:
    """Ciclo de vida de la conexión a ai_assisted_news en modo news."""

    def __init__(self) -> None:
        self.connected = False
        self._client, database_name = open_news_client()
        self.database = self._client[database_name]

    async def connect(self) -> None:
        await self.database.command("ping")
        self.connected = True

    async def close(self) -> None:
        await self._client.close()
        self.connected = False


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    if settings.news_mode:
        repository = NewsDatabaseRepository()
        application.state.news_database = repository.database
    else:
        repository = (
            MongoContextRepository(settings)
            if settings.mongodb_configured
            else EmptyContextRepository()
        )
    application.state.context_repository = repository
    application.state.mongodb_error = None
    try:
        await repository.connect()
    except Exception as error:
        application.state.mongodb_error = str(error)
        if settings.mongodb_required:
            raise
    yield
    await repository.close()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Modular Chatbot API",
        version="2.0.0",
        description="Chatbot modular con prompt externo y contexto opcional desde MongoDB.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @application.exception_handler(ChatbotConfigurationError)
    async def configuration_error_handler(
        _request: Request, error: ChatbotConfigurationError
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(error)})

    @application.get("/health", response_model=HealthResponse)
    async def health(request: Request) -> HealthResponse:
        current_settings = get_settings()
        mongo_connected = request.app.state.context_repository.connected
        healthy = not current_settings.mongodb_required or mongo_connected
        return HealthResponse(
            status="ok" if healthy else "degraded",
            provider=current_settings.provider,
            api_key_configured=api_key_is_configured(),
            mongodb_configured=current_settings.mongodb_configured,
            mongodb_connected=mongo_connected,
            prompt_version=current_settings.prompt_version,
        )

    if settings.news_mode:

        @application.post("/chat", response_model=news_schemas.ChatReply)
        async def news_chat(
            chat_request: news_schemas.ChatRequest,
            request: Request,
            service: NewsChatServiceDependency,
        ) -> news_schemas.ChatReply:
            try:
                admin_username = None
                if chat_request.user.id.startswith(("admin:", "local-admin:")):
                    admin_username = authorized_admin_username(
                        request.headers.get("Authorization", ""), get_news_settings()
                    )
                return await service.reply(chat_request, admin_username=admin_username)
            except AdminAuthenticationError as error:
                raise HTTPException(
                    status_code=401, detail="Token admin inválido o requerido."
                ) from error
            except SecretFileError as error:
                raise HTTPException(
                    status_code=503, detail="La autenticación admin no está configurada."
                ) from error
            except ChatbotConfigurationError as error:
                raise HTTPException(status_code=503, detail=str(error)) from error
            except NewsChatRequestError as error:
                raise HTTPException(status_code=error.status_code, detail=str(error)) from error
            except PyMongoError as error:
                raise HTTPException(
                    status_code=503, detail="No fue posible leer la base de noticias."
                ) from error

        return application

    @application.post("/chat", response_model=ChatResponse)
    async def chat(chat_request: ChatRequest, service: ChatServiceDependency) -> ChatResponse:
        try:
            return await service.reply(chat_request)
        except ChatbotConfigurationError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except ChatbotServiceError as error:
            raise HTTPException(status_code=error.status_code, detail=str(error)) from error

    return application


app = create_app()

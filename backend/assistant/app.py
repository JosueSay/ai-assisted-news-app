from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import ChatbotConfigurationError, api_key_is_configured, get_settings
from .models import ChatRequest, ChatResponse, HealthResponse
from .providers.openai import OpenAIChatProvider
from .providers.stub import StubChatProvider
from .repositories.base import EmptyContextRepository
from .repositories.mongo import MongoContextRepository
from .service import ChatbotServiceError, ChatService


def _build_provider(settings):
    if settings.provider == "stub":
        return StubChatProvider()
    return OpenAIChatProvider(settings)


async def get_chat_service(request: Request) -> ChatService:
    settings = get_settings()
    return ChatService(settings, _build_provider(settings), request.app.state.context_repository)


ChatServiceDependency = Annotated[ChatService, Depends(get_chat_service)]


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
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
        allow_headers=["Content-Type"],
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

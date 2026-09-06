from .config import Settings
from .models import ChatRequest, ChatResponse
from .prompts import load_system_prompt
from .providers.base import ChatProvider
from .providers.openai import OpenAIProviderError
from .repositories.base import ContextRepository, ContextRepositoryError


class ChatbotServiceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class ChatService:
    def __init__(
        self,
        settings: Settings,
        provider: ChatProvider,
        context_repository: ContextRepository,
    ) -> None:
        self._settings = settings
        self._provider = provider
        self._context_repository = context_repository

    async def reply(self, request: ChatRequest) -> ChatResponse:
        context: dict[str, object] = {}
        if request.user_id:
            try:
                context = await self._context_repository.get_context(request.user_id)
            except ContextRepositoryError as error:
                raise ChatbotServiceError(str(error), status_code=503) from error

        try:
            response = await self._provider.generate(
                instructions=load_system_prompt(self._settings),
                message=request.message,
                previous_response_id=request.previous_response_id,
                context=context,
                user_id=request.user_id,
            )
        except OpenAIProviderError as error:
            raise ChatbotServiceError(str(error), error.status_code) from error

        return ChatResponse(
            message=response.message,
            response_id=response.response_id,
            model=response.model,
        )

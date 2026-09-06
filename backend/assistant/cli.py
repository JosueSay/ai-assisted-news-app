import asyncio

from .config import ChatbotConfigurationError, get_settings
from .models import ChatRequest
from .providers.openai import OpenAIChatProvider
from .providers.stub import StubChatProvider
from .repositories.base import EmptyContextRepository
from .repositories.mongo import MongoContextRepository
from .service import ChatbotServiceError, ChatService


async def main() -> None:
    settings = get_settings()
    repository = (
        MongoContextRepository(settings)
        if settings.mongodb_configured
        else EmptyContextRepository()
    )
    try:
        await repository.connect()
        provider = (
            StubChatProvider()
            if settings.provider == "stub"
            else OpenAIChatProvider(settings)
        )
    except ChatbotConfigurationError as error:
        print(f"Configuración incompleta: {error}")
        await repository.close()
        return

    previous_response_id: str | None = None
    print("El asistente está listo. Escribí 'salir' para terminar.\n")
    try:
        while True:
            message = input("Vos: ").strip()
            if message.lower() in {"salir", "exit", "quit"}:
                break
            if not message:
                continue
            try:
                response = await ChatService(settings, provider, repository).reply(
                    ChatRequest(message=message, previous_response_id=previous_response_id)
                )
            except ChatbotServiceError as error:
                print(f"Asistente: {error}\n")
                continue
            previous_response_id = response.response_id
            print(f"Asistente: {response.message}\n")
    finally:
        await repository.close()


if __name__ == "__main__":
    asyncio.run(main())

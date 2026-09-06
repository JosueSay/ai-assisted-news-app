from uuid import uuid4

from .base import ProviderResponse


class StubChatProvider:
    """Proveedor determinista para desarrollo y smoke tests; nunca llama a OpenAI."""

    async def generate(
        self,
        *,
        instructions: str,
        message: str,
        previous_response_id: str | None,
        context: dict[str, object],
        user_id: str | None,
    ) -> ProviderResponse:
        del instructions, previous_response_id, user_id
        context_status = "con contexto" if context else "sin contexto"
        return ProviderResponse(
            message=f"[stub {context_status}] Respuesta para: {message}",
            response_id=f"stub_{uuid4().hex}",
            model="stub",
        )

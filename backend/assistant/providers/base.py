from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResponse:
    message: str
    response_id: str
    model: str
    # Uso reportado por el proveedor; None cuando no lo informa.
    input_tokens: int | None = None
    output_tokens: int | None = None


class ChatProvider(Protocol):
    async def generate(
        self,
        *,
        instructions: str,
        message: str,
        previous_response_id: str | None,
        context: dict[str, object],
        user_id: str | None,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResponse: ...

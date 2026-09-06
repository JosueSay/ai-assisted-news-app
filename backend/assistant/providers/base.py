from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResponse:
    message: str
    response_id: str
    model: str


class ChatProvider(Protocol):
    async def generate(
        self,
        *,
        instructions: str,
        message: str,
        previous_response_id: str | None,
        context: dict[str, object],
        user_id: str | None,
    ) -> ProviderResponse: ...

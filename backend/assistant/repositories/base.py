from typing import Protocol


class ContextRepositoryError(RuntimeError):
    """No fue posible obtener el contexto del usuario."""


class ContextRepository(Protocol):
    connected: bool

    async def connect(self) -> None: ...

    async def close(self) -> None: ...

    async def get_context(self, user_id: str) -> dict[str, object]: ...


class EmptyContextRepository:
    connected = False

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def get_context(self, user_id: str) -> dict[str, object]:
        del user_id
        return {}

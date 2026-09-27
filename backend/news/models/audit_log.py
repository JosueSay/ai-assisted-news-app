"""Modelo AuditLog — Registro de acciones administrativas sobre noticias."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from . import AuditAction


class AuditLog(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    actorId: ObjectId
    action: AuditAction
    entityType: str = "news"
    entityId: ObjectId
    details: dict = Field(default_factory=dict)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

    @field_validator("entityType")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        if v != "news":
            raise ValueError("entityType debe ser 'news'")
        return v

    def model_dump_mongo(self) -> dict:
        return self.model_dump(by_alias=True, mode="python")
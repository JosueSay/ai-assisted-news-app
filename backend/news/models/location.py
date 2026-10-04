"""Modelo Location — Catálogo global precargado de ubicaciones."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import BaseModel, Field

from . import LocationLevel


class Location(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    name: str
    city: str | None = None
    region: str | None = None
    country: str
    countryCode: str
    level: LocationLevel
    active: bool = True
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

    def model_dump_mongo(self) -> dict:
        return self.model_dump(by_alias=True, mode="python")
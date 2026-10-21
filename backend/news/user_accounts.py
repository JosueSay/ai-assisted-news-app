"""Resolución idempotente de usuarios desde una identidad Firebase verificada."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from .firebase_auth import FirebaseIdentity
from .models import UserRole
from .models.user import Onboarding, User


class UserAccountError(RuntimeError):
    """No se puede preparar el perfil de noticias para una identidad autenticada."""


def _default_location_id(database, default_location_code: str) -> ObjectId:
    locations = database["locations"]
    location = locations.find_one(
        {"countryCode": default_location_code, "active": True}, {"_id": 1}
    ) or locations.find_one({"active": True}, {"_id": 1})
    if location is None:
        raise UserAccountError("No hay ubicaciones activas. Ejecuta make db-seed-catalog.")
    return location["_id"]


async def _default_location_id_async(database, default_location_code: str) -> ObjectId:
    locations = database["locations"]
    location = await locations.find_one(
        {"countryCode": default_location_code, "active": True}, {"_id": 1}
    ) or await locations.find_one({"active": True}, {"_id": 1})
    if location is None:
        raise UserAccountError("No hay ubicaciones activas. Ejecuta make db-seed-catalog.")
    return location["_id"]


def _profile_updates(identity: FirebaseIdentity, now: datetime) -> dict[str, Any]:
    changes: dict[str, Any] = {"lastLoginAt": now, "updatedAt": now}
    # Preserve existing profile values when an anonymous token has no such claim.
    if identity.email:
        changes["email"] = identity.email
    if identity.display_name:
        changes["displayName"] = identity.display_name
    if identity.photo_url:
        changes["photoUrl"] = identity.photo_url
    return changes


def _new_user(identity: FirebaseIdentity, location_id: ObjectId, now: datetime) -> dict:
    return User(
        firebaseUid=identity.uid,
        email=identity.email,
        displayName=identity.display_name or "Invitado",
        photoUrl=identity.photo_url,
        role=UserRole.user,
        simulatedLocationId=location_id,
        onboarding=Onboarding(),
        createdAt=now,
        updatedAt=now,
        lastLoginAt=now,
    ).model_dump_mongo()


def ensure_news_user(
    database,
    identity: FirebaseIdentity,
    *,
    default_location_code: str = "GT",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Busca/crea un usuario sin cambiar su rol, preferencias o ubicación existente."""
    current_time = now or datetime.now(timezone.utc)
    users = database["users"]
    existing = users.find_one({"firebaseUid": identity.uid})
    if existing is None:
        document = _new_user(
            identity,
            _default_location_id(database, default_location_code),
            current_time,
        )
        try:
            users.insert_one(document)
            return document
        except DuplicateKeyError:
            existing = users.find_one({"firebaseUid": identity.uid})
            if existing is None:
                raise

    changes = _profile_updates(identity, current_time)
    users.update_one({"_id": existing["_id"]}, {"$set": changes})
    return {**existing, **changes}


async def ensure_news_user_async(
    database,
    identity: FirebaseIdentity,
    *,
    default_location_code: str = "GT",
    now: datetime | None = None,
) -> dict[str, Any]:
    """AsyncMongoClient counterpart used by the news chat service."""
    current_time = now or datetime.now(timezone.utc)
    users = database["users"]
    existing = await users.find_one({"firebaseUid": identity.uid})
    if existing is None:
        document = _new_user(
            identity,
            await _default_location_id_async(database, default_location_code),
            current_time,
        )
        try:
            await users.insert_one(document)
            return document
        except DuplicateKeyError:
            existing = await users.find_one({"firebaseUid": identity.uid})
            if existing is None:
                raise

    changes = _profile_updates(identity, current_time)
    await users.update_one({"_id": existing["_id"]}, {"$set": changes})
    return {**existing, **changes}

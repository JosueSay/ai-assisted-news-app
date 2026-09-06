import asyncio
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING, AsyncMongoClient
from pymongo.errors import PyMongoError

from ..config import Settings
from .base import ContextRepositoryError

Document = dict[str, Any]

NOVU_PRODUCT_CATALOG = [
    {
        "id": "personal_goal",
        "name": "Plan personal",
        "use_when": "La persona tiene una meta individual y necesita aportes flexibles.",
    },
    {
        "id": "group_challenge",
        "name": "Reto grupal",
        "use_when": "La motivación compartida puede ayudar a sostener la constancia.",
    },
    {
        "id": "family_fund",
        "name": "Fondo grupal",
        "use_when": "Hay imprevistos o apoyo familiar que conviene planificar juntos.",
    },
]


class MongoContextRepository:
    connected = False

    def __init__(
        self,
        settings: Settings,
        client: AsyncMongoClient[Document] | None = None,
    ) -> None:
        if not settings.mongodb_uri:
            raise ValueError("MongoContextRepository requiere MONGODB_URI.")
        self._settings = settings
        self._client = client or AsyncMongoClient(
            settings.mongodb_uri,
            appname="assistant-service",
            serverSelectionTimeoutMS=5_000,
            uuidRepresentation="standard",
        )
        self._database = self._client[settings.mongodb_database]

    async def connect(self) -> None:
        try:
            await self._database.command("ping")
        except PyMongoError as error:
            raise ContextRepositoryError("No fue posible conectar con MongoDB.") from error
        self.connected = True

    async def close(self) -> None:
        await self._client.close()
        self.connected = False

    def _user_id(self, raw_user_id: str) -> str | ObjectId:
        if self._settings.mongodb_user_id_type == "string":
            return raw_user_id
        if not ObjectId.is_valid(raw_user_id):
            raise ContextRepositoryError(
                "user_id debe ser un ObjectId válido para la configuración actual."
            )
        return ObjectId(raw_user_id)

    async def get_context(self, user_id: str) -> dict[str, object]:
        try:
            if self._settings.mongodb_context_mode == "novu":
                return await self._get_novu_context(self._user_id(user_id))
            return await self._get_projection_context(self._user_id(user_id))
        except ContextRepositoryError:
            raise
        except PyMongoError as error:
            raise ContextRepositoryError("No fue posible leer el contexto en MongoDB.") from error

    async def _get_projection_context(self, user_id: str | ObjectId) -> dict[str, object]:
        document = await self._database[
            self._settings.mongodb_context_collection
        ].find_one(
            {"user_id": user_id},
            {"_id": 0, "user_id": 0, "schema_version": 0, "updated_at": 0},
        )
        if not document:
            return {}
        context = document.get("context")
        return context if isinstance(context, dict) else {}

    async def _get_novu_context(self, user_id: str | ObjectId) -> dict[str, object]:
        user_task = self._database.users.find_one(
            {"_id": user_id},
            {"profile.first_name": 1, "profile.locale": 1, "profile.timezone": 1, "status": 1},
        )
        savings_task = self._database.savings_profiles.find_one(
            {"user_id": user_id}, {"_id": 0, "user_id": 0}
        )
        goals_task = (
            self._database.goals.find(
                {"owner_id": user_id, "deleted_at": None},
                {
                    "_id": 0,
                    "name": 1,
                    "category": 1,
                    "target_amount_minor": 1,
                    "saved_amount_minor": 1,
                    "recommendation": 1,
                    "target_date": 1,
                    "status": 1,
                    "currency": 1,
                },
            )
            .sort("updated_at", DESCENDING)
            .limit(20)
            .to_list(length=20)
        )
        contributions_task = (
            self._database.contributions.find(
                {"user_id": user_id, "status": {"$in": ["posted", "reversed"]}},
                {
                    "_id": 0,
                    "amount_minor": 1,
                    "currency": 1,
                    "description": 1,
                    "status": 1,
                    "occurred_at": 1,
                    "destination": 1,
                },
            )
            .sort("occurred_at", DESCENDING)
            .limit(50)
            .to_list(length=50)
        )
        withdrawals_task = (
            self._database.withdrawal_requests.find(
                {"requester_id": user_id, "status": {"$in": ["approved", "executed"]}},
                {
                    "_id": 0,
                    "amount_minor": 1,
                    "currency": 1,
                    "reason": 1,
                    "status": 1,
                    "source": 1,
                    "created_at": 1,
                    "executed_at": 1,
                },
            )
            .sort("created_at", DESCENDING)
            .limit(50)
            .to_list(length=50)
        )
        activities_task = (
            self._database.activities.find(
                {"user_id": user_id},
                {"_id": 0, "title": 1, "type": 1, "amount_minor": 1, "occurred_at": 1},
            )
            .sort("occurred_at", DESCENDING)
            .limit(30)
            .to_list(length=30)
        )
        user, savings, goals, contributions, withdrawals, activities = await asyncio.gather(
            user_task,
            savings_task,
            goals_task,
            contributions_task,
            withdrawals_task,
            activities_task,
        )
        if not user:
            return {}
        profile = user.get("profile", {})
        return {
            "person": {
                "first_name": profile.get("first_name"),
                "locale": profile.get("locale", "es-GT"),
                "timezone": profile.get("timezone", "America/Guatemala"),
                "account_status": user.get("status"),
            },
            "savings_profile": savings,
            "goals": goals,
            "recent_contributions": contributions,
            "recent_withdrawals": withdrawals,
            "recent_activity": activities,
            "product_catalog": NOVU_PRODUCT_CATALOG,
            "context_limits": {
                "contributions_returned": len(contributions),
                "withdrawals_returned": len(withdrawals),
                "activities_returned": len(activities),
                "history_is_recent_sample": True,
            },
        }

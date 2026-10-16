"""Turno de chat del assistant en modo news.

Cumple docs/design/database/04-criterios-de-chat-y-costos.md:

- Usa el proveedor del assistant (`llm`) con las noticias publicadas como contexto
  autorizado, si el proveedor es real, los precios están configurados y queda
  presupuesto. Cada llamada real queda registrada en `aiUsage`.
- Sin proveedor real, sin presupuesto o si la IA falla, responde con los campos de
  las noticias (`database_query`) y no consume presupuesto.
- Las peticiones fuera del dominio se responden con `template` y no llaman a la IA.
- La conversación vive embebida en `chatSessions` y expira con la sesión; el
  historial se envía al modelo en cada turno en lugar de guardarse en OpenAI.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId
from news.identity import admin_author_id, admin_external_id
from news.models import (
    AiFeature,
    ConfidenceLevel,
    MessageRole,
    ResponseIntent,
    ResponseStrategy,
    UserRole,
)
from news.models.ai_usage import AiUsage
from news.models.chat_session import ChatSession, Message, ResponseMetadata
from news.models.user import User
from news.presentation import topic_label
from pymongo.errors import DuplicateKeyError

from ..config import ChatbotConfigurationError, Settings
from ..prompts import load_system_prompt
from ..providers.base import ChatProvider
from ..providers.openai import OpenAIProviderError
from .conversation import resolve_message
from .intent import ClassifiedQuery
from .retrieval import (
    ELABORATION_LIMIT,
    LISTING_LIMIT,
    Confidence,
    compute_confidence,
    count_news,
    find_published_news,
    find_published_news_by_ids,
    format_detail,
    format_listing,
    news_context,
    news_filters,
    published_news_matching,
    recent_published_news,
    resolve_news_locations,
    select_news,
    verification_status,
)
from .schemas import ChatAssistantMessage, ChatCitedNews, ChatReply, ChatRequest

HISTORY_MESSAGES_FOR_LLM = 10
# Estimación conservadora de tokens por carácter para el chequeo de presupuesto.
CHARS_PER_TOKEN_ESTIMATE = 3

LISTING_INTENTS = {
    ResponseIntent.recent_news,
    ResponseIntent.regional_news,
    ResponseIntent.topic_news,
}


UNSUPPORTED_REPLY = (
    "Solo puedo ayudarte con las noticias publicadas en AI News. Puedes pedirme las "
    "últimas noticias, noticias de un país o de un tema, el detalle de una noticia, "
    "o que resuma o explique una noticia."
)
NOT_FOUND_REPLY = (
    "No encontré noticias publicadas que coincidan con tu consulta. "
    "Prueba con otro país, otro tema o pide las últimas noticias."
)


class NewsChatRequestError(RuntimeError):
    """La petición de chat no puede atenderse."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class _Plan:
    """Qué noticias respaldan la respuesta y cómo se respondería sin IA."""

    intent: ResponseIntent
    cited: list[dict[str, Any]] = field(default_factory=list)
    database_reply: str = ""
    include_content: bool = False
    database_only: bool = False
    matching_count: int | None = None


@dataclass
class _Answer:
    content: str
    strategy: ResponseStrategy
    intent: ResponseIntent
    cited: list[dict[str, Any]]
    confidence: Confidence


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _plain(value: Any) -> str:
    return str(getattr(value, "value", value))


def _optional_object_id(value: str | None, field_name: str) -> ObjectId | None:
    if value is None:
        return None
    if not ObjectId.is_valid(value):
        raise NewsChatRequestError(f"{field_name} debe ser ObjectId válido.", 400)
    return ObjectId(value)


class NewsChatService:
    def __init__(
        self,
        settings: Settings,
        provider_factory: Callable[[], ChatProvider],
        database,
        *,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._settings = settings
        self._provider_factory = provider_factory
        self._db = database
        self._clock = clock

    # ------------------------------------------------------------------
    # Flujo principal
    # ------------------------------------------------------------------

    async def reply(self, request: ChatRequest, *, admin_username: str | None = None) -> ChatReply:
        now = self._clock()
        session_id = _optional_object_id(request.sessionId, "sessionId")
        news_id = _optional_object_id(request.newsId, "newsId")
        location_id = _optional_object_id(request.locationId, "locationId")

        user = await self._ensure_user(request, location_id, now, admin_username=admin_username)
        session = await self._load_or_create_session(session_id, user, now)

        news_document = None
        if news_id is not None:
            news_document = await find_published_news(self._db, news_id)
            if news_document is None:
                raise NewsChatRequestError("La noticia no existe o no está publicada.", 404)

        query = resolve_message(
            request.message,
            session.get("messages") or [],
            has_news_context=news_document is not None,
        )
        plan = await self._plan(query, news_document, user, session)
        answer = await self._answer(request, plan, news_document, user, session)

        assistant_created_at = self._clock()
        metadata = ResponseMetadata(
            strategy=answer.strategy,
            intent=answer.intent,
            citedNewsIds=[document["_id"] for document in answer.cited],
            confidence=answer.confidence.level,
            uncertainty=answer.confidence.uncertainty,
            aiUsed=answer.strategy == ResponseStrategy.llm,
        )
        messages = [
            Message(role=MessageRole.user, content=request.message, createdAt=now),
            Message(
                role=MessageRole.assistant,
                content=answer.content,
                responseMetadata=metadata,
                createdAt=assistant_created_at,
            ),
        ]
        await self._db["chatSessions"].update_one(
            {"_id": session["_id"]},
            {
                "$push": {
                    "messages": {
                        "$each": [message.model_dump(mode="python") for message in messages]
                    }
                }
            },
        )

        return ChatReply(
            sessionId=str(session["_id"]),
            expiresAt=_as_utc(session["expiresAt"]).isoformat(),
            locationId=str(user["simulatedLocationId"]),
            message=ChatAssistantMessage(
                content=answer.content,
                strategy=metadata.strategy,
                intent=metadata.intent,
                confidence=metadata.confidence,
                uncertainty=metadata.uncertainty,
                aiUsed=metadata.aiUsed,
                citedNews=[
                    ChatCitedNews(
                        id=str(document["_id"]),
                        slug=str(document.get("slug") or ""),
                        title=str(document.get("title") or ""),
                        verificationStatus=verification_status(document),
                    )
                    for document in answer.cited
                ],
                createdAt=assistant_created_at.isoformat(),
            ),
        )

    # ------------------------------------------------------------------
    # Usuario, ubicación y sesión
    # ------------------------------------------------------------------

    async def _default_location_id(self) -> ObjectId:
        locations = self._db["locations"]
        location = await locations.find_one(
            {"countryCode": self._settings.default_location_code, "active": True}, {"_id": 1}
        ) or await locations.find_one({"active": True}, {"_id": 1})
        if location is None:
            raise NewsChatRequestError(
                "No hay ubicaciones activas. Ejecutá make db-seed-catalog.", 503
            )
        return location["_id"]

    async def _ensure_user(
        self,
        request: ChatRequest,
        location_id: ObjectId | None,
        now: datetime,
        *,
        admin_username: str | None = None,
    ) -> dict[str, Any]:
        external_id = request.user.id
        is_admin = external_id.startswith(("admin:", "local-admin:"))
        if is_admin:
            if not admin_username or external_id not in {
                f"admin:{admin_username}",
                admin_external_id(admin_username),
            }:
                raise NewsChatRequestError("Token admin válido requerido para esta identidad.", 401)
            external_id = admin_external_id(admin_username)
        if location_id is not None:
            location = await self._db["locations"].find_one(
                {"_id": location_id, "active": True}, {"_id": 1}
            )
            if location is None:
                raise NewsChatRequestError("La ubicación seleccionada no existe.", 400)

        users = self._db["users"]
        existing = await users.find_one({"firebaseUid": external_id})
        if existing is None:
            identity = {"_id": admin_author_id(admin_username)} if is_admin else {}
            document = User(
                **identity,
                firebaseUid=external_id,
                email=request.user.email,
                displayName=request.user.displayName,
                photoUrl=request.user.photoUrl,
                role=UserRole.admin if is_admin else UserRole.user,
                simulatedLocationId=location_id or await self._default_location_id(),
                createdAt=now,
                updatedAt=now,
                lastLoginAt=now,
            ).model_dump_mongo()
            try:
                await users.insert_one(document)
                return document
            except DuplicateKeyError:
                existing = await users.find_one({"firebaseUid": external_id})
                if existing is None:
                    raise

        changes: dict[str, Any] = {"lastLoginAt": now, "updatedAt": now}
        if is_admin:
            changes["role"] = UserRole.admin
        if location_id is not None and location_id != existing.get("simulatedLocationId"):
            changes["simulatedLocationId"] = location_id
        await users.update_one({"_id": existing["_id"]}, {"$set": changes})
        return {**existing, **changes}

    async def _load_or_create_session(
        self, session_id: ObjectId | None, user: dict[str, Any], now: datetime
    ) -> dict[str, Any]:
        sessions = self._db["chatSessions"]
        if session_id is not None:
            # El TTL de MongoDB borra con retraso: la vigencia se comprueba también aquí.
            session = await sessions.find_one(
                {"_id": session_id, "userId": user["_id"], "expiresAt": {"$gt": now}}
            )
            if session is not None:
                return session

        session = ChatSession(
            userId=user["_id"],
            simulatedLocationId=user["simulatedLocationId"],
            messages=[],
            createdAt=now,
            expiresAt=now + timedelta(seconds=self._settings.chat_session_ttl_seconds),
        ).model_dump_mongo()
        await sessions.insert_one(session)
        return session

    # ------------------------------------------------------------------
    # Selección de noticias
    # ------------------------------------------------------------------

    async def _query_locations(
        self, query: ClassifiedQuery, user: dict[str, Any]
    ) -> list[dict[str, Any]]:
        conditions: list[dict[str, Any]] = []
        if query.country_codes:
            conditions.append({"countryCode": {"$in": list(query.country_codes)}})
        if query.wants_user_location:
            conditions.append({"_id": user["simulatedLocationId"]})
        if not conditions and not query.group_by_country:
            return []
        return await (
            self._db["locations"]
            .find(
                {"active": True, **({"$or": conditions} if conditions else {})},
                {"_id": 1, "country": 1, "countryCode": 1},
            )
            .to_list(length=None)
        )

    async def _previously_cited(
        self, session: dict[str, Any], index: int | None = None
    ) -> list[dict[str, Any]]:
        for message in reversed(session.get("messages") or []):
            if message.get("role") != MessageRole.assistant:
                continue
            metadata = message.get("responseMetadata") or {}
            if metadata.get("intent") == ResponseIntent.unsupported:
                continue
            cited_ids = list(metadata.get("citedNewsIds") or [])
            if index is not None:
                cited_ids = cited_ids[index : index + 1]
            # Un rechazo ajeno a noticias no borra el contexto; una consulta sin
            # coincidencias sí deja su selección vacía para no recuperar otra.
            return await find_published_news_by_ids(self._db, cited_ids)
        return []

    async def _plan(
        self,
        query: ClassifiedQuery,
        news_document: dict[str, Any] | None,
        user: dict[str, Any],
        session: dict[str, Any],
    ) -> _Plan:
        if query.wants_count or (query.group_by_country and query.intent in LISTING_INTENTS):
            return await self._inventory_plan(query, user)
        if news_document is not None:
            intent = query.intent or ResponseIntent.explain
            return self._plan_for(intent, [news_document], intro="")
        if query.use_previous_citations:
            cited = await self._previously_cited(session, query.citation_index)
            if not cited:
                return _Plan(
                    intent=query.intent or ResponseIntent.explain,
                    database_reply="No encontré esa referencia entre las noticias publicadas de este turno.",
                )
            return self._plan_for(
                query.intent or ResponseIntent.explain,
                cited,
                intro="",
                preserve_selection=True,
            )

        locations = await self._query_locations(query, user)
        location_ids = {location["_id"] for location in locations}
        intent = query.intent
        filters = news_filters(query, location_ids)
        matching_count = None
        if intent in LISTING_INTENTS:
            candidates = await published_news_matching(self._db, filters)
            matching_count = await self._db["news"].count_documents(
                {**filters, "status": "published"}
            )
        else:
            recent = await recent_published_news(self._db)
            candidates = select_news(recent, query, location_ids, use_terms=True)

        if intent is None:
            if query.terms:
                # Términos propios que no aparecen en ninguna noticia: fuera de dominio.
                if not candidates:
                    return _Plan(intent=ResponseIntent.unsupported)
                intent = (
                    ResponseIntent.news_detail
                    if len(candidates) == 1
                    else ResponseIntent.topic_news
                )
            else:
                # Seguimiento sin términos ("¿y eso?"): se apoya en lo último que se citó.
                candidates = await self._previously_cited(session)
                if not candidates:
                    return _Plan(intent=ResponseIntent.unsupported)
                intent = ResponseIntent.explain

        if not candidates:
            return _Plan(intent=intent, database_reply=NOT_FOUND_REPLY)

        if intent == ResponseIntent.regional_news:
            countries = ", ".join(sorted({str(location["country"]) for location in locations}))
            intro = f"Noticias de {countries}:"
        elif intent == ResponseIntent.topic_news:
            labels = ", ".join(topic_label(topic) for topic in query.topics)
            intro = f"Noticias de {labels}:" if labels else "Noticias relacionadas con tu consulta:"
        elif intent == ResponseIntent.recent_news:
            intro = "Estas son las noticias más recientes:"
        else:
            intro = ""
        plan = self._plan_for(intent, candidates, intro=intro)
        plan.matching_count = matching_count
        return plan

    async def _inventory_plan(self, query: ClassifiedQuery, user: dict[str, Any]) -> _Plan:
        locations = await self._query_locations(query, user)
        filters = news_filters(query, {location["_id"] for location in locations})
        counts = await count_news(self._db, filters)
        labels = ", ".join(topic_label(topic) for topic in query.topics)
        topic_note = f" sobre {labels}" if labels else ""
        if query.group_by_country:
            lines = [f"Hay {counts['published']} noticias publicadas{topic_note}. Por país:", ""]
            countries: dict[str, list[dict[str, Any]]] = {}
            for location in locations:
                countries.setdefault(location["country"], []).append(location)
            cited_by_id: dict[ObjectId, dict[str, Any]] = {}
            for country, members in sorted(countries.items()):
                country_filters = {
                    **filters,
                    "geographicScope.locationIds": {"$in": [item["_id"] for item in members]},
                }
                total = await self._db["news"].count_documents(
                    {**country_filters, "status": "published"}
                )
                if not total:
                    continue
                example = await published_news_matching(self._db, country_filters, limit=1)
                lines.append(f"**{country}**: {total} noticias publicadas.")
                if example:
                    lines.append(format_listing("Ejemplo:", example))
                    cited_by_id[example[0]["_id"]] = example[0]
                lines.append("")
            if not cited_by_id:
                lines.append("No hay noticias publicadas con países resueltos en el catálogo.")
            lines.append("Las noticias con varios países pueden aparecer en más de un grupo.")
            return _Plan(
                ResponseIntent.regional_news,
                list(cited_by_id.values()),
                "\n".join(lines),
                database_only=True,
            )
        countries = ", ".join(sorted({location["country"] for location in locations}))
        country_note = f" de {countries}" if countries else ""
        reply = (
            f"En la base de datos de AI News{country_note}{topic_note} hay "
            f"{counts['total']} noticias en total: {counts['published']} publicadas y "
            f"{counts['draft']} borradores.\n\n"
            "El chat solo muestra y cita el contenido de noticias publicadas."
        )
        cited = await published_news_matching(self._db, filters)
        return _Plan(query.intent or ResponseIntent.recent_news, cited, reply, database_only=True)

    @staticmethod
    def _plan_for(
        intent: ResponseIntent,
        candidates: list[dict[str, Any]],
        *,
        intro: str,
        preserve_selection: bool = False,
    ) -> _Plan:
        if intent in LISTING_INTENTS:
            cited = candidates[:LISTING_LIMIT]
            return _Plan(intent, cited, format_listing(intro, cited))
        if intent == ResponseIntent.news_detail:
            cited = candidates[:1]
            return _Plan(intent, cited, format_detail(cited[0]), include_content=True)
        cited = candidates if preserve_selection else candidates[:ELABORATION_LIMIT]
        if intent == ResponseIntent.summarize:
            reply = format_listing("Resumen de las noticias:", cited)
        else:
            reply = "\n\n".join(format_detail(document) for document in cited)
        return _Plan(intent, cited, reply, include_content=True)

    # ------------------------------------------------------------------
    # Respuesta: IA cuando corresponde, base de datos como respaldo
    # ------------------------------------------------------------------

    async def _answer(
        self,
        request: ChatRequest,
        plan: _Plan,
        news_document: dict[str, Any] | None,
        user: dict[str, Any],
        session: dict[str, Any],
    ) -> _Answer:
        if plan.intent == ResponseIntent.unsupported:
            return _Answer(
                UNSUPPORTED_REPLY,
                ResponseStrategy.template,
                plan.intent,
                [],
                Confidence(ConfidenceLevel.low, None),
            )

        confidence = compute_confidence(plan.cited)
        if plan.database_only:
            return self._database_answer(plan, confidence, note=None)
        if not plan.cited:
            return self._database_answer(plan, confidence, note=None)
        if self._settings.provider == "stub":
            # El stub no es un proveedor real: no elabora ni consume presupuesto.
            note = (
                "La elaboración con IA no está habilitada; esta es la información registrada."
                if plan.intent in {ResponseIntent.summarize, ResponseIntent.explain}
                else None
            )
            return self._database_answer(plan, confidence, note=note)

        if (
            self._settings.input_usd_per_million is None
            or self._settings.output_usd_per_million is None
        ):
            raise ChatbotConfigurationError(
                "NEWS_CHAT_INPUT_USD_PER_MILLION y NEWS_CHAT_OUTPUT_USD_PER_MILLION son "
                "obligatorios con un proveedor real: sin ellos no se puede registrar el costo "
                "en aiUsage."
            )

        provider = self._provider_factory()
        instructions = load_system_prompt(self._settings)
        history = [
            {"role": _plain(message["role"]), "content": message["content"]}
            for message in (session.get("messages") or [])[-HISTORY_MESSAGES_FOR_LLM:]
        ]
        locations = await resolve_news_locations(self._db, plan.cited)
        context = {
            "noticias": news_context(
                plan.cited, include_content=plan.include_content, locations=locations
            ),
            "inventario": await count_news(self._db),
            "seleccion": {
                "mostradas": len(plan.cited),
                "coincidenciasPublicadas": plan.matching_count,
                "esMuestra": plan.matching_count is None or plan.matching_count > len(plan.cited),
            },
        }
        message = f"Petición ({plan.intent.value}): {request.message}"

        input_chars = (
            len(instructions)
            + sum(len(item["content"]) for item in history)
            + len(json.dumps(context, ensure_ascii=False))
            + len(message)
        )
        worst_case_cost = self._cost(
            input_chars // CHARS_PER_TOKEN_ESTIMATE + 1, self._settings.max_output_tokens
        )
        if await self._spent_usd() + worst_case_cost > self._settings.ai_budget_usd:
            return self._database_answer(
                plan,
                confidence,
                note="Se alcanzó el presupuesto de IA; esta es la información registrada.",
            )

        try:
            response = await provider.generate(
                instructions=instructions,
                message=message,
                previous_response_id=None,
                context=context,
                user_id=request.user.id,
                history=history,
            )
        except OpenAIProviderError:
            return self._database_answer(
                plan,
                confidence,
                note="La IA no respondió en este momento; esta es la información registrada.",
            )

        if response.input_tokens is not None and response.output_tokens is not None:
            cost = self._cost(response.input_tokens, response.output_tokens)
        else:
            # Sin uso reportado se registra el peor caso para no subestimar el gasto.
            cost = worst_case_cost
        await self._db["aiUsage"].insert_one(
            AiUsage(
                feature=AiFeature.chat,
                provider=self._settings.provider,
                model=response.model,
                userId=user["_id"],
                newsId=news_document["_id"] if news_document is not None else None,
                chatSessionId=session["_id"],
                inputTokens=response.input_tokens,
                outputTokens=response.output_tokens,
                estimatedCostUsd=cost,
                createdAt=self._clock(),
            ).model_dump_mongo()
        )

        content = response.message
        if confidence.level == ConfidenceLevel.low and confidence.uncertainty:
            content = f"{content}\n\nAviso: {confidence.uncertainty}"
        return _Answer(content, ResponseStrategy.llm, plan.intent, plan.cited, confidence)

    @staticmethod
    def _database_answer(plan: _Plan, confidence: Confidence, *, note: str | None) -> _Answer:
        content = f"{plan.database_reply}\n\n{note}" if note else plan.database_reply
        return _Answer(
            content, ResponseStrategy.database_query, plan.intent, plan.cited, confidence
        )

    def _cost(self, input_tokens: int, output_tokens: int) -> float:
        input_price = self._settings.input_usd_per_million or 0.0
        output_price = self._settings.output_usd_per_million or 0.0
        return float(
            input_tokens * input_price / 1_000_000 + output_tokens * output_price / 1_000_000
        )

    async def _spent_usd(self) -> float:
        cursor = await self._db["aiUsage"].aggregate(
            [{"$group": {"_id": None, "total": {"$sum": "$estimatedCostUsd"}}}]
        )
        result = await cursor.to_list(length=1)
        return float(result[0]["total"]) if result else 0.0

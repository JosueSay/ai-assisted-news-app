"""Validated, retry-safe recording and inference for reading interactions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from .models.user_interaction import InteractionContext, UserInteraction


OPENED_DWELL_THRESHOLD_SECONDS = 30
OPENED_INTEREST_INCREMENT = 0.02
READ_INTEREST_INCREMENT = 0.08


def _recompute_interests(database, user_id: ObjectId, now: datetime) -> None:
    user = database["users"].find_one({"_id": user_id})
    if not user:
        return
    existing = {
        item["topic"]: item
        for item in user.get("inferredInterests") or []
    }
    events_by_news_and_type: dict[tuple[ObjectId, str], dict[str, Any]] = {}
    for interaction in database["userInteractions"].find({"userId": user_id}):
        raw_type = interaction["type"]
        interaction_type = getattr(raw_type, "value", raw_type)
        key = (interaction["newsId"], str(interaction_type))
        previous = events_by_news_and_type.get(key)
        if previous is None or (
            interaction["type"] == "opened"
            and (interaction.get("dwellTimeSeconds") or 0)
            > (previous.get("dwellTimeSeconds") or 0)
        ):
            events_by_news_and_type[key] = interaction

    scores: dict[str, float] = {}
    for (news_id, interaction_type), interaction in events_by_news_and_type.items():
        if interaction_type == "opened":
            if (interaction.get("dwellTimeSeconds") or 0) < OPENED_DWELL_THRESHOLD_SECONDS:
                continue
            delta = OPENED_INTEREST_INCREMENT
        elif interaction_type == "read":
            delta = READ_INTEREST_INCREMENT
        else:
            continue
        news = database["news"].find_one({"_id": news_id}, {"topics": 1})
        for topic in dict.fromkeys((news or {}).get("topics") or []):
            scores[topic] = min(1.0, scores.get(topic, 0.0) + delta)

    interests = []
    for topic in sorted(scores):
        score = scores[topic]
        previous = existing.get(topic) or {}
        interests.append(
            {
                "topic": topic,
                "score": score,
                "updatedAt": previous.get("updatedAt", now)
                if float(previous.get("score", -1)) == score
                else now,
            }
        )
    previous_interests = sorted(
        user.get("inferredInterests") or [], key=lambda item: item["topic"]
    )
    if interests != previous_interests:
        database["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "inferredInterests": interests,
                    "updatedAt": now,
                }
            },
        )


def record_interaction(
    database,
    user: dict[str, Any],
    news: dict[str, Any],
    interaction_type: str,
    *,
    feed_position: int | None = None,
    dwell_time_seconds: int | None = None,
    now: datetime | None = None,
) -> tuple[dict[str, Any], bool]:
    """Record one event per user/news/type; repeated calls do not repeat learning."""
    if interaction_type not in {"opened", "read"}:
        raise ValueError("Tipo de interacción no disponible.")
    current_time = now or datetime.now(timezone.utc)
    collection = database["userInteractions"]
    query = {
        "userId": user["_id"],
        "newsId": news["_id"],
        "type": interaction_type,
    }

    if interaction_type == "opened":
        existing = collection.find_one(query)
        if existing:
            current_dwell = existing.get("dwellTimeSeconds")
            updated_dwell = max(current_dwell or 0, dwell_time_seconds or 0)
            if updated_dwell != current_dwell:
                collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"dwellTimeSeconds": updated_dwell}},
                )
                existing = {**existing, "dwellTimeSeconds": updated_dwell}
            _recompute_interests(database, user["_id"], current_time)
            return existing, False

        interaction = UserInteraction(
            userId=user["_id"],
            newsId=news["_id"],
            type="opened",
            dwellTimeSeconds=dwell_time_seconds,
            context=InteractionContext(
                simulatedLocationId=user["simulatedLocationId"],
                feedPosition=feed_position,
            ),
            createdAt=current_time,
        ).model_dump_mongo()
        collection.insert_one(interaction)
        _recompute_interests(database, user["_id"], current_time)
        return interaction, True

    existing = collection.find_one(query)
    if existing:
        _recompute_interests(database, user["_id"], current_time)
        return existing, False

    opened = collection.find_one({**query, "type": "opened"})
    if not opened:
        raise ValueError("La apertura de la noticia no fue registrada.")
    interaction = UserInteraction(
        userId=user["_id"],
        newsId=news["_id"],
        type="read",
        dwellTimeSeconds=dwell_time_seconds,
        context=InteractionContext.model_validate(opened["context"]),
        createdAt=current_time,
    ).model_dump_mongo()
    collection.insert_one(interaction)
    _recompute_interests(database, user["_id"], current_time)
    return interaction, True

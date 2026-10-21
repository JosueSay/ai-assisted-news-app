"""Deterministic ranking and diversity policy for the news feed."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


FRESHNESS_WINDOW_DAYS = 14
FEED_LIMIT = 50
DIVERSITY_POSITIONS = (3, 8)  # zero-based: positions 4 and 9


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )


def _location_id(value: Any) -> str | None:
    return str(value) if value is not None else None


def _rank_components(
    document: dict[str, Any], user: dict[str, Any] | None, now: datetime
) -> tuple[float, dict[str, float]]:
    scope = document.get("geographicScope") or {}
    location_ids = {str(value) for value in scope.get("locationIds") or []}
    level = str(scope.get("level") or "")
    topics = set(document.get("topics") or [])
    components = {
        "location": 0.0,
        "declared": 0.0,
        "inferred": 0.0,
        "freshness": 0.0,
    }

    if user:
        user_location = _location_id(user.get("simulatedLocationId"))
        if user_location and user_location in location_ids:
            components["location"] = 30.0
        elif level == "international":
            components["location"] = 10.0

        onboarding = user.get("onboarding") or {}
        if topics.intersection(onboarding.get("selectedTopics") or []):
            components["declared"] = 20.0

        inferred_scores = {
            item.get("topic"): float(item.get("score", 0))
            for item in user.get("inferredInterests") or []
            if item.get("topic") in topics
        }
        if inferred_scores:
            components["inferred"] = 20.0 * max(inferred_scores.values())

    published_at = _as_utc(document.get("publishedAt"))
    if published_at is not None:
        current_time = _as_utc(now) or datetime.now(timezone.utc)
        age_days = max(0.0, (current_time - published_at).total_seconds() / 86400)
        components["freshness"] = max(
            0.0, 20.0 * (1.0 - age_days / FRESHNESS_WINDOW_DAYS)
        )

    return sum(components.values()), components


def _published_timestamp(document: dict[str, Any]) -> float:
    published_at = _as_utc(document.get("publishedAt"))
    return published_at.timestamp() if published_at else float("-inf")


def _reason(components: dict[str, float]) -> str:
    labels = {
        "location": "Por tu ubicación",
        "declared": "Por los temas que elegiste",
        "inferred": "Por tus intereses de lectura",
        "freshness": "Por actualidad",
    }
    strongest = max(components, key=lambda key: components[key])
    return labels[strongest] if components[strongest] > 0 else "En tu feed"


def rank_news(
    documents: list[dict[str, Any]],
    user: dict[str, Any] | None,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Score all candidates before truncating, with stable score/date/id ties."""
    current_time = now or datetime.now(timezone.utc)
    ranked = []
    for document in documents:
        score, components = _rank_components(document, user, current_time)
        ranked.append(
            {
                "document": document,
                "score": score,
                "components": components,
                "reason": _reason(components),
            }
        )
    return sorted(
        ranked,
        key=lambda item: (
            -item["score"],
            -_published_timestamp(item["document"]),
            str(item["document"].get("_id", item["document"].get("slug", ""))),
        ),
    )


def _is_diverse_candidate(
    document: dict[str, Any], user: dict[str, Any] | None
) -> bool:
    scope = document.get("geographicScope") or {}
    if scope.get("level") == "international":
        return True
    if user is None or user.get("simulatedLocationId") is None:
        return False
    location_ids = {str(value) for value in scope.get("locationIds") or []}
    return bool(location_ids) and str(user["simulatedLocationId"]) not in location_ids


def compose_feed(
    ranked: list[dict[str, Any]],
    user: dict[str, Any] | None,
    *,
    limit: int = FEED_LIMIT,
) -> list[dict[str, Any]]:
    """Reserve two of the first ten slots for other geographic coverage when possible."""
    candidates = ranked
    diverse_candidates = sorted(
        (item for item in ranked if _is_diverse_candidate(item["document"], user)),
        key=lambda item: (
            -_published_timestamp(item["document"]),
            str(item["document"].get("_id", item["document"].get("slug", ""))),
        ),
    )
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    diversity_positions = set(DIVERSITY_POSITIONS)

    def take_next(*, diverse_only: bool = False) -> dict[str, Any] | None:
        for item in diverse_candidates if diverse_only else candidates:
            document = item["document"]
            item_id = str(document.get("_id", document.get("slug", "")))
            if item_id in selected_ids:
                continue
            selected_ids.add(item_id)
            if diverse_only:
                return {**item, "reason": "Para ampliar tu cobertura"}
            return item
        return None

    for position in range(min(len(candidates), max(0, limit))):
        item = take_next(diverse_only=position in diversity_positions and position < 10)
        if item is None:
            item = take_next()
        if item is None:
            break
        selected.append(item)
    return selected

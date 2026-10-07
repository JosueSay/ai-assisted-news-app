"""MongoDB $jsonSchema validators para las colecciones de noticias."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import COLLECTIONS

JsonDict = dict[str, Any]

OBJECT_ID = {"bsonType": "objectId"}
STRING = {"bsonType": "string"}
DATE = {"bsonType": "date"}
BOOL = {"bsonType": "bool"}
STRING_OR_NULL = {"bsonType": ["string", "null"]}
DATE_OR_NULL = {"bsonType": ["date", "null"]}
OBJECT_ID_OR_NULL = {"bsonType": ["objectId", "null"]}
NUMBER_NON_NEGATIVE = {"bsonType": ["int", "long", "double", "decimal"], "minimum": 0}
INT_NON_NEGATIVE = {"bsonType": ["int", "long"], "minimum": 0}
INT_POSITIVE = {"bsonType": ["int", "long"], "minimum": 1}

LOCATION_LEVELS = ["city", "region", "country", "international"]
USER_ROLES = ["user", "admin"]
NEWS_STATUSES = ["draft", "published"]
VERIFICATION_STATUSES = [
    "confirmed",
    "developing",
    "insufficient_sources",
    "conflicting_sources",
]
SOURCE_TYPES = ["official", "media", "primary_source", "witness", "other"]
IMAGE_TYPES = ["photograph", "illustration", "ai_generated", "ai_modified", "none"]
INTERACTION_TYPES = ["opened", "read"]
MESSAGE_ROLES = ["user", "assistant"]
RESPONSE_STRATEGIES = ["database_query", "template", "llm"]
RESPONSE_INTENTS = [
    "recent_news",
    "regional_news",
    "topic_news",
    "news_detail",
    "summarize",
    "explain",
    "unsupported",
]
CONFIDENCE_LEVELS = ["high", "medium", "low"]
AI_FEATURES = ["chat", "summary", "image_generation", "classification"]
AUDIT_ACTIONS = ["news.created", "news.updated", "news.published", "image.generated"]


def array_of(items: JsonDict) -> JsonDict:
    return {"bsonType": "array", "items": items}


def object_schema(required: list[str], properties: JsonDict) -> JsonDict:
    return {
        "bsonType": "object",
        "required": required,
        "properties": properties,
    }


def validator(schema: JsonDict) -> JsonDict:
    return {"$jsonSchema": schema}


VALIDATORS: dict[str, JsonDict] = {
    "locations": validator(
        object_schema(
            ["_id", "name", "country", "countryCode", "level", "active", "createdAt"],
            {
                "_id": OBJECT_ID,
                "name": STRING,
                "city": STRING_OR_NULL,
                "region": STRING_OR_NULL,
                "country": STRING,
                "countryCode": STRING,
                "level": {"enum": LOCATION_LEVELS},
                "active": BOOL,
                "createdAt": DATE,
            },
        )
    ),
    "users": validator(
        object_schema(
            [
                "_id",
                "firebaseUid",
                "email",
                "displayName",
                "photoUrl",
                "role",
                "simulatedLocationId",
                "onboarding",
                "inferredInterests",
                "createdAt",
                "updatedAt",
                "lastLoginAt",
            ],
            {
                "_id": OBJECT_ID,
                "firebaseUid": STRING,
                "email": STRING,
                "displayName": STRING,
                "photoUrl": STRING,
                "role": {"enum": USER_ROLES},
                "simulatedLocationId": OBJECT_ID,
                "onboarding": object_schema(
                    ["completed", "completedAt", "selectedTopics"],
                    {
                        "completed": BOOL,
                        "completedAt": DATE_OR_NULL,
                        "selectedTopics": array_of(STRING),
                    },
                ),
                "inferredInterests": array_of(
                    object_schema(
                        ["topic", "score", "updatedAt"],
                        {
                            "topic": STRING,
                            "score": {
                                "bsonType": ["int", "long", "double", "decimal"],
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "updatedAt": DATE,
                        },
                    )
                ),
                "createdAt": DATE,
                "updatedAt": DATE,
                "lastLoginAt": DATE,
            },
        )
    ),
    "news": validator(
        object_schema(
            [
                "_id",
                "slug",
                "title",
                "summary",
                "content",
                "authorId",
                "status",
                "topics",
                "keywords",
                "geographicScope",
                "verification",
                "sources",
                "image",
                "aiAssistance",
                "wordCount",
                "estimatedReadingMinutes",
                "publishedAt",
                "createdAt",
                "updatedAt",
            ],
            {
                "_id": OBJECT_ID,
                "slug": STRING,
                "title": STRING,
                "summary": STRING,
                "content": STRING,
                "authorId": OBJECT_ID,
                "status": {"enum": NEWS_STATUSES},
                "topics": array_of(STRING),
                "keywords": array_of(STRING),
                "geographicScope": object_schema(
                    ["level", "locationIds"],
                    {
                        "level": {"enum": LOCATION_LEVELS},
                        "locationIds": array_of(OBJECT_ID),
                    },
                ),
                "verification": object_schema(
                    ["status", "reviewedBy", "reviewedAt", "notes"],
                    {
                        "status": {"enum": VERIFICATION_STATUSES},
                        "reviewedBy": OBJECT_ID_OR_NULL,
                        "reviewedAt": DATE_OR_NULL,
                        "notes": STRING_OR_NULL,
                    },
                ),
                "sources": array_of(
                    object_schema(
                        [
                            "name",
                            "url",
                            "sourceType",
                            "publishedAt",
                            "accessedAt",
                            "supports",
                        ],
                        {
                            "name": STRING,
                            "url": STRING,
                            "sourceType": {"enum": SOURCE_TYPES},
                            "publishedAt": DATE_OR_NULL,
                            "accessedAt": DATE,
                            "supports": STRING_OR_NULL,
                        },
                    )
                ),
                "image": object_schema(
                    ["url", "alt", "type", "credit", "rights", "aiDisclosure"],
                    {
                        "url": STRING_OR_NULL,
                        "alt": STRING_OR_NULL,
                        "type": {"enum": IMAGE_TYPES},
                        "credit": STRING_OR_NULL,
                        "rights": STRING_OR_NULL,
                        "aiDisclosure": STRING_OR_NULL,
                    },
                ),
                "aiAssistance": object_schema(
                    [
                        "summaryGenerated",
                        "topicsGenerated",
                        "imageGenerated",
                        "humanReviewed",
                    ],
                    {
                        "summaryGenerated": BOOL,
                        "topicsGenerated": BOOL,
                        "imageGenerated": BOOL,
                        "humanReviewed": BOOL,
                    },
                ),
                "wordCount": INT_NON_NEGATIVE,
                "estimatedReadingMinutes": INT_POSITIVE,
                "publishedAt": DATE_OR_NULL,
                "createdAt": DATE,
                "updatedAt": DATE,
            },
        )
    ),
    "userInteractions": validator(
        object_schema(
            [
                "_id",
                "userId",
                "newsId",
                "type",
                "dwellTimeSeconds",
                "context",
                "createdAt",
            ],
            {
                "_id": OBJECT_ID,
                "userId": OBJECT_ID,
                "newsId": OBJECT_ID,
                "type": {"enum": INTERACTION_TYPES},
                "dwellTimeSeconds": {"bsonType": ["int", "long", "null"], "minimum": 0},
                "context": object_schema(
                    ["simulatedLocationId", "feedPosition"],
                    {
                        "simulatedLocationId": OBJECT_ID,
                        "feedPosition": {"bsonType": ["int", "long", "null"], "minimum": 0},
                    },
                ),
                "createdAt": DATE,
            },
        )
    ),
    "chatSessions": validator(
        object_schema(
            ["_id", "userId", "simulatedLocationId", "messages", "createdAt", "expiresAt"],
            {
                "_id": OBJECT_ID,
                "userId": OBJECT_ID,
                "simulatedLocationId": OBJECT_ID,
                "messages": array_of(
                    object_schema(
                        ["role", "content", "responseMetadata", "createdAt"],
                        {
                            "role": {"enum": MESSAGE_ROLES},
                            "content": STRING,
                            "responseMetadata": {
                                "bsonType": ["object", "null"],
                                "required": [
                                    "strategy",
                                    "intent",
                                    "citedNewsIds",
                                    "confidence",
                                    "uncertainty",
                                    "aiUsed",
                                ],
                                "properties": {
                                    "strategy": {"enum": RESPONSE_STRATEGIES},
                                    "intent": {"enum": RESPONSE_INTENTS},
                                    "citedNewsIds": array_of(OBJECT_ID),
                                    "confidence": {"enum": CONFIDENCE_LEVELS},
                                    "uncertainty": STRING_OR_NULL,
                                    "aiUsed": BOOL,
                                },
                            },
                            "createdAt": DATE,
                        },
                    )
                ),
                "createdAt": DATE,
                "expiresAt": DATE,
            },
        )
    ),
    "aiUsage": validator(
        object_schema(
            [
                "_id",
                "feature",
                "provider",
                "model",
                "userId",
                "newsId",
                "chatSessionId",
                "inputTokens",
                "outputTokens",
                "estimatedCostUsd",
                "createdAt",
            ],
            {
                "_id": OBJECT_ID,
                "feature": {"enum": AI_FEATURES},
                "provider": STRING,
                "model": STRING,
                "userId": OBJECT_ID_OR_NULL,
                "newsId": OBJECT_ID_OR_NULL,
                "chatSessionId": OBJECT_ID_OR_NULL,
                "inputTokens": {"bsonType": ["int", "long", "null"], "minimum": 0},
                "outputTokens": {"bsonType": ["int", "long", "null"], "minimum": 0},
                "estimatedCostUsd": NUMBER_NON_NEGATIVE,
                "createdAt": DATE,
            },
        )
    ),
    "auditLogs": validator(
        object_schema(
            ["_id", "actorId", "action", "entityType", "entityId", "details", "createdAt"],
            {
                "_id": OBJECT_ID,
                "actorId": OBJECT_ID,
                "action": {"enum": AUDIT_ACTIONS},
                "entityType": {"enum": ["news"]},
                "entityId": OBJECT_ID,
                "details": {"bsonType": "object"},
                "createdAt": DATE,
            },
        )
    ),
}


def expected_validators() -> dict[str, JsonDict]:
    """Devuelve una copia segura de los validators esperados."""
    return deepcopy(VALIDATORS)


def validator_for(collection_name: str) -> JsonDict:
    if collection_name not in COLLECTIONS:
        raise KeyError(f"Colección no soportada: {collection_name}")
    return deepcopy(VALIDATORS[collection_name])

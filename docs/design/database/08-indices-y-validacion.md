# Índices y validación

Parte de la [documentación de base de datos](README.md).

Este documento describe la estructura física esperada en MongoDB para la base
`ai_assisted_news`. La fuente ejecutable está en `backend/news/schema/`.

## Colecciones

El inicializador crea únicamente las colecciones faltantes:

| Colección | Tipo |
| --- | --- |
| `locations` | Catálogo |
| `users` | Persistente |
| `news` | Persistente |
| `userInteractions` | Persistente |
| `chatSessions` | Temporal |
| `aiUsage` | Persistente |
| `auditLogs` | Persistente |

## Validación

Cada colección usa un validator MongoDB `$jsonSchema` con:

| Opción | Valor |
| --- | --- |
| `validationLevel` | `strict` |
| `validationAction` | `error` |

Los validators cubren los campos requeridos, tipos BSON, enums definidos en el diseño lógico,
campos nullable explícitos y rangos numéricos importantes como `inferredInterests.score`,
`estimatedReadingMinutes`, `dwellTimeSeconds`, tokens y costo estimado.

## Índices únicos

| Colección | Índice | Clave | Motivo |
| --- | --- | --- | --- |
| `users` | `uq_users_firebase_uid` | `{ firebaseUid: 1 }` | Identificador externo de Firebase |
| `news` | `uq_news_slug` | `{ slug: 1 }` | URL/identificador legible de noticia |

## Índice TTL

| Colección | Índice | Clave | TTL |
| --- | --- | --- | --- |
| `chatSessions` | `ttl_chat_sessions_expires_at` | `{ expiresAt: 1 }` | `expireAfterSeconds: 0` |

`expiresAt` contiene la fecha exacta de expiración de la sesión. MongoDB elimina el documento
cuando esa fecha ya venció.

## Índices de consulta

| Colección | Índice | Clave | Patrón |
| --- | --- | --- | --- |
| `news` | `idx_news_status_published_at` | `{ status: 1, publishedAt: -1 }` | Feed general de publicadas recientes |
| `news` | `idx_news_location_status_published_at` | `{ geographicScope.locationIds: 1, status: 1, publishedAt: -1 }` | Feed por ubicación simulada |
| `news` | `idx_news_topics_status_published_at` | `{ topics: 1, status: 1, publishedAt: -1 }` | Feed y búsqueda por tema |
| `userInteractions` | `idx_interactions_user_created_at` | `{ userId: 1, createdAt: -1 }` | Historial reciente para intereses |
| `userInteractions` | `idx_interactions_user_news_type` | `{ userId: 1, newsId: 1, type: 1 }` | Consulta/deduplicación por usuario y noticia |
| `aiUsage` | `idx_ai_usage_feature_created_at` | `{ feature: 1, createdAt: -1 }` | Consumo de IA por funcionalidad |
| `auditLogs` | `idx_audit_entity_created_at` | `{ entityId: 1, createdAt: -1 }` | Historial administrativo por noticia |

## Operación segura

`make db-init` es idempotente y no destructivo:

- crea colecciones faltantes;
- sincroniza validators con `createCollection` o `collMod`;
- crea índices faltantes;
- no inserta documentos;
- no elimina documentos;
- no elimina índices existentes.

Si existe un índice con el mismo nombre pero distinta definición, el inicializador falla para
evitar un cambio destructivo implícito.

`make db-schema-check` verifica drift sin modificar la base de datos.

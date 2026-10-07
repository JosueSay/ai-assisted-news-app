# Loop 03 — MongoDB Collections, Validation and Indexes Result

## 1. Resultado

Completed.

Se materializó el esquema físico de `ai_assisted_news` con inicialización idempotente y no
destructiva. También se integró el flujo de base de datos al `docker-compose.yml` para poder
trabajar en modo local sin Atlas o en modo Atlas usando `keys/mongodb_uri`.

## 2. Estructura implementada

```text
backend/news/schema/
├── __init__.py
├── collections.py
├── validators.py
├── indexes.py
├── initialize.py
└── check.py
```

Colecciones materializadas:

```text
locations
users
news
userInteractions
chatSessions
aiUsage
auditLogs
```

## 3. Validators e índices

Cada colección tiene validator MongoDB `$jsonSchema` con:

```text
validationLevel: strict
validationAction: error
```

Índices únicos:

```text
users.uq_users_firebase_uid
news.uq_news_slug
```

TTL:

```text
chatSessions.ttl_chat_sessions_expires_at
expireAfterSeconds: 0
```

Índices de consulta:

```text
news.idx_news_status_published_at
news.idx_news_location_status_published_at
news.idx_news_topics_status_published_at
userInteractions.idx_interactions_user_created_at
userInteractions.idx_interactions_user_news_type
aiUsage.idx_ai_usage_feature_created_at
auditLogs.idx_audit_entity_created_at
```

## 4. Docker Compose y Makefile

Servicios agregados:

```text
news-mongo   profile: news-local
news-tools   profile: tools
```

El Makefile ahora ejecuta las tareas `db-*` dentro de Docker Compose.

Comandos agregados:

```bash
make db-init
make db-schema-check
make news-db-up
make news-db-down
```

En modo `local`, el Makefile levanta `news-mongo` antes de ejecutar las tareas. En modo `atlas`,
no levanta el Mongo local y usa `keys/mongodb_uri`.

## 5. Configuración

El `.env` principal vive en la raíz del repositorio.

Modo local:

```dotenv
NEWS_DB_MODE=local
COMPOSE_PROFILES=news-local
NEWS_MONGODB_DATABASE=ai_assisted_news
NEWS_MONGODB_REQUIRED=true
NEWS_MONGODB_TIMEOUT_MS=5000
NEWS_LOCAL_MONGO_PORT=27018
```

Modo Atlas:

```dotenv
NEWS_DB_MODE=atlas
COMPOSE_PROFILES=
NEWS_MONGODB_DATABASE=ai_assisted_news
NEWS_MONGODB_REQUIRED=true
NEWS_MONGODB_TIMEOUT_MS=5000
NEWS_LOCAL_MONGO_PORT=27018
```

## 6. Verificación ejecutada

```bash
docker compose config --quiet
docker compose build news-tools
make db-test
make db-check-config
make db-ping
make db-schema-check
make db-init
make db-schema-check
make db-init
NEWS_DB_MODE=atlas COMPOSE_PROFILES= make db-check-config
```

Resultados observados:

```text
docker compose config: OK
tests: 115 passed
local ping: OK
local schema before init: DRIFT DETECTED
local init: 7 collections, 7 validators, 10 indexes
local schema after init: OK
second init: unchanged
atlas config: configured
```

Inspección directa en Mongo local confirmó:

```text
collections: aiUsage, auditLogs, chatSessions, locations, news, userInteractions, users
TTL: chatSessions.expiresAt expireAfterSeconds=0
unique: users.firebaseUid, news.slug
```

## 7. Seguridad

```text
secret values exposed: NO
secret files tracked: NO
assistant modified: NO
documents inserted: NO
documents deleted: NO
collections dropped: NO
indexes dropped: NO
```

No se leyó ni imprimió el contenido de `keys/mongodb_uri`.

## 8. Documentación

Se actualizó:

```text
backend/news/README.md
docs/design/database/README.md
docs/design/database/07-diagrama.md
docs/design/database/08-indices-y-validacion.md
```

## 9. Blockers

Ninguno.

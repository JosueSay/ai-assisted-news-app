# Loop 03 — MongoDB Collections, Validation and Indexes Result

## 1. Resultado

Completed.

Cierre formal verificado el 2026-10-12: Atlas inicializado, dos comprobaciones de esquema
exitosas, segunda inicialización sin cambios y regresión de 126 tests aprobada. La implementación
existente está incluida en `a99b5df` (PR #2); este cierre modifica únicamente este handoff.

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
database dropped: NO
```

No se accedió directamente al contenido de archivos secretos ni se mostraron sus valores.
Atlas consumió la credencial exclusivamente mediante las interfaces existentes. Los comandos
Atlas de inicialización y comprobación descartaron stderr para evitar exponer detalles de
conexión ante una excepción del driver. Todos finalizaron con código 0.

Las confirmaciones de seguridad de datos describen las operaciones de este loop: no se
ejecutaron seeds, inserciones, actualizaciones de documentos, eliminaciones ni drops. No se
consultaron documentos ni se afirma que la base esté vacía. Los tests usaron mocks/fakes y
archivos temporales; no insertaron datos reales. `git ls-files keys` devolvió únicamente
`keys/README.md`.

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

El sandbox inicialmente impidió acceder al socket Docker para `make db-test`. Se repitió el
comando con permiso para ejecutarlo fuera del sandbox y pasó. Las verificaciones Atlas también
se ejecutaron con ese permiso. No fue necesario evadir `AGENTS.md` ni acceder directamente a
secretos. La configuración informó que falta la contraseña del panel admin; ese archivo no
es necesario para inicializar o verificar el esquema y no bloquea Loop 03.

## 10. Verificación final de Atlas e idempotencia

Se usaron asignaciones como argumentos de Make para asegurar que el `.env` incluido por el
Makefile no reemplazara el modo Atlas ni activara el perfil local. No se modificó `.env`.

Comandos ejecutados, en este orden después de la regresión offline:

```bash
make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-check-config
make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-init 2>/dev/null
make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-schema-check 2>/dev/null
make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-init 2>/dev/null
make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-schema-check 2>/dev/null
```

La interfaz segura de configuración confirmó antes de inicializar:

```text
Mode: atlas
Database: ai_assisted_news
MongoDB credential: configured
```

| Verificación | Primera ejecución | Segunda ejecución |
| --- | --- | --- |
| Colecciones creadas | 7 | 0 |
| Validators sincronizados | 7 | 0 |
| Índices creados | 10 | 0 |
| Estado del inicializador | Estructura creada | Schema already configured / unchanged. |
| Database schema | OK | OK |
| Collections | 7/7, sin colecciones inesperadas | 7/7, sin colecciones inesperadas |
| Validators | OK | OK |
| Indexes | OK | OK |
| TTL | OK | OK |

El schema check compara las definiciones de `backend/news/schema/`: validators completos y
política `strict/error`, claves y opciones de los 10 índices esperados, incluidos los únicos
de `users.firebaseUid` y `news.slug`, y TTL de `chatSessions.expiresAt` con
`expireAfterSeconds: 0`. No modifica la base ni comprueba la validez de documentos existentes.
La segunda inicialización confirmó idempotencia real sin cambios estructurales.

## 11. Regresión final

```bash
make db-test
```

Resultado: **126 passed in 0.43s**, cero fallos. Se mantienen las pruebas del Loop 03 y se
ejecutan también las pruebas ya presentes en `a99b5df`; no se agregaron tests ni funcionalidades
durante este cierre. No hubo regresiones respecto de los 115 tests registrados originalmente.

## 12. Trazabilidad del cierre

| Elemento revisado | Estado y evidencia | Cambió en este cierre |
| --- | --- | --- |
| Modelos | Revisados los siete modelos, campos, referencias, embebidos y enums frente a los validators; se conserva la separación de reglas indicada abajo | No |
| Validators | Siete definiciones; enums compartidos conceptualmente con los modelos; igualdad con Atlas y política strict/error verificadas por ambos schema checks | No |
| Índices | Diez definiciones con Access Patterns documentados en `08-indices-y-validacion.md`; unique y TTL verificados en Atlas | No |
| Documentación | Revisados README de DB, README de `backend/news/`, documentación de índices y reglas de lectura; se añade aquí evidencia del cierre | Solo este handoff |
| Diagrama | `07-diagrama.md` revisado: siete colecciones, referencias lógicas, embebidos, campos únicos y TTL vigentes | No |
| Tests | Suite existente de modelos, infraestructura, definiciones, inicialización y drift aprobada; 126 tests totales | No |
| Makefile | Se verificaron y ejecutaron `db-test`, `db-check-config`, `db-init` y `db-schema-check` | No |
| Secrets/bootstrap | Revisados configuración, montaje de secretos de solo lectura y `setup-keys` frente a `keys/README.md`; no cambió ninguna credencial requerida ni se ejecutó bootstrap | No |
| Seeders/scripts | Ningún cambio estructural que requiera sincronización; no se ejecutaron seeders | No |

Separación de validación existente, sin reinterpretar ni modificar el esquema:

| Regla | Modelo | MongoDB | Motivo |
| --- | --- | --- | --- |
| Campos y embebidos, tipos, enums y referencias ObjectId | Sí | Sí | Validación de aplicación y estructura BSON persistida |
| Rangos de score, tokens, costo y duración de interacción | Sí | Sí | Restricciones numéricas |
| URL HTTP(S), coherencia de publicación, imagen/IA y metadata de chat | Sí | Solo estructura/tipos/enums | Reglas cruzadas permanecen en aplicación |
| Cálculo de lectura | Sí | No recalcula | Campo derivado de content |
| Mínimo de estimatedReadingMinutes | No negativo en draft; cálculo con mínimo 1 al publicar | Mínimo 1 al persistir | Restricción física especificada por Loop 03; el modelo admite 0 en borradores, que MongoDB rechaza |
| Unicidad y expiración TTL | Calcula fecha de expiración | Índices unique y TTL | Garantías de persistencia |

## 13. Git y archivos modificados

- Commit de implementación: `a99b5df6a238cbfa78cb6289e12e0498b6237528` (`a99b5df`, PR #2).
- No se crea otro commit artificial para la implementación existente.
- Único archivo modificado para el cierre: `backend/loops/handoffs/03-db-indexes-validation-result.md`.
- Commit documental de cierre: `docs: close database schema loop` (el commit que contiene esta actualización).
- Revisión previa al commit: `git diff`, `git diff --check`, `git diff --cached` y `git status`;
  únicamente este Markdown se incluye en staging, sin secretos ni cambios en `backend/assistant/`.
- Estado final de Git: working tree limpio tras el commit documental; sin push ni modificación
  de historia. El hash del cierre y la comprobación post-commit se reportan en la respuesta final.

## 14. Continuidad

Loop 03 cerrado. No quedan decisiones pendientes para este cierre. Loop 04 puede partir del
esquema verificado en Atlas y de las interfaces existentes, revisando por separado el código
de catálogos/seeders ya incluido en el PR #2. Este cierre no ejecutó ni implementó Loop 04.

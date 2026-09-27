# Backend Discovery Result

## 1. Executive Summary

El backend contiene un único servicio funcional (`assistant/`), un chatbot modular con FastAPI,
OpenAI y MongoDB opcional. No existe ningún modelo, esquema, repositorio ni infraestructura de
persistencia relacionada con el diseño de base de datos de la aplicación de noticias definido en
`docs/design/database/`. El proyecto entero carece de base de datos operativa para la app de
noticias; la única conexión MongoDB existente es para contexto de chat (proyección `assistant_contexts`
o esquema NOVU heredado). No existe Makefile, CI/CD, ni automatización además de Docker Compose.

## 2. Backend Stack

| Área | Encontrado |
| --- | --- |
| Python | 3.13 (Dockerfile `python:3.13-slim`); host local 3.10.12 |
| Framework | FastAPI |
| Package manager | pip (`requirements.txt`) |
| Server | Uvicorn (puerto 8010) |
| Testing | pytest + pytest-asyncio + httpx + ruff |
| Database | MongoDB (solo `assistant/`, para contexto de chat) |
| Mongo library / ODM | PyMongo (`pymongo>=4.13`) directamente; sin ODM |

## 3. Relevant Repository Structure

```
ai-assisted-news-app/
├── .gitignore
├── docker-compose.yml                 # Servicios: mongo, chatbot, tests (perfil test)
├── backend/
│   ├── README.md
│   ├── assistant/                     # Único servicio implementado
│   │   ├── app.py                     # FastAPI entrypoint (v2.0.0)
│   │   ├── config.py                  # Settings desde variables de entorno + .env
│   │   ├── cli.py                     # CLI interactivo (asyncio)
│   │   ├── models.py                  # Pydantic: ChatRequest, ChatResponse, HealthResponse
│   │   ├── service.py                 # ChatService: orquestación turno
│   │   ├── prompts.py                 # Carga de system prompt desde archivo
│   │   ├── pyproject.toml             # pytest + ruff config
│   │   ├── requirements.txt           # fastapi, openai, pymongo, python-dotenv, uvicorn
│   │   ├── requirements-dev.txt       # + httpx, pytest, pytest-asyncio, ruff
│   │   ├── Dockerfile                 # multi-stage: base, test, runtime
│   │   ├── .env.example
│   │   ├── .gitignore
│   │   ├── .dockerignore
│   │   ├── README.md
│   │   ├── docs/
│   │   │   └── database.md            # Documentación interna de persistencia MongoDB
│   │   ├── docker/
│   │   │   └── mongo-init.js          # Init script: colección + índices + seed demo
│   │   ├── prompts/
│   │   │   └── system.md              # Prompt del asistente (NOVU financiero)
│   │   ├── providers/
│   │   │   ├── base.py                # Protocol ChatProvider, ProviderResponse
│   │   │   ├── openai.py              # OpenAI Responses API
│   │   │   └── stub.py                # Stub determinista para tests
│   │   ├── repositories/
│   │   │   ├── base.py                # Protocol ContextRepository + EmptyContextRepository
│   │   │   └── mongo.py               # MongoContextRepository (modos projection / novu)
│   │   └── tests/
│   │       ├── conftest.py            # Limpia caché de settings
│   │       ├── test_app.py            # FastAPI TestClient (health, chat, validación, error)
│   │       ├── test_mongo_repository.py  # Unit tests con MagicMock
│   │       ├── test_openai_provider.py   # Unit tests con FakeClient
│   │       ├── test_prompt.py         # Carga de prompt desde archivo
│   │       ├── test_service.py        # Integración service + provider + repository
│   │       ├── test_smoke.py          # Smoke test contra Docker Compose
│   │       └── README.md
│   ├── loops/
│   │   ├── 00-discovery.md            # Este loop
│   │   └── handoffs/
│   ├── prompts/
│   │   └── 00-discovery.md
│   ├── services/
│   │   └── README.md                  # Convención para servicios futuros
│   └── tests/
│       └── README.md
├── docs/
│   └── design/
│       ├── README.md
│       ├── 99-checklist-replicacion.md
│       └── database/
│           ├── README.md
│           ├── 01-colecciones.md
│           ├── 02-criterios-de-contenido.md
│           ├── 03-criterios-de-personalizacion.md
│           ├── 04-criterios-de-chat-y-costos.md
│           ├── 05-tiempo-de-lectura.md
│           └── 06-decisiones-descartadas.md
├── frontend/                          # App Expo (no relevante para backend DB)
└── keys/                              # NO INSPECCIONADO
```

## 4. Current Backend Architecture

El backend sigue una arquitectura de **servicio único** (`assistant/`). La convención documentada en
`backend/README.md` indica que los servicios futuros deben crearse dentro de `services/`.

`assistant/` está organizado en capas:

- **Entrypoint**: `app.py` (FastAPI) y `cli.py` (terminal CLI).
- **Config**: `config.py` lee variables de entorno + `.env` vía `python-dotenv`; usa `@lru_cache`.
- **Models**: `models.py` define Pydantic models (`ChatRequest`, `ChatResponse`, `HealthResponse`).
- **Service**: `service.py` orquesta: contexto → prompt → proveedor IA → respuesta.
- **Providers**: `providers/` implementa `ChatProvider` protocol con `OpenAIChatProvider` (OpenAI
  Responses API) y `StubChatProvider` (determinista, para tests).
- **Repositories**: `repositories/` implementa `ContextRepository` protocol con
  `MongoContextRepository` (dos modos: `projection` y `novu`) y `EmptyContextRepository` (no-op).
- **Prompts**: `prompts/` contiene `system.md` editable (NOVU financiero); se recarga en cada turno.

No existe:
- Router/controller layer separado (las rutas están en `app.py`).
- Capa de negocio de noticias.
- Modelos ODM.
- Seeders.
- Migraciones.
- Infraestructura CI/CD.

## 5. Database Design Found

El diseño aprobado está en `docs/design/database/` y define **7 colecciones MongoDB**:

### Colecciones propuestas

| Colección | Naturaleza |
| --- | --- |
| `locations` | Catálogo precargado (ciudades, regiones, países) |
| `users` | Persistente (cuenta, onboarding, intereses inferidos) |
| `news` | Persistente (contenido, verificación, fuentes, imagen, IA, alcance geográfico) |
| `userInteractions` | Persistente (`opened`, `read` + ubicación contextual) |
| `chatSessions` | Temporal con TTL (mensajes embebidos, expiración) |
| `aiUsage` | Persistente (control de presupuesto IA, 20 USD) |
| `auditLogs` | Persistente (solo acciones sobre `news`) |

### Relaciones principales

- `users.simulatedLocationId` → `locations` (N:1)
- `news.authorId` → `users` (N:1)
- `news.geographicScope.locationIds` → `locations` (N:M)
- `userInteractions.{userId,newsId,context.simulatedLocationId}` → `users`, `news`, `locations`
- `chatSessions.{userId,simulatedLocationId}` → `users`, `locations`
- `chatSessions.messages[].citedNewsIds` → `news` (N:M)
- `aiUsage.{userId,newsId,chatSessionId}` → opcional
- `auditLogs.{actorId,entityId}` → `users`, `news`

### Catálogos

- `locations`: catálogo geográfico con `level` city/region/country/international y `active` flag.

### Campos principales

- **users**: `firebaseUid` (único), `email`, `displayName`, `role`, `simulatedLocationId`,
  `onboarding`, `inferredInterests[]`
- **news**: `slug` (único), `title`, `summary`, `content`, `status` (draft/published),
  `topics`, `geographicScope`, `verification`, `sources[]`, `image`, `aiAssistance`,
  `wordCount`, `estimatedReadingMinutes`
- **userInteractions**: `type` (opened/read), `dwellTimeSeconds`, `context.{simulatedLocationId,
  feedPosition}`
- **chatSessions**: `messages[]` embebidos con `role`, `responseMetadata` (strategy, intent,
  citedNewsIds, confidence, uncertainty, aiUsed)
- **aiUsage**: `feature` (chat/summary/image_generation/classification), `estimatedCostUsd`
- **auditLogs**: `action` (news.created/updated/published, image.generated)

### Criterios de personalización

- Intereses declarados (`onboarding.selectedTopics`) vs inferidos (`inferredInterests[].score` 0-1).
- Feed ordenado por: ubicación, temas declarados, intereses inferidos, actualidad.
- Feed debe exponer contenido local/nacional/internacional aunque no coincida con intereses.
- Sin campo de prioridad editorial (descartado explícitamente).

### Criterios de contenido

- `news.status`: solo draft/published (sin revisión separada).
- Verificación: confirmed/developing/insufficient_sources/conflicting_sources.
- Fuentes: official/media/primary_source/witness/other.
- Imagen: photograph/illustration/ai_generated/ai_modified/none; coherencia con `aiAssistance`.
- Alcance geográfico: city/region/country/international.

### Comportamiento esperado del chat

- Sesiones temporales con TTL.
- Mensajes embebidos en el documento de sesión.
- `responseMetadata` discrimina estrategia (database_query/template/llm) e intención.
- Solo noticias `published` pueden citarse.

### Estrategia de costos

- Presupuesto total: 20 USD.
- Cada llamada IA registrada en `aiUsage` con `estimatedCostUsd`.
- `database_query` y `template` no generan registro en `aiUsage`.

### Cálculo de tiempo de lectura

- `estimatedReadingMinutes = ceil(wordCount / 200)`.
- Velocidad de referencia: 200 palabras/minuto.
- Se fijan al publicar; se recalculan si cambia `content`.
- Habilita proporción de lectura = `dwellTimeSeconds / (estimatedReadingMinutes * 60)`.

### Decisiones descartadas

- Prioridad editorial en `news` (eliminada).
- Interacciones `saved`, `shared`, `hidden`, `impression` (eliminadas).
- `location_change` como interacción (eliminada).
- Estado de revisión separado entre draft y published (no existe).
- Auditoría de entidades distintas de news (solo `news`).
- Proporción de lectura almacenada en `userInteractions` (es derivable).

## 6. Existing Persistence

La única persistencia existente es MongoDB a través de `MongoContextRepository` en `assistant/`.

**No existe** persistencia para el diseño de la aplicación de noticias.

### Detalle de persistencia existente

- **Driver**: PyMongo (`AsyncMongoClient`).
- **ODM**: Ninguno. PyMongo directamente.
- **Colecciones existentes**: Solo las del asistente:
  - `assistant_contexts` (modo `projection`): documentos con `{user_id, schema_version, context,
    updated_at}`.
  - Colecciones NOVU legado (modo `novu`): `users`, `savings_profiles`, `goals`, `contributions`,
    `withdrawal_requests`, `activities`.
- **Base de datos**: `assistant` (por defecto).
- **Modos de contexto**: `projection` (recomendado, 1 consulta) o `novu` (heredado, 6 consultas paralelas).
- **Índices conocidos** (de `mongo-init.js`):
  - `assistant_contexts`: `{user_id: 1}` único, `{updated_at: -1}`.
- **Init script**: `docker/mongo-init.js` crea colección, índices y seed `demo-user`.
- **Conexión**:
  - Timeout 5s (`serverSelectionTimeoutMS`).
  - Opcional (`MONGODB_REQUIRED=false` por defecto).
  - Si falla conexión y no es requerida, el servicio funciona sin contexto.

## 7. Configuration and Secrets

### Variables de entorno

El sistema actual lee configuración desde:

1. **Variables de entorno del sistema** (prioritarias).
2. **Archivo `.env`** en `backend/assistant/.env` (vía `python-dotenv`).

Variables definidas en `config.py`:

| Variable | Default | Propósito |
| --- | --- | --- |
| `API_GPT` | (vacío) | API key de OpenAI |
| `OPENAI_MODEL` | `gpt-5-mini` | Modelo |
| `OPENAI_MAX_OUTPUT_TOKENS` | 1600 | Tokens máximos |
| `OPENAI_TIMEOUT_SECONDS` | 30.0 | Timeout HTTP |
| `CHATBOT_PROVIDER` | `openai` | `openai` o `stub` |
| `CHATBOT_PROMPT_FILE` | `prompts/system.md` | Ruta al prompt |
| `CHATBOT_PROMPT_VERSION` | `assistant-v1` | Versión para trazabilidad |
| `CHATBOT_ALLOWED_ORIGINS` | `http://localhost:3000,...` | CORS |
| `MONGODB_URI` | (vacío) | URI MongoDB |
| `MONGODB_DATABASE` | `assistant` | DB name |
| `MONGODB_CONTEXT_MODE` | `projection` | `projection` o `novu` |
| `MONGODB_CONTEXT_COLLECTION` | `assistant_contexts` | Colección para modo projection |
| `MONGODB_USER_ID_TYPE` | `string` | `string` o `objectid` |
| `MONGODB_REQUIRED` | `false` | Si fallo de conexión es crítico |

### Secretos

- `API_GPT` es el único secreto actual.
- No se usa gestor de secretos externo.
- `.env` está en `.gitignore` y `.dockerignore`.
- Docker Compose pasa `API_GPT` vía variable de entorno (vacío por defecto).

### `keys/`

```
keys/ inspected: NO
keys/ exists: NO
keys/ in root .gitignore: No está listado explícitamente (no existe el directorio)
```

El directorio `keys/` no existe en el repositorio. No se inspeccionó ningún archivo dentro de él.

## 8. Existing Automation

| Herramienta | Comandos / Propósito |
| --- | --- |
| **Docker Compose** | `docker compose up --build` (servicios: mongo + chatbot) |
| | `docker compose --profile test up --build --abort-on-container-exit --exit-code-from tests tests` |
| | `docker compose down -v` (limpiar, incluyendo volúmenes) |
| **pip** | `python -m pip install -r assistant/requirements-dev.txt` |
| **Uvicorn** | `python -m uvicorn assistant.app:app --reload --port 8010` |
| **CLI** | `python -m assistant.cli` (chat interactivo en terminal) |
| **pytest** | `python -m pytest assistant/tests` |
| **ruff** | `python -m ruff check assistant` |

No existe Makefile, Taskfile, CI/CD pipeline, ni scripts shell adicionales.

## 9. Testing

### Framework y herramientas

- **Framework**: pytest (config en `pyproject.toml`).
- **Plugins**: pytest-asyncio (modo `auto`).
- **Linter**: ruff (line-length 100, target py312).
- **HTTP client**: httpx (para smoke test contra Docker).

### Estructura de tests

7 archivos en `backend/assistant/tests/`:

| Archivo | Tipo | Lo que prueba |
| --- | --- | --- |
| `test_app.py` | Unitario (TestClient) | Health sin leaks, chat response, validación, error de configuración |
| `test_mongo_repository.py` | Unitario (MagicMock) | Modo projection |
| `test_openai_provider.py` | Unitario (FakeClient) | Llamada a OpenAI Responses API |
| `test_prompt.py` | Unitario | Carga de archivo, prompt vacío |
| `test_service.py` | Integración (fakes) | Service pasa contexto al provider |
| `test_smoke.py` | Integración (Docker) | Health + chat contra contenedor en ejecución |
| `conftest.py` | Fixture | Limpieza de caché de settings |

### Ejecución de tests

**Resultado: NO EJECUTADOS** — el entorno local (Python 3.10.12) no tiene las dependencias
requeridas (`bson`, `pymongo`, `fastapi`, etc.). La instalación de dependencias violaría la
restricción del loop ("No instalar dependencias").

Los tests requieren:
- Python 3.12+ (el proyecto apunta a 3.13 en Docker).
- Dependencias de `requirements-dev.txt`.
- No requieren credenciales ni MongoDB para pasar (usan mocks/fakes/stub).

Los tests pueden ejecutarse correctamente dentro de Docker Compose:
```bash
docker compose --profile test up --build --abort-on-container-exit --exit-code-from tests tests
```

## 10. Git State

| Aspecto | Valor |
| --- | --- |
| Branch actual | `feat/design-db` |
| Estado del working tree | Limpio (sin cambios staged); archivos untracked: `backend/loops/`, `backend/prompts/` |
| Upstream | `origin/feat/design-db` (up to date) |
| Commits recientes (10) | Desde `b255cdc` (Initial commit) hasta `a6baeeb` (checklist replicación) |
| Estilo observable | Commits en español, prefijos tipo `docs:`, `feat:`, convención conventional commits |
| Commits clave | `b6a32ac` feat: add modular assistant; `bc08ee8` app móvil Expo; `9654ef3` docs DB design |

## 11. Missing Pieces

Componentes necesarios para implementar el diseño de base de datos que **no existen actualmente**:

1. **Modelos/ODM**: No hay modelos para `locations`, `users` (app), `news`, `userInteractions`,
   `chatSessions`, `aiUsage`, `auditLogs`.
2. **Repositorios**: No existe capa de acceso a datos para ninguna de las 7 colecciones del diseño.
3. **Seeders**: No hay datos de catálogo (`locations`) ni datos de prueba.
4. **Conexión MongoDB para la app**: La única conexión existente es para `assistant/`. Se necesita
   una conexión independiente (o compartida) para la base de datos de la aplicación de noticias.
5. **Servicio de noticias**: No existe ningún servicio, router o controlador para CRUD de noticias.
6. **Servicio de usuarios (app)**: No hay gestión de usuarios de la aplicación (solo existe
   contexto de chat).
7. **Servicio de interacciones**: No hay registro de `userInteractions`.
8. **Servicio de chat (nuevo diseño)**: El chat existente en `assistant/` es un chatbot financiero
   (NOVU); el diseño propone `chatSessions` con un esquema diferente para noticias.
9. **Control de presupuesto IA**: No existe el registro `aiUsage` ni lógica de presupuesto de 20 USD.
10. **Auditoría**: No existe `auditLogs`.
11. **Cálculo de tiempo de lectura**: No hay `wordCount` ni `estimatedReadingMinutes`.
12. **Índices MongoDB**: No existen índices para las nuevas colecciones.
13. **Inicialización de DB**: No hay `mongo-init.js` para el esquema de noticias.
14. **Migraciones**: No hay sistema de migraciones ni versionado de esquema.
15. **Variables de entorno para la nueva DB**: No existen variables como `NEWS_MONGODB_URI`,
    `NEWS_MONGODB_DATABASE`, etc.
16. **Autenticación Firebase**: El diseño referencia `firebaseUid` pero no hay integración con
    Firebase Auth.

## 12. Risks / Conflicts

1. **Conflicto de naming**: `assistant/` ya usa colecciones como `users` en modo `novu`. El diseño
   nuevo también incluye `users`. Habrá que decidir si comparten DB o son independientes.
2. **Chat existente vs chat del diseño**: El chatbot actual (`assistant/`) es financiero (NOVU). El
   diseño propone `chatSessions` para noticias. No está claro si deben converger o ser servicios
   separados.
3. **Versión de Python**: El host local tiene Python 3.10.12, pero el proyecto apunta a 3.13
   (Dockerfile) y `pyproject.toml` especifica `target-version = "py312"`. Desarrollo local fuera de
   Docker requiere Python 3.12+.
4. **Presupuesto IA**: El diseño fija 20 USD de presupuesto, pero no hay mecanismo para medir,
   alertar o cortar el gasto.
5. **FirebaseUid vs user_id**: El diseño usa `firebaseUid` como identificador único de usuario,
   pero el asistente actual usa `user_id` string. La integración con Firebase Auth no existe.
6. **Ubicación simulada**: El diseño usa `simulatedLocationId` (ubicación elegida manualmente), no
   geolocalización real. Esto puede diferir de expectativas de producto.
7. **Sin estado de revisión**: El diseño descarta explícitamente un estado de revisión entre draft y
   published. Cualquier flujo editorial futuro requeriría cambiar el esquema.

## 13. Decisions Required Before Implementation

1. **¿Compartir MongoDB entre assistant y app de noticias?** El asistente actual usa
   `assistant` database. La app de noticias necesita sus propias colecciones. ¿Misma instancia/
   misma DB/DB separada?
2. **¿Chat único o dos chats?** El `assistant/` actual es un chatbot financiero NOVU. El diseño
   propone un chat de noticias. ¿Se reutiliza el servicio, se bifurca, o se crea uno nuevo en
   `services/`?
3. **¿Firebase UID como identificador?** El diseño asume `firebaseUid`. ¿El backend debe integrar
   Firebase Auth, o usar un identificador propio?
4. **Ubicación inicial del catálogo `locations`**: ¿Qué ubicaciones concretas debe contener el
   catálogo? ¿Solo Guatemala o alcance internacional?
5. **¿Mecanismo de control de presupuesto IA?** El diseño fija 20 USD. ¿Quién/ cómo se corta el
   acceso al excederlo? ¿Alerta o bloqueo?
6. **¿Vigencia de sesiones de chat?** El diseño deja `chatSessions.expiresAt` como "Por definir".
   ¿Cuánto deben durar las sesiones?
7. **¿Prioridad de implementación?** ¿Qué colección implementar primero? Se sugiere empezar por
   `locations` + `news` (el catálogo y la entidad principal).

## 14. Proposed Engineering Loops

### Loop 01 — Conexión MongoDB para la app de noticias

| Campo | Valor |
| --- | --- |
| Loop | 01 |
| Objective | Configurar conexión MongoDB independiente para la app de noticias |
| Inputs | `docs/design/database/`, `00-discovery-result.md` |
| Expected changes | Nuevo archivo de configuración, variables de entorno, `MongoClient` |
| Verification | Health check reporta estado de conexión sin errores |
| Dependencies | Ninguna |
| Requires credentials | Sí (MONGODB_URI) |
| Destructive operations | No |
| Suggested commit | `feat: add MongoDB connection for news app` |

### Loop 02 — Catálogo `locations`

| Campo | Valor |
| --- | --- |
| Loop | 02 |
| Objective | Implementar colección `locations` con seed data |
| Inputs | `docs/design/database/01-colecciones.md`, loop anterior |
| Expected changes | Modelo `Location`, seed script, endpoint GET /locations |
| Verification | Test inserta ubicaciones y las recupera |
| Dependencies | Loop 01 |
| Requires credentials | Sí |
| Destructive operations | No |
| Suggested commit | `feat: add locations catalog` |

### Loop 03 — Colección `news`

| Campo | Valor |
| --- | --- |
| Loop | 03 |
| Objective | Implementar colección `news` con slug único, verificación, fuentes, imagen y tiempos |
| Inputs | `01-colecciones.md`, `02-criterios-de-contenido.md`, `05-tiempo-de-lectura.md` |
| Expected changes | Modelo `News`, repositorio, servicio, endpoints CRUD |
| Verification | Test crea, publica y consulta noticias |
| Dependencies | Loop 01 |
| Requires credentials | Sí |
| Destructive operations | No |
| Suggested commit | `feat: add news collection with verification and reading time` |

### Loop 04 — Colección `users` (app)

| Campo | Valor |
| --- | --- |
| Loop | 04 |
| Objective | Implementar colección `users` con onboarding e intereses inferidos |
| Inputs | `01-colecciones.md`, `03-criterios-de-personalizacion.md` |
| Expected changes | Modelo `User`, repositorio, seed, endpoint de onboarding |
| Verification | Test crea usuario, completa onboarding, registra intereses |
| Dependencies | Loop 01, Loop 02 (locations) |
| Requires credentials | Sí (Firebase o similar) |
| Destructive operations | No |
| Suggested commit | `feat: add users collection with onboarding and inferred interests` |

### Loop 05 — Colección `userInteractions`

| Campo | Valor |
| --- | --- |
| Loop | 05 |
| Objective | Implementar registro de interacciones (opened/read) |
| Inputs | `01-colecciones.md`, `03-criterios-de-personalizacion.md`, `05-tiempo-de-lectura.md` |
| Expected changes | Modelo `UserInteraction`, repositorio, endpoint POST |
| Verification | Test registra interacción y verifica contexto histórico |
| Dependencies | Loop 01, Loop 03, Loop 04 |
| Requires credentials | Sí |
| Destructive operations | No |
| Suggested commit | `feat: add user interactions tracking` |

### Loop 06 — Colecciones `chatSessions` y `aiUsage`

| Campo | Valor |
| --- | --- |
| Loop | 06 |
| Objective | Implementar chat de noticias con sesiones temporales y control de costos IA |
| Inputs | `01-colecciones.md`, `04-criterios-de-chat-y-costos.md` |
| Expected changes | Modelos `ChatSession`, `AiUsage`, endpoints de chat, control de presupuesto |
| Verification | Test crea sesión, envía mensaje, verifica registro en aiUsage |
| Dependencies | Loop 01, Loop 03, Loop 04 |
| Requires credentials | Sí (OpenAI) |
| Destructive operations | No |
| Suggested commit | `feat: add chat sessions with TTL and AI usage tracking` |

### Loop 07 — Colección `auditLogs`

| Campo | Valor |
| --- | --- |
| Loop | 07 |
| Objective | Implementar auditoría de acciones administrativas sobre noticias |
| Inputs | `01-colecciones.md`, `04-criterios-de-chat-y-costos.md` |
| Expected changes | Modelo `AuditLog`, middleware/repositorio, integración con news |
| Verification | Test registra acción y verifica campos |
| Dependencies | Loop 03, Loop 04 |
| Requires credentials | Sí |
| Destructive operations | No |
| Suggested commit | `feat: add audit logs for news administrative actions` |
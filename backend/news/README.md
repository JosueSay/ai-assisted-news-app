# Módulo de base de datos — AI Assisted News App

## Propósito

Infraestructura mínima, independiente y segura para conectar la aplicación de noticias a su
propia base de datos MongoDB, ya sea local con Docker o en MongoDB Atlas.

**No** depende del asistente existente (`backend/assistant/`).
Incluye una API HTTP local de lectura para el frontend.
Los modelos representan el esquema lógico y el paquete `schema/` materializa la estructura física
de forma no destructiva: colecciones, validators e índices.

## Estructura

```text
backend/news/
├── __init__.py              # Docstring del módulo
├── config.py                # Configuración no secreta (NewsSettings)
├── secret_loader.py         # Carga segura de secretos desde archivos
├── database.py              # Conexión MongoDB (cliente, ping, cierre)
├── check_config.py          # Verificación de configuración (CLI)
├── ping.py                  # Prueba de conectividad (CLI)
├── api.py                   # API HTTP local de noticias
├── seed_demo.py             # Seeder idempotente de noticias demo locales
├── models/
│   ├── __init__.py          # Enums compartidos
│   ├── reading_time.py      # Cálculo de tiempo de lectura
│   ├── location.py          # Catálogo de ubicaciones
│   ├── user.py              # Usuarios con onboarding e intereses
│   ├── news.py              # Noticias con verificación, fuentes, imagen
│   ├── user_interaction.py  # Registro de interacciones de lectura
│   ├── chat_session.py      # Sesiones temporales de chat
│   ├── ai_usage.py          # Consumo de IA y control de presupuesto
│   └── audit_log.py         # Auditoría de acciones administrativas
├── schema/
│   ├── collections.py       # Lista canónica de colecciones
│   ├── validators.py        # MongoDB $jsonSchema validators
│   ├── indexes.py           # Índices esperados, únicos y TTL
│   ├── initialize.py        # Inicialización idempotente no destructiva
│   └── check.py             # Verificación de drift del esquema
├── README.md
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_secret_loader.py        # 8 tests
    ├── test_config.py               # 4 tests
    ├── test_database.py             # 6 tests
    ├── test_check_config.py         # 3 tests
    ├── test_reading_time.py         # 8 tests
    ├── test_location_model.py       # 5 tests
    ├── test_user_model.py           # 9 tests
    ├── test_news_model.py           # 20 tests
    ├── test_user_interaction_model.py  # 9 tests
    ├── test_chat_session_model.py   # 12 tests
    ├── test_ai_usage_model.py       # 9 tests
    ├── test_audit_log_model.py      # 6 tests
    ├── test_schema_definitions.py
    ├── test_schema_initialize.py
    └── test_schema_check.py
```

## Siete colecciones

| Colección | Naturaleza | Estado actual |
| --- | --- | --- |
| `locations` | Catálogo precargado | Modelo implementado (Loop 02) |
| `users` | Persistente | Modelo implementado (Loop 02) |
| `news` | Persistente | Modelo implementado (Loop 02) |
| `userInteractions` | Persistente | Modelo implementado (Loop 02) |
| `chatSessions` | Temporal con TTL | Modelo implementado (Loop 02) |
| `aiUsage` | Persistente | Modelo implementado (Loop 02) |
| `auditLogs` | Persistente | Modelo implementado (Loop 02) |

Loop 03 materializa estas colecciones en MongoDB mediante validators e índices.

## Dependencias

- Python 3.10+
- PyMongo
- python-dotenv
- Pydantic

## Configuración

### 1. Crear el `.env` raíz

```bash
make env-local
# o:
make env-atlas
```

Ese archivo vive en la raíz del proyecto, junto a `docker-compose.yml` y `Makefile`.

Para desarrollo local sin Atlas:

```dotenv
NEWS_DB_MODE=local
COMPOSE_PROFILES=news-local
NEWS_MONGODB_DATABASE=ai_assisted_news
NEWS_MONGODB_REQUIRED=true
NEWS_MONGODB_TIMEOUT_MS=5000
NEWS_LOCAL_MONGO_PORT=27018
```

Para usar Atlas:

```dotenv
NEWS_DB_MODE=atlas
COMPOSE_PROFILES=
NEWS_MONGODB_URI_FILE=keys/mongodb_uri
NEWS_MONGODB_DATABASE=ai_assisted_news
NEWS_MONGODB_REQUIRED=true
NEWS_MONGODB_TIMEOUT_MS=5000
NEWS_LOCAL_MONGO_PORT=27018
```

`make env-atlas` no escribe la URI de MongoDB en `.env`; solo deja la ruta hacia
`keys/mongodb_uri`.

### 2. Preparar secretos si usas Atlas

```bash
make setup-keys
```

Esto crea `keys/mongodb_uri`, `keys/client_id` y `keys/client_secret` si no existen. En modo
Atlas, completa manualmente `keys/mongodb_uri` con la URI de conexión.

En modo local, `keys/mongodb_uri` no se necesita.

Ver `keys/README.md` para más detalles.

Variables disponibles:

| Variable | Default | Descripción |
| --- | --- | --- |
| `NEWS_DB_MODE` | `local` en Makefile/Compose | `local` usa MongoDB Docker; `atlas` usa `keys/mongodb_uri` |
| `COMPOSE_PROFILES` | — | En local debe incluir `news-local`; en Atlas debe quedar vacío |
| `NEWS_MONGODB_DATABASE` | `ai_assisted_news` | Nombre de la base de datos |
| `NEWS_MONGODB_URI_FILE` | `keys/mongodb_uri` | Ruta al archivo con la URI de Atlas |
| `NEWS_MONGODB_LOCAL_URI` | `mongodb://news-mongo:27017/...` en Compose | URI interna del servicio local |
| `NEWS_MONGODB_REQUIRED` | `true` | Si es obligatoria para operar |
| `NEWS_MONGODB_TIMEOUT_MS` | `5000` | Timeout de conexión en ms |
| `NEWS_LOCAL_MONGO_PORT` | `27018` | Puerto del MongoDB local expuesto al host |

## Comandos disponibles (Makefile)

```bash
make env-local          # Crea/reemplaza .env para MongoDB local
make env-atlas          # Crea/reemplaza .env para Atlas sin incluir la URI
make setup-keys        # Prepara archivos de secretos faltantes
make db-check-config   # Verifica configuración sin exponer secretos
make db-ping           # Prueba conectividad MongoDB
make db-init           # Crea colecciones, validators e índices faltantes
make db-seed-demo      # Inserta/actualiza datos ficticios para prueba local
make db-schema-check   # Verifica drift de colecciones, validators e índices
make db-test           # Ejecuta tests unitarios dentro de Docker Compose
make news-db-up        # Levanta solo el MongoDB local de noticias
make news-db-down      # Detiene solo el MongoDB local de noticias
make news-api-up       # Levanta la API local de noticias
```

Todos estos comandos pasan por `docker-compose.yml`. En modo local, el Makefile levanta
`news-mongo` antes de ejecutar la tarea. En modo Atlas, no levanta `news-mongo` y usa la URI
guardada en `keys/mongodb_uri`.

## API local

En Docker Compose la API escucha en:

```text
http://localhost:8020
```

Endpoints:

```text
GET /health
GET /news
GET /news/{slug}
```

`/news` devuelve documentos adaptados al contrato del frontend. No cambia la estructura de la
base: lee desde `news`, busca el autor en `users` y deriva la categoría desde `news.topics`.

## Prueba local con frontend

```bash
make db-init
make db-seed-demo
docker compose up -d --build frontend
```

Luego abrir:

```text
http://localhost:8081
```

El frontend usa `EXPO_PUBLIC_NEWS_API_BASE_URL=http://localhost:8020`. Si la API no responde,
muestra un estado de error. El frontend no mantiene un dataset local como fallback.

## Separación respecto de assistant/

- `backend/news/` es independiente de `backend/assistant/`.
- La base de datos por defecto es `ai_assisted_news`, no `assistant`.
- No reutiliza modelos, repositorios ni configuración del asistente.
- No modifica `backend/assistant/` en absoluto.

## Seguridad

- `db-ping` nunca muestra la URI.
- `db-check-config` solo reporta `configured` / `missing` / `invalid`.
- `db-ping` no crea colecciones, no inserta ni modifica datos.
- `db-init` no inserta ni elimina documentos. Tampoco elimina índices: si encuentra un índice
  incompatible con el mismo nombre, falla para que se revise manualmente.
- `db-seed-demo` hace upsert de documentos ficticios de prueba y no elimina colecciones,
  documentos ni índices.

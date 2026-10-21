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
├── firebase_auth.py         # Verificación de Firebase ID tokens sin service-account key
├── user_accounts.py         # Resolución de users por UID Firebase verificado
├── seed_catalog.py        # Seeder idempotente del catálogo locations (16 países)
├── seed_demo.py           # Seeder idempotente de noticias demo locales
├── demo_news.py           # Generador determinista de 32 noticias demo (Loop 05)
├── seed_news.py           # Seeder idempotente de noticias demo por slug (Loop 05)
├── news_check.py          # Inspección no destructiva del dataset demo (Loop 05)
├── demo_images.py         # Catálogo versionado de imágenes Commons (Loop 08)
├── news_images_check.py   # Check HTTP online de las URLs de imagen (Loop 08)
├── reseed.py              # Reseed seguro del dataset controlado: ownership, preflight, deletes por _id, confirmación (Loop 06)
├── reseed_dry_run.py      # CLI no destructivo del plan de reseed (Loop 06)
├── bootstrap.py           # Bootstrap idempotente: init + seeds + checks, sin deletes (Loop 06)
├── verify.py              # Verificación integral solo-lectura: schema + catálogos + demo news (Loop 06)
├── topics.py              # Catálogo estático versionado de topics (no es colección)
├── seed_check.py          # Inspección no destructiva del catálogo locations
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
    ├── test_schema_check.py
    ├── test_topics.py             # catálogo estático de topics
    ├── test_catalog_data.py       # datos locations contra el modelo Location
    ├── test_seed_catalog.py       # seeder idempotente por countryCode
    ├── test_seed_check.py         # inspección no destructiva del catálogo
    ├── test_demo_news.py          # generador determinista de 32 noticias demo
    ├── test_seed_news.py          # seeder idempotente por slug (solo news)
    ├── test_news_check.py         # inspección no destructiva del dataset demo
    ├── test_news_images_check.py  # check HTTP de imágenes sin red real
    ├── test_reseed.py             # reseed seguro: confirmación, ownership, dry-run, orden, preservación, fallos (Loop 06)
    ├── test_bootstrap.py          # bootstrap idempotente sin deletes (Loop 06)
    ├── test_verify.py             # verificación solo-lectura y sus drifts (Loop 06)
    ├── test_api.py                # adaptación de documentos MongoDB a la API
    ├── test_api_firebase_auth.py  # identidad y autorización de rutas protegidas
    ├── test_firebase_auth.py      # validación offline de claims/token
    ├── test_user_accounts.py      # upsert seguro por UID Firebase
    └── test_seed_demo.py          # seeder demo legacy con upsert (preexistente, previo al Loop 05)
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

Loop 04 agrega los datos base reproducibles: el catálogo `locations` (16 países a
nivel `country`, identidad natural `countryCode`) se siembra con
`make db-seed-catalogs` de forma idempotente (solo inserta faltantes, nunca
modifica ni elimina) y se inspecciona sin escribir con `make db-seed-check`. El
 catálogo de topics es estático y versionado en `topics.py`: no es colección
 MongoDB y los modelos aún no validan contra él de forma cerrada (decisión
 pendiente documentada en `docs/design/database/09-catalogos-y-seeders.md`).

 Loop 05 agrega el dataset reproducible de noticias demo: `demo_news.py`
 genera exactamente 32 noticias sintéticas (DEMO / SYNTHETIC DATA, 2 por país
 a nivel `country`, 28 `published` / 4 `draft`, 4 verification statuses, 14
 topics cubiertos, tiempos de lectura coherentes) de forma determinista y sin
 MongoDB; `make db-seed-news` las persiste de forma idempotente por `slug`
 (solo escribe en `news`, nunca crea users: `authorId` es un identificador
 sintético documentado pendiente de correspondencia real) y
 `make db-news-check` inspecciona el dataset sin modificarlo. Detalle en
 `docs/design/database/10-generador-noticias-demo.md`.

 Loop 08 sustituye los placeholders por imágenes reales de Wikimedia Commons
 con procedencia, crédito y derechos verificados. El catálogo vive en
 `demo_images.py`; `make db-news-images-check` comprueba por HTTP (HEAD, sin
 descargar el cuerpo) que las URLs responden con `Content-Type: image/*`. Es
 online y no usa MongoDB ni secretos. Detalle en
 `docs/design/database/13-imagenes-demo.md`.

## Dependencias

- Python 3.10+
- PyMongo
- google-auth (verificación de firma Firebase por certificados públicos)
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

Esto crea `keys/mongodb_uri` y `keys/openai_api_key` si no existen. En modo Atlas,
completa manualmente `keys/mongodb_uri` con la URI de conexión.

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
| `NEWS_FIREBASE_PROJECT_ID` | vacío | Project ID esperado al verificar Firebase ID tokens |

## Comandos disponibles (Makefile)

```bash
make env-local          # Crea/reemplaza .env para MongoDB local
make env-atlas          # Crea/reemplaza .env para Atlas sin incluir la URI
make setup-keys        # Prepara archivos de secretos faltantes
make db-check-config   # Verifica configuración sin exponer secretos
make db-ping           # Prueba conectividad MongoDB
make db-init           # Crea colecciones, validators e índices faltantes
make db-seed-catalog    # Alias: siembra el catálogo locations (idempotente)
make db-seed-catalogs   # Siembra únicamente catálogos autorizados (idempotente)
make db-seed-check      # Inspecciona el catálogo sin modificar la base
make db-seed-demo      # Inserta/actualiza datos ficticios para prueba local
make db-seed-news      # Siembra el dataset demo de 32 noticias (idempotente, solo news)
make db-news-check      # Inspecciona el dataset demo sin modificar la base
make db-news-images-check  # Comprueba por HTTP las URLs de imagen (online, sin DB)
make db-schema-check   # Verifica drift de colecciones, validators e índices
make db-bootstrap      # Init + catálogos + demo news + checks (idempotente, sin confirmación)
make db-verify         # Verificación integral solo-lectura (schema + catálogos + demo news)
make db-reseed-dry-run # Plan real de reseed sin escribir nada
make db-reseed CONFIRM="RESEED ai_assisted_news"  # Reseed controlado (local; en Atlas la frase es RESEED ATLAS <db>)
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
GET /auth/me                 # Bearer Firebase ID token requerido; resuelve users.firebaseUid
POST /admin/news             # Bearer Firebase ID token + users.role=admin requerido
```

La verificación valida firma, audience, issuer, expiración y Project ID con los
certificados públicos de Firebase. No requiere service-account JSON ni permisos IAM
para verificar firmas. `/auth/me` crea un usuario regular si no existe; el rol no se
toma del token ni del request.

`/news` devuelve documentos adaptados al contrato del frontend. No cambia la estructura de la
base: lee desde `news`, busca el autor en `users` y deriva la categoría desde `news.topics`.

## Prueba local con frontend

```bash
make db-bootstrap
make db-verify
docker compose up -d --build news-api chatbot frontend
```

Luego abrir:

```text
http://localhost:8081
```

El frontend usa `EXPO_PUBLIC_NEWS_API_BASE_URL=http://localhost:8020`. Si la API no responde,
muestra un estado de error. El frontend no mantiene un dataset local como fallback.

## Separación respecto de assistant/

- `backend/news/` conserva su DB independiente de `backend/assistant/`; el modo news del
  chat reutiliza deliberadamente el verificador Firebase y los modelos de este módulo.
- La base de datos por defecto es `ai_assisted_news`, no `assistant`.
- No reutiliza la base `assistant`, colecciones ni repositorios históricos.
- La autenticación del chat news comparte el Firebase ID token; los otros modos del assistant
  (`projection` y `novu`) conservan su comportamiento.

## Seguridad

- `db-ping` nunca muestra la URI.
- `db-check-config` solo reporta `configured` / `missing` / `invalid`.
- `db-ping` no crea colecciones, no inserta ni modifica datos.
- `db-init` no inserta ni elimina documentos. Tampoco elimina índices: si encuentra un índice
  incompatible con el mismo nombre, falla para que se revise manualmente.
- `db-seed-demo` hace upsert de documentos ficticios de prueba y no elimina colecciones,
  documentos ni índices.
- `db-seed-news` solo inserta noticias demo faltantes por `slug` en `news`: nunca
  modifica ni elimina documentos, nunca escribe en otras colecciones y nunca crea users.
- `db-bootstrap` y `db-verify` nunca eliminan: el primero solo asegura schema e inserta
  faltantes, el segundo solo lee.
- `db-reseed-dry-run` nunca escribe: solo inspecciona y reporta el plan.
- `db-reseed` elimina únicamente documentos controlados verificados por ownership
  (`countryCode`+`_id` determinista, `slug`+`_id` determinista) mediante
  `delete_many({"_id": {"$in": [...]}})`; nunca `delete_many({})`, nunca filtros
  amplios, nunca `drop`. Requiere `CONFIRM` con la frase exacta del modo
  (`RESEED <db>` en local, `RESEED ATLAS <db>` en Atlas); sin ella aborta sin
  modificar nada. No existe `--force`. Detalle en
  `docs/design/database/11-automatizacion-y-reseed.md`.


## Contrato compartido de API y chat

La API conserva todos los topics, fuentes, verificación, alcance geográfico y
metadatos de imagen/IA de los modelos aprobados. El chat reutiliza esos modelos
y el catálogo de 14 topics. `make news-contract` genera el catálogo/tipos Expo;
`make news-contract-check` detecta drift sin DB ni credenciales. El detalle por
slug permite abrir citas fuera de la página del feed.

Publicación y chat usan la misma identidad Firebase verificada. Para habilitar una
cuenta admin, primero inicia sesión y deja que `/auth/me` cree su usuario; después
una persona autorizada asigna `users.role=admin` en MongoDB. Los usuarios provisionales
se conservan sin asociación automática. Ver
[contrato compartido](../../docs/architecture/contrato-compartido-noticias.md).

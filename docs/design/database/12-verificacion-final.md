# Verificación final y reproducibilidad

Parte de la [documentación de base de datos](README.md).

Cierre formal del trabajo de diseño e infraestructura de base de datos de AI Assisted News App
(Loop 07). Este documento es el punto de entrada técnico para nuevos desarrolladores: resume el
estado final verificado, cómo reproducirlo desde cero y qué decisiones quedan pendientes.

Este loop **no agrega funcionalidades**. Solo audita, demuestra reproducibilidad y documenta.

## Estado final verificado

| Área | Estado |
| --- | --- |
| Colecciones | 7/7 (`locations`, `users`, `news`, `userInteractions`, `chatSessions`, `aiUsage`, `auditLogs`) |
| Validators | 7/7 con `validationLevel: strict`, `validationAction: error` |
| Índices | 10/10 (2 únicos, 1 TTL, 7 de consulta) |
| TTL | `chatSessions.expiresAt` con `expireAfterSeconds: 0` (vigencia 3600 s) |
| Catálogo | 16/16 locations, 0 duplicados |
| Demo news | 32/32, 16/16 países, 28 published / 4 draft, 0 duplicados, 0 externas |
| Local | schema OK, verify OK |
| Atlas | schema OK, verify OK (solo operaciones no destructivas) |
| Tests | 204 passed, 0 failed |

No existe colección MongoDB `topics`: es un catálogo estático versionado en
`backend/news/topics.py`. No existe ninguna colección añadida "por si acaso".

## Arquitectura

```text
docs/design/database/          diseño aprobado (documentos 01–12)
        ↕
backend/news/models/           esquema lógico (Pydantic, validación y serialización, no es ODM)
        ↕
backend/news/schema/           esquema físico (validators $jsonSchema, índices, init/check)
        ↕
seeders/generador              backend/news/seed_catalog.py, seed_news.py, demo_news.py, topics.py
        ↕
automatización                 backend/news/bootstrap.py, verify.py, reseed.py + Makefile
        ↕
tests                          backend/news/tests/ (offline, sin Atlas)
```

Base de datos independiente: `ai_assisted_news`, nunca `assistant`. Sin ODM (PyMongo directo).
`backend/news/` no depende de `backend/assistant/` ni lo modifica.

## Las siete colecciones

Detalle campo por campo en [01 Colecciones](01-colecciones.md); diagrama en
[07 Diagrama](07-diagrama.md).

| Colección | Naturaleza | Clave lógica |
| --- | --- | --- |
| `locations` | Catálogo precargado | `countryCode` (identidad natural, sin índice único: decisión pendiente) |
| `users` | Persistente | `firebaseUid` UNIQUE |
| `news` | Persistente | `slug` UNIQUE |
| `userInteractions` | Persistente | `userId` + `newsId` + `type` |
| `chatSessions` | Temporal con TTL | `expiresAt` (3600 s) |
| `aiUsage` | Persistente | control del presupuesto de 20 USD |
| `auditLogs` | Persistente | solo acciones sobre `news` |

MongoDB no impone foreign keys; las referencias (`authorId`, `simulatedLocationId`,
`locationIds`, `citedNewsIds`, …) son lógicas mediante `ObjectId`.

## Validators e índices

Fuente ejecutable en `backend/news/schema/`. Detalle en
[08 Índices y validación](08-indices-y-validacion.md).

- 7 validators `$jsonSchema`, política `strict` / `error`.
- Únicos: `uq_users_firebase_uid`, `uq_news_slug`.
- TTL: `ttl_chat_sessions_expires_at` (`expireAfterSeconds: 0`).
- Consulta: 3 en `news` (status, ubicación, topics), 2 en `userInteractions`, 1 en `aiUsage`,
  1 en `auditLogs`.
- `make db-init` es idempotente y no destructivo; `make db-schema-check` verifica drift sin
  escribir.

## Catálogos

Detalle en [09 Catálogos y seeders](09-catalogos-y-seeders.md).

- **locations**: 16 países a nivel `country` (8 América, 2 Europa, 2 Asia, 2 África, 2 Oceanía).
  Identidad natural `countryCode`; seeder idempotente por código con `_id` determinista solo en
  inserción; nunca modifica ni elimina.
- **topics**: 14 valores estáticos (`actualidad`, `tecnologia`, …, `internacional`). Los modelos
  mantienen strings libres (validación cerrada pendiente, no resuelta en este loop).

## Dataset demo

Detalle en [10 Generador de noticias demo](10-generador-noticias-demo.md).

- 32 noticias sintéticas (DEMO / SYNTHETIC DATA), 2 por país, nivel `country`.
- 28 `published` / 4 `draft` (MX, ES, JP, ZA); 4 verification statuses; 14 topics cubiertos;
  5 tipos de imagen; tiempos de lectura coherentes (200 ppm, mínimo 1).
- Generador puro y determinista (`demo_news.py`); seeder idempotente por `slug` que solo
  escribe en `news` y nunca crea users.
- `authorId` es un identificador sintético determinista pendiente de correspondencia con un
  `users` real (decisión pendiente, no resuelta en este loop).

## Automatización

Detalle en [11 Automatización y reseed](11-automatizacion-y-reseed.md). Fuente en
`backend/news/*.py` y `Makefile`.

### Comandos seguros (no destructivos)

```text
make setup-keys            bootstrap de secretos (idempotente, no sobrescribe)
make db-check-config       verifica configuración sin exponer secretos
make db-ping               prueba conectividad
make db-init               crea colecciones/validators/índices faltantes
make db-schema-check       verifica drift del esquema (solo lectura)
make db-seed-catalogs      siembra 16 locations (idempotente)
make db-seed-check         inspecciona catálogo (solo lectura)
make db-seed-news          siembra 32 news demo (idempotente)
make db-news-check         inspecciona dataset demo (solo lectura)
make db-bootstrap          init + seeds + checks (idempotente, sin confirmación)
make db-verify             verificación integral (solo lectura)
make db-reseed-dry-run     plan real de reseed sin escribir nada
make db-test               suite offline (204 tests)
```

No existen `db-reset`, `db-drop`, `db-clean` ni equivalentes.

### Comando destructivo (único)

```bash
make db-reseed CONFIRM="RESEED ai_assisted_news"              # local
make db-reseed NEWS_DB_MODE=atlas COMPOSE_PROFILES= CONFIRM="RESEED ATLAS ai_assisted_news"  # Atlas
```

- Elimina **únicamente** las 16 locations y 32 news controladas verificadas por ownership
  (`countryCode`+`_id`, `slug`+`_id`); preserva users, interacciones, chats, aiUsage, auditLogs
  y documentos externos.
- Deletes exclusivamente con `delete_many({"_id": {"$in": [...]}})`; nunca `delete_many({})`,
  nunca filtros amplios, nunca `drop`.
- Requiere frase exacta diferenciada por modo; sin coincidencia aborta con cero modificaciones.
- Orden: elimina news → locations; reconstruye locations → news; luego checks.

## Reproducibilidad demostrada (Loop 07)

Reconstrucción desde cero con DB local temporal y aislada
(`ai_assisted_news_verification`), sin tocar la DB local normal y sin usar Atlas:

```text
DB inexistente
→ db-bootstrap  →  Locations inserted: 16, News inserted: 32, Bootstrap: OK
→ db-verify     →  Database verification: OK (schema, catalogs, demo news)
→ conteo directo: 7 colecciones, 16 locations, 32 news
→ segundo db-bootstrap  →  inserted 0 / unchanged 16 y 32, Bootstrap: OK
→ db-verify     →  OK
→ limpieza: dropDatabase solo de ai_assisted_news_verification (explícita y verificada)
→ DB normal intacta: 16 locations, 32 news
```

La DB temporal se eliminó únicamente porque estaba inequívocamente identificada como la creada
por esta sesión; la DB normal nunca recibió operaciones destructivas.

## Setup de nuevo desarrollador

```bash
git clone ...
make setup-keys        # crea keys/mongodb_uri, keys/news_admin_password,
                       # keys/client_id, keys/client_secret si faltan (vacíos, sin sobrescribir)

# completar secretos cuando corresponda (modo Atlas: keys/mongodb_uri)

make db-check-config   # sin exponer secretos
make db-bootstrap      # init + catálogos + demo news + checks
make db-verify         # verificación integral
```

- Modo local (`NEWS_DB_MODE=local`): funciona sin Atlas; MongoDB local en el puerto 27018.
- Modo Atlas (`NEWS_DB_MODE=atlas`): usa la URI de `keys/mongodb_uri`; nunca ejecutar
  `db-reseed` contra Atlas sin autorización explícita.
- `make env-local` / `make env-atlas` generan el `.env` raíz (parametrización no secreta;
  la URI real vive solo en `keys/`).

## Seguridad

- Secretos solo en `keys/` (ignorado por Git salvo `keys/README.md`); `.env` solo
  parametrización no secreta. Ningún valor secreto versionado ni expuesto en logs, tests,
  handoffs o commits.
- El agente nunca lee el contenido de `keys/`; solo verifica existencia/estado
  (`configured` / `missing` / `invalid`).
- Docker monta `keys/` como solo lectura (`:ro`) en `news-tools` y `news-api`.
- Escaneo de secretos sobre rutas acotadas (`backend/news`, `Makefile`,
  `docs/design/database`, `docker-compose.yml`, `.env.example`): únicamente 9 hallazgos
  `mongodb-uri` preexistentes del baseline (URIs internas `mongodb://…:27017/…` y fixtures de
  test sin credenciales reales); 0 hallazgos nuevos. `keys/` nunca escaneado.
- Modelo de amenazas (abuso → mitigación): reseed en modo equivocado → frases de confirmación
  diferenciadas + modo visible; confirmación vacía/automática → match exacto, sin default
  autorizante; borrado de documento externo → ownership exige identidad completa, drift aborta;
  borrado masivo → solo `_id $in` versionado, sin `drop`; secreto en logs → outputs solo con
  conteos; fallo parcial → estado `incomplete` honesto sin claim de rollback, recuperación vía
  `db-bootstrap`.
- Atlas no recibió operaciones destructivas durante este loop (solo `db-verify`).

## Tests

```bash
make db-test   # 204 passed, 0 failed (offline, sin credenciales)
```

Cubre infraestructura, configuración, modelos y lectura, definiciones de esquema,
inicialización y drift, catálogos, dataset demo, bootstrap, verify y reseed (confirmación,
ownership, orden, preservación, fallos). Los tests que requerirían Atlas están separados: la
suite normal nunca depende de credenciales reales.

## Code review (Loop 07)

Revisión integral del sistema DB con `.skills/code-reviewer` (correctness, safety,
mantenibilidad, performance, tests). Sin BLOCKER ni MAJOR.

- **MINOR**: `backend/news/seed_demo.py` + `make db-seed-demo` son legacy previos al Loop 05
  (5 noticias + demo user con upsert). Si se ejecutan, `db-news-check`/`db-verify` reportan
  drift (externos preservados, nunca borrados). No se eliminan en este loop por ser cambio de
  comportamiento fuera de alcance; ver follow-ups.
- **FOLLOW-UP**: ver decisiones pendientes abajo.

## Decisiones pendientes (no resueltas, por diseño)

Se auditan y se dejan documentadas; resolverlas requeriría decisión humana explícita:

1. **Índice único en `locations.countryCode`**: no existe. El seed concurrente podría duplicar
   (uso previsto: un operador por Makefile). Pendiente con el esquema físico.
2. **Validación cerrada de topics**: el catálogo existe y los seeders lo usan, pero los modelos
   mantienen strings libres. Convertirlo en enum cerrado es cambio funcional.
3. **`authorId` sintético**: el dataset demo usa `DEMO_NEWS_AUTHOR_ID` sin user persistido. La
   autoría real queda para el flujo editorial futuro.
4. **`geographicScope` international dedicado**: el dataset cubre solo el nivel `country`;
   probar `international` requeriría ampliar el dataset más allá de 32.
5. **Legacy `seed_demo.py` / `db-seed-demo`**: previo al dataset vigente; evaluar deprecar o
   documentar su interacción con `db-verify`.

## Trazabilidad

| Elemento | Estado |
| --- | --- |
| colecciones, modelos, embebidos, validators, índices, TTL, access patterns | sincronizados |
| locations, topics, demo news, reading time | sincronizados |
| seeders, checks, bootstrap, verify, reseed | sincronizados |
| tests (204), documentación (01–12), diagrama, Makefile, Docker | sincronizados |
| secrets/bootstrap (`setup-keys`, `keys/README.md`) | sincronizados |
| handoffs 00–06 | existentes, no modificados |

## Mapa de documentos

| Documento | Contenido |
| --- | --- |
| [01](01-colecciones.md) – [06](06-decisiones-descartadas.md) | Diseño lógico y criterios |
| [07](07-diagrama.md) | Diagrama Mermaid vigente |
| [08](08-indices-y-validacion.md) | Estructura física MongoDB |
| [09](09-catalogos-y-seeders.md) | Catálogos e idempotencia |
| [10](10-generador-noticias-demo.md) | Dataset sintético de 32 noticias |
| [11](11-automatizacion-y-reseed.md) | Bootstrap, verify, reseed seguro |
| 12 (este documento) | Cierre, reproducibilidad y entrada para nuevos desarrolladores |

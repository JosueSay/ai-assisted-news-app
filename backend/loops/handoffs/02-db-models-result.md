# Loop 02 — Database Models Result

## 1. Resultado

Completed.

Se implementó el esquema lógico completo de AI Assisted News App mediante modelos Pydantic
independientes de MongoDB Atlas. No se crearon colecciones, índices, repositorios, endpoints ni
datos.

## 2. Models Implemented

| Colección | Modelo | Documentos embebidos |
| --- | --- | --- |
| `locations` | `Location` | — |
| `users` | `User` | `Onboarding`, `InferredInterest` |
| `news` | `News` | `GeographicScope`, `Verification`, `Source`, `Image`, `AiAssistance` |
| `userInteractions` | `UserInteraction` | `InteractionContext` |
| `chatSessions` | `ChatSession` | `Message`, `ResponseMetadata` |
| `aiUsage` | `AiUsage` | — |
| `auditLogs` | `AuditLog` | — |

Los enums compartidos están en `backend/news/models/__init__.py`. Todos usan valores string
estables y restringen los catálogos aprobados.

## 3. Model Structure

```text
backend/news/
├── models/
│   ├── __init__.py
│   ├── reading_time.py
│   ├── location.py
│   ├── user.py
│   ├── news.py
│   ├── user_interaction.py
│   ├── chat_session.py
│   ├── ai_usage.py
│   └── audit_log.py
└── tests/
    ├── test_reading_time.py
    ├── test_location_model.py
    ├── test_user_model.py
    ├── test_news_model.py
    ├── test_user_interaction_model.py
    ├── test_chat_session_model.py
    ├── test_ai_usage_model.py
    └── test_audit_log_model.py
```

## 4. Validation Rules

- Identificadores MongoDB representados como `ObjectId`, serializables con `model_dump_mongo()`.
- Enums restringidos para niveles geográficos, roles, estados de noticia/verificación, fuentes,
  imágenes, interacciones, chat, IA y auditoría.
- `InferredInterest.score` acepta únicamente el rango inclusivo de 0 a 1.
- `Source.url` e `Image.url` aceptan únicamente URLs HTTP(S) con host, sin hacer requests.
- La imagen `none` requiere `url` y `alt` nulos.
- Las imágenes `ai_generated` y `ai_modified` requieren `aiDisclosure` no vacío.
- `AiAssistance.imageGenerated` es coherente con `Image.type == ai_generated`.
- `draft` exige `publishedAt = null`; `published` exige `publishedAt`, `wordCount` y
  `estimatedReadingMinutes` coherentes con el contenido.
- `UserInteraction` restringe `type` a `opened`/`read` y rechaza duración o posición negativas.
- `ResponseMetadata.aiUsed` solo es verdadero para estrategia `llm`; la metadata no puede estar
  en mensajes de rol `user`.
- Tokens y costo de `AiUsage` no pueden ser negativos.
- `AuditLog.entityType` acepta únicamente `news`.

## 5. Reading Time

`backend/news/models/reading_time.py` contiene funciones puras:

- `count_words(content)`
- `estimate_reading_minutes(word_count)`
- `compute_reading_time(content)`

La fórmula aplicada es `ceil(wordCount / 200)`, con mínimo de un minuto. `News.recompute_reading_time()` actualiza los dos campos derivados y `updatedAt`. Ocho tests cubren conteo, espacios, límite de 200 palabras, redondeo y cálculo integrado.

## 6. Database Diagram

Creado `docs/design/database/07-diagrama.md` con Mermaid.

Incluye las siete colecciones, todos los documentos embebidos principales, las referencias
lógicas `ObjectId`, campos únicos conceptuales, catálogo `locations`, datos generados por uso y
el TTL futuro de 3600 segundos de `chatSessions`. Aclara que MongoDB no impone foreign keys.

## 7. Secrets Bootstrap

Se agregó `make setup-keys`.

- Crea `keys/` cuando falta.
- Crea vacíos solamente `keys/mongodb_uri`, `keys/client_id` y `keys/client_secret` si no existen.
- No sobrescribe ni lee archivos existentes, incluidos enlaces simbólicos.
- No crea `mongodb_username` ni `mongodb_password`.
- `keys/README.md` documenta los tres archivos y deja claro que los dos secretos de cliente están reservados y no se consumen.

Resultado observado en la primera ejecución:

```text
keys/mongodb_uri       EXISTS
keys/client_id         CREATED
keys/client_secret     CREATED
```

La segunda y tercera ejecución reportaron los tres archivos como `EXISTS`; por tanto el target es idempotente. No se leyeron ni mostraron contenidos de secretos.

## 8. Tests

Comando final ejecutado:

```bash
make db-test
```

Resultado:

```text
99 passed in 0.21s
```

La suite incluye los 21 tests de infraestructura del Loop 01 y 78 pruebas adicionales de modelos y tiempo de lectura. Todas son offline: no acceden a `keys/`, Atlas ni servicios externos.

También se ejecutó:

```bash
make setup-keys
make setup-keys
```

para verificar idempotencia del bootstrap.

## 9. Traceability Verification

| Elemento | Estado | Verificación |
| --- | --- | --- |
| models | Sincronizado | Siete colecciones, campos, ObjectId, enums y embebidos aprobados |
| documentation | Sincronizada | `backend/news/README.md`, `keys/README.md` y README de diseño actualizados |
| diagram | Sincronizado | `07-diagrama.md` refleja modelos y referencias implementadas |
| tests | Sincronizados | 99 pruebas cubren infraestructura, modelos, enums y validaciones |
| Makefile | Sincronizado | Mantiene `db-*` y agrega `setup-keys` |
| secrets/bootstrap | Sincronizado | Tres archivos requeridos, sin duplicar credenciales MongoDB |

## 10. Atlas

```text
collections created: NO
documents inserted: NO
destructive operations: NO
```

No se ejecutó `make db-ping`; la conectividad Atlas ya había sido comprobada manualmente antes de este loop. Los modelos y tests no establecen conexiones MongoDB.

## 11. Security

```text
secret values exposed: NO
secret files tracked: NO
assistant modified: NO
```

- `.gitignore` mantiene `keys/*` ignorado, con excepción intencional para `keys/README.md`.
- `git ls-files` no devuelve `keys/mongodb_uri`, `keys/client_id` ni `keys/client_secret`.
- No hay lectura ni consumo de `client_id` o `client_secret` en el código Python.
- No se modificó ningún archivo bajo `backend/assistant/`.

## 12. Files Changed

```text
Makefile
backend/news/README.md
backend/news/models/__init__.py
backend/news/models/reading_time.py
backend/news/models/location.py
backend/news/models/user.py
backend/news/models/news.py
backend/news/models/user_interaction.py
backend/news/models/chat_session.py
backend/news/models/ai_usage.py
backend/news/models/audit_log.py
backend/news/tests/test_check_config.py
backend/news/tests/test_config.py
backend/news/tests/test_reading_time.py
backend/news/tests/test_location_model.py
backend/news/tests/test_user_model.py
backend/news/tests/test_news_model.py
backend/news/tests/test_user_interaction_model.py
backend/news/tests/test_chat_session_model.py
backend/news/tests/test_ai_usage_model.py
backend/news/tests/test_audit_log_model.py
docs/design/database/README.md
docs/design/database/07-diagrama.md
keys/README.md
backend/loops/handoffs/02-db-models-result.md
```

## 13. Decisions

- Se usó Pydantic, ya disponible de forma coherente en el backend, solo como validación y serialización de documentos; no es un ODM.
- Los enums residen en `backend/news/models/__init__.py` para evitar duplicar strings persistidos.
- La configuración de sesión usa 3600 segundos, valor fijado por `AGENTS.md` y Loop 02; se actualizó el parámetro documental que aún indicaba "Por definir".
- `lastLoginAt` se representa como fecha siempre presente, conforme al diseño de colecciones.

## 14. Blockers

Ninguno.

## 15. Git

Se preparó el commit único requerido:

```text
feat: add news database models
```

El hash se registra en la respuesta final del loop. No se hizo push.

## 16. Information for Loop 03

Loop 03 puede usar estos modelos como fuente directa para validators e índices físicos MongoDB:

- Índices únicos: `users.firebaseUid` y `news.slug`.
- Índice TTL futuro: `chatSessions.expiresAt` con expiración en la fecha indicada.
- Validadores deben reflejar los enums y reglas cruzadas de los modelos, especialmente publicación,
  tiempos de lectura, imagen/IA, interacción, metadata de chat y valores no negativos.
- Las referencias siguen siendo lógicas por `ObjectId`; MongoDB no debe introducir foreign keys.
- La conexión debe seguir usando `ai_assisted_news`, nunca la base `assistant`.

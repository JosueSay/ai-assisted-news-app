# Loop 03 — MongoDB Collections, Validation and Indexes

## Objetivo

Materializar de forma reproducible en MongoDB el esquema lógico aprobado e implementado durante Loop 02.

Este loop debe implementar:

- definición física de las siete colecciones;
- MongoDB `$jsonSchema` validators;
- índices necesarios;
- TTL de `chatSessions`;
- script idempotente de inicialización;
- comandos Makefile;
- pruebas offline;
- verificación controlada contra MongoDB Atlas;
- documentación y trazabilidad.

Este será el primer loop autorizado para crear estructura física en:

```text
ai_assisted_news
```

Puede crear:

- colecciones;
- validators;
- índices.

NO puede:

- insertar seed data;
- insertar noticias;
- crear usuarios;
- crear sesiones;
- borrar colecciones;
- borrar la database;
- ejecutar reseed;
- implementar repositories;
- implementar endpoints.

---

# Lecturas obligatorias

Antes de modificar código leer:

```text
AGENTS.md

backend/loops/handoffs/00-discovery-result.md
backend/loops/handoffs/01-db-foundation-result.md
backend/loops/handoffs/02-db-models-result.md

docs/design/database/README.md
docs/design/database/01-colecciones.md
docs/design/database/02-criterios-de-contenido.md
docs/design/database/03-criterios-de-personalizacion.md
docs/design/database/04-criterios-de-chat-y-costos.md
docs/design/database/05-tiempo-de-lectura.md
docs/design/database/06-decisiones-descartadas.md
docs/design/database/07-diagrama.md

backend/news/models/
```

Los modelos implementados en Loop 02 y la documentación aprobada deben permanecer sincronizados.

No reinterpretar el esquema.

---

# Estado heredado

Loop 02 dejó implementados:

```text
locations
users
news
userInteractions
chatSessions
aiUsage
auditLogs
```

mediante modelos Python/Pydantic.

También dejó:

```text
99 passed
```

y ningún dato o colección creado en Atlas.

La conectividad Atlas fue comprobada manualmente:

```text
MongoDB connection: OK
Database: ai_assisted_news
```

---

# Principio de implementación

Los modelos Python representan validación en aplicación.

MongoDB debe proporcionar una segunda barrera mediante:

```text
$jsonSchema
```

No intentar reproducir en `$jsonSchema` lógica que MongoDB no pueda expresar limpiamente.

Clasificar las reglas en:

```text
MODEL
DATABASE
BOTH
```

Ejemplos:

```text
enum                     -> BOTH
required field           -> BOTH
numeric minimum          -> BOTH
ObjectId type            -> BOTH
URL HTTP(S)              -> MODEL
reading-time calculation -> MODEL
cross-field logic        -> MODEL cuando $jsonSchema lo complique innecesariamente
```

Documentar las excepciones.

---

# Fase 1 — Estructura de infraestructura

Crear una estructura clara dentro de:

```text
backend/news/database/
```

o una ubicación equivalente coherente con la infraestructura existente.

Debe separar como mínimo:

- definición de colecciones;
- validators;
- índices;
- inicialización.

Ejemplo conceptual:

```text
backend/news/db/
├── __init__.py
├── collections.py
├── validators.py
├── indexes.py
└── initialize.py
```

El nombre exacto puede adaptarse para evitar conflicto con `backend/news/database.py`.

No mover innecesariamente archivos existentes.

---

# Fase 2 — Colecciones

Definir exactamente estas siete:

```text
locations
users
news
userInteractions
chatSessions
aiUsage
auditLogs
```

Mantener los nombres exactamente como están documentados.

No crear una octava colección.

La inicialización debe detectar:

```text
existing collections
missing collections
```

y crear únicamente las faltantes.

No eliminar colecciones existentes.

---

# Fase 3 — Validators MongoDB

Crear `$jsonSchema` validators para las siete colecciones.

Los validators deben reflejar razonablemente:

- BSON types;
- required fields;
- documentos embebidos;
- arrays;
- enums;
- mínimos numéricos;
- estructura de ObjectId;
- fechas.

## locations

Validar:

```text
_id
name
city
region
country
countryCode
level
active
createdAt
```

`level`:

```text
city
region
country
international
```

---

## users

Validar:

```text
firebaseUid
email
displayName
photoUrl
role
simulatedLocationId
onboarding
inferredInterests
createdAt
updatedAt
lastLoginAt
```

`role`:

```text
user
admin
```

`inferredInterests.score`:

```text
minimum: 0
maximum: 1
```

---

## news

Validar estructura para:

```text
slug
title
summary
content
authorId
status
topics
keywords
geographicScope
verification
sources
image
aiAssistance
wordCount
estimatedReadingMinutes
publishedAt
createdAt
updatedAt
```

`status`:

```text
draft
published
```

`verification.status`:

```text
confirmed
developing
insufficient_sources
conflicting_sources
```

`sourceType`:

```text
official
media
primary_source
witness
other
```

`image.type`:

```text
photograph
illustration
ai_generated
ai_modified
none
```

`geographicScope.level`:

```text
city
region
country
international
```

Validar:

```text
wordCount >= 0
estimatedReadingMinutes >= 1
```

cuando esos campos existan según el modelo.

No intentar recalcular tiempo de lectura desde MongoDB.

---

## userInteractions

`type` únicamente:

```text
opened
read
```

Validar:

```text
dwellTimeSeconds >= 0
feedPosition >= 0
```

cuando existan.

---

## chatSessions

Validar:

```text
userId
simulatedLocationId
messages
createdAt
expiresAt
```

Validar enums documentados para:

```text
role
strategy
intent
confidence
```

No implementar lógica de chatbot.

---

## aiUsage

Validar enums de `feature`:

```text
chat
summary
image_generation
classification
```

Validar como no negativos cuando existan:

```text
inputTokens
outputTokens
estimatedCostUsd
```

---

## auditLogs

Validar:

```text
actorId
action
entityType
entityId
details
createdAt
```

`action`:

```text
news.created
news.updated
news.published
image.generated
```

`entityType` únicamente:

```text
news
```

---

# Fase 4 — Validation policy

Las colecciones deben configurarse con una política apropiada de validación.

Preferir:

```text
validationLevel: strict
validationAction: error
```

salvo que exista una razón documentada para otra configuración.

La intención es impedir documentos nuevos incompatibles con el esquema.

---

# Fase 5 — Índices obligatorios

Crear como mínimo:

## users

```text
{ firebaseUid: 1 }
unique: true
```

## news

```text
{ slug: 1 }
unique: true
```

## chatSessions

TTL:

```text
{ expiresAt: 1 }
expireAfterSeconds: 0
```

`expiresAt` contiene la fecha absoluta de expiración.

La vigencia funcional es:

```text
createdAt + 3600 segundos
```

pero el índice TTL debe utilizar `expireAfterSeconds: 0`.

---

# Fase 6 — Índices derivados de Access Patterns

Agregar únicamente índices respaldados por consultas que ya conocemos.

Como mínimo evaluar:

## Feed

```text
news:
{ status: 1, publishedAt: -1 }
```

## Feed geográfico

```text
news:
{ "geographicScope.locationIds": 1, status: 1, publishedAt: -1 }
```

## Feed/consulta por topic

```text
news:
{ topics: 1, status: 1, publishedAt: -1 }
```

## Personalización

```text
userInteractions:
{ userId: 1, createdAt: -1 }
```

y evaluar:

```text
{ userId: 1, newsId: 1, type: 1 }
```

## AI usage

```text
{ feature: 1, createdAt: -1 }
```

y/o:

```text
{ createdAt: -1 }
```

solo si existe un access pattern documentado para gasto total por periodo.

## Audit

```text
{ entityId: 1, createdAt: -1 }
```

No crear índices especulativos.

Para cada índice no-obvio documentar qué Access Pattern resuelve.

---

# Fase 7 — Nombres de índices

Asignar nombres explícitos y estables.

Ejemplos:

```text
uq_users_firebase_uid
uq_news_slug
ttl_chat_sessions_expires_at
idx_news_status_published_at
idx_news_location_status_published_at
idx_news_topics_status_published_at
idx_interactions_user_created_at
idx_ai_usage_feature_created_at
idx_audit_entity_created_at
```

La nomenclatura debe permanecer consistente.

---

# Fase 8 — Inicialización idempotente

Crear un script Python que pueda ejecutar:

```text
initialize database schema
```

Debe:

1. conectarse mediante la infraestructura de Loop 01;
2. obtener colecciones existentes;
3. crear únicamente colecciones faltantes;
4. aplicar validators;
5. crear índices faltantes;
6. verificar índices existentes;
7. no insertar documentos;
8. no borrar documentos;
9. no borrar colecciones;
10. no hacer drop de database.

Debe ser seguro ejecutarlo repetidamente.

La segunda ejecución debe producir un resultado equivalente a:

```text
already configured / unchanged
```

sin errores ni duplicación de índices.

---

# Fase 9 — Cambios de validators

Si una colección ya existe, el inicializador puede utilizar:

```text
collMod
```

para sincronizar el validator.

`collMod` está permitido en este loop porque modifica únicamente estructura/validación.

No modificar datos existentes.

Si un cambio estructural no puede aplicarse de forma segura, detenerse y reportarlo.

---

# Fase 10 — Drift detection

Implementar una verificación no destructiva:

```text
make db-schema-check
```

Debe comparar el estado esperado contra MongoDB cuando haya credenciales disponibles.

Debe comprobar como mínimo:

- siete colecciones;
- validators;
- índices obligatorios;
- TTL.

Resultado conceptual:

```text
Database schema: OK
Collections: 7/7
Validators: OK
Indexes: OK
TTL: OK
```

Si existe diferencia:

```text
Database schema: DRIFT DETECTED
```

y describir únicamente la diferencia estructural sin exponer secretos.

No corregir automáticamente mediante `db-schema-check`.

---

# Fase 11 — Makefile

Mantener:

```text
make setup-keys
make db-check-config
make db-ping
make db-test
```

Agregar:

```text
make db-init
make db-schema-check
```

## db-init

Crea/sincroniza:

- colecciones;
- validators;
- índices.

No inserta datos.

## db-schema-check

Solo inspecciona.

No modifica DB.

Documentar claramente la diferencia.

---

# Fase 12 — Seguridad de `db-init`

Aunque `db-init` no sea destructivo respecto de datos, modifica estructura real.

Antes de ejecutarlo debe mostrar:

```text
Database: ai_assisted_news
Operation:
- create missing collections
- synchronize validators
- create missing indexes

No documents will be inserted or deleted.
```

No mostrar URI.

No pedir confirmación para esta inicialización no destructiva salvo que la implementación detecte una operación incompatible.

Operaciones destructivas continúan prohibidas.

---

# Fase 13 — Tests offline

Los tests deben probar la infraestructura sin Atlas real.

Cubrir como mínimo:

### Collections

- exactamente siete nombres;
- ningún nombre adicional.

### Validators

- validator disponible para cada colección;
- enums sincronizados;
- tipos BSON;
- mínimos;
- campos requeridos principales.

### Indexes

- unique firebaseUid;
- unique slug;
- TTL correcto;
- nombres estables;
- índices de access patterns.

### Initializer

Con mocks/fakes:

- crea colección faltante;
- no recrea colección existente;
- aplica validator;
- crea índice faltante;
- segunda ejecución idempotente;
- nunca inserta documentos;
- nunca ejecuta drop.

### Schema check

- estado correcto;
- colección faltante;
- índice faltante;
- TTL incorrecto;
- validator diferente.

Los tests normales no deben requerir Atlas.

---

# Fase 14 — Verificación real contra Atlas

Después de que todos los tests offline pasen, puede ejecutarse:

```text
make db-init
```

contra la DB configurada:

```text
ai_assisted_news
```

Esta ejecución está autorizada porque:

- crea únicamente estructura;
- no inserta datos;
- no elimina datos.

Después ejecutar:

```text
make db-schema-check
```

Resultado esperado:

```text
Database schema: OK
```

Después volver a ejecutar:

```text
make db-init
make db-schema-check
```

para comprobar idempotencia real.

IMPORTANTE:

El agente no debe leer ni mostrar `keys/mongodb_uri`.

Debe utilizar las interfaces existentes.

Si las reglas del entorno impiden ejecutar comandos que consumen indirectamente el secreto, detener la parte Atlas y solicitar ejecución humana.

Eso no invalida los tests offline.

---

# Fase 15 — Documentación

Actualizar:

```text
backend/news/README.md
docs/design/database/README.md
docs/design/database/07-diagrama.md
```

solo cuando corresponda.

Crear documentación específica de estructura física si resulta útil, por ejemplo:

```text
docs/design/database/08-indices-y-validacion.md
```

Este archivo es recomendado.

Debe documentar:

- validators;
- qué reglas viven en modelo vs DB;
- índices;
- Access Pattern de cada índice;
- TTL;
- inicialización;
- drift detection.

No duplicar código completo de validators en Markdown.

---

# Fase 16 — Diagrama

Revisar:

```text
docs/design/database/07-diagrama.md
```

No cambiar el esquema lógico salvo que sea necesario para reflejar correctamente la implementación.

Agregar indicaciones de índices/TTL solo si mejora el diagrama sin volverlo ilegible.

El diagrama debe continuar sincronizado.

---

# Fase 17 — Verificación de trazabilidad

Antes de cerrar:

```text
[ ] modelos sincronizados
[ ] validators sincronizados
[ ] índices sincronizados
[ ] documentación sincronizada
[ ] diagrama sincronizado
[ ] tests sincronizados
[ ] Makefile sincronizado
[ ] secrets/bootstrap sincronizados
```

Comprobar:

```text
git status
git diff
git diff --cached
```

Verificar:

```text
secret values exposed: NO
secret files tracked: NO
assistant modified: NO
documents inserted: NO
documents deleted: NO
collections dropped: NO
database dropped: NO
```

---

# Fase 18 — Regression

Ejecutar:

```text
make db-test
```

Todos los tests anteriores deben seguir pasando.

No aceptar regresiones respecto de los 99 tests existentes.

---

# Commit

Si toda la Definition of Done se cumple:

```text
feat: add MongoDB schema validation and indexes
```

No hacer push.

---

# Entregable

Crear:

```text
backend/loops/handoffs/03-db-indexes-validation-result.md
```

Debe incluir:

## 1. Resultado

Completed / Partial / Blocked.

## 2. Collections

Siete colecciones configuradas.

## 3. Validators

Resumen por colección.

## 4. Model vs Database Validation

Tabla:

```text
Rule | Model | MongoDB | Reason
```

## 5. Indexes

Tabla:

```text
Collection | Index | Fields | Properties | Access Pattern
```

## 6. TTL

Configuración implementada.

## 7. Initializer

Comportamiento e idempotencia.

## 8. Schema Check

Comportamiento y resultado.

## 9. Offline Tests

Comandos y resultados.

## 10. Atlas Verification

Comandos ejecutados y resultados.

Nunca incluir URI.

## 11. Idempotency

Resultado de segunda ejecución.

## 12. Traceability

Estado de:

```text
models
validators
indexes
documentation
diagram
tests
Makefile
secrets/bootstrap
```

## 13. Security

Confirmar:

```text
secret values exposed: NO
secret files tracked: NO
assistant modified: NO
```

## 14. Data Safety

Confirmar:

```text
documents inserted: NO
documents deleted: NO
collections dropped: NO
database dropped: NO
```

## 15. Files Changed

Listado.

## 16. Decisions

Decisiones técnicas menores.

## 17. Blockers

Solo bloqueos reales.

## 18. Git

Commit y working tree.

## 19. Information for Loop 04

Información necesaria para implementar catálogos y seeders.

---

# Definition of Done

Loop 03 termina cuando:

- existen exactamente siete definiciones de colección;
- existen validators para las siete;
- validators están sincronizados con modelos;
- existen índices únicos de `firebaseUid` y `slug`;
- existe TTL de `chatSessions.expiresAt`;
- índices adicionales corresponden a Access Patterns reales;
- existe inicializador idempotente;
- existe schema check no destructivo;
- existen tests offline;
- todos los tests anteriores continúan pasando;
- Makefile contiene `db-init` y `db-schema-check`;
- documentación está sincronizada;
- diagrama está revisado;
- si el entorno lo permite, Atlas fue inicializado y verificado;
- una segunda inicialización no produce cambios incorrectos;
- ningún documento fue insertado;
- ningún documento fue eliminado;
- ninguna colección fue eliminada;
- ningún secreto fue expuesto;
- `assistant/` permanece intacto;
- existe handoff;
- existe commit.

---

# Stop Conditions

Detener y solicitar decisión humana si:

- un validator requiere cambiar el modelo aprobado;
- se descubre contradicción entre modelos y documentación;
- se necesita un índice sin Access Pattern justificable;
- se necesita una octava colección;
- se requiere modificar documentos existentes;
- se requiere eliminar/recrear una colección;
- `collMod` produciría una incompatibilidad no segura;
- se requiere acceder directamente al contenido de `keys/`;
- se detecta que `db-init` apunta a una DB distinta de `ai_assisted_news`;
- se necesita modificar `assistant/`;
- aparece cualquier operación destructiva no autorizada.

No resolver estas situaciones silenciosamente.

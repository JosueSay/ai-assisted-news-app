# Loop 02 — Database Models

## Objetivo

Implementar en Python el diseño completo y aprobado de las siete colecciones MongoDB de AI Assisted News App, manteniendo sincronizados:

- diseño documental;
- modelos Python;
- enums;
- validaciones de dominio;
- diagrama de base de datos;
- tests;
- bootstrap de secretos;
- documentación.

Este loop representa el esquema lógico de la base de datos.

**No crear todavía colecciones en MongoDB Atlas.  
No crear índices MongoDB.  
No ejecutar seeders.  
No insertar documentos.  
No implementar repositories.  
No implementar endpoints.**

---

## Lecturas obligatorias

Antes de modificar código leer:

```text
AGENTS.md

backend/loops/handoffs/00-discovery-result.md
backend/loops/handoffs/01-db-foundation-result.md

docs/design/database/README.md
docs/design/database/01-colecciones.md
docs/design/database/02-criterios-de-contenido.md
docs/design/database/03-criterios-de-personalizacion.md
docs/design/database/04-criterios-de-chat-y-costos.md
docs/design/database/05-tiempo-de-lectura.md
docs/design/database/06-decisiones-descartadas.md
```

El contenido de `docs/design/database/` es la fuente de verdad funcional.

No recuperar features explícitamente descartadas.

---

# Decisiones ya tomadas

## Colecciones

El diseño contiene exactamente estas siete colecciones:

```text
locations
users
news
userInteractions
chatSessions
aiUsage
auditLogs
```

No agregar colecciones adicionales sin decisión humana.

---

## MongoDB

Usar:

```text
MongoDB Atlas
PyMongo
Python
```

No introducir ODM.

Los modelos Python representan documentos MongoDB pero no deben conectarse por sí mismos a MongoDB.

---

## Base de datos

Usar la infraestructura creada por Loop 01.

Database por defecto:

```text
ai_assisted_news
```

No utilizar:

```text
assistant
```

No modificar:

```text
backend/assistant/
```

---

# Secretos

Actualmente existen o se prevén cinco valores proporcionados por el desarrollador:

```text
MongoDB URI
MongoDB username
MongoDB password
Client ID
Client secret
```

Sin embargo, la MongoDB URI actual ya contiene username y password.

Por tanto, **no duplicar las credenciales MongoDB** en:

```text
keys/mongodb_username
keys/mongodb_password
```

mientras la estrategia vigente utilice una URI completa.

El secreto MongoDB requerido actualmente sigue siendo únicamente:

```text
keys/mongodb_uri
```

Preparar además archivos vacíos para:

```text
keys/client_id
keys/client_secret
```

Estos secretos se reservan para autenticación/integración futura.

Loop 02:

- NO debe leerlos;
- NO debe utilizarlos;
- NO debe integrar Firebase/OAuth;
- NO debe validar sus valores.

No crear archivos separados de username/password de Mongo mientras la URI ya los incluya.

Si en el futuro cambia la estrategia de conexión, deberá modificarse explícitamente el diseño de secretos.

---

# Fase 1 — Bootstrap de secretos

Agregar al Makefile:

```text
make setup-keys
```

Debe garantizar que existan:

```text
keys/mongodb_uri
keys/client_id
keys/client_secret
```

Reglas:

1. crear `keys/` si falta;
2. crear únicamente archivos faltantes;
3. crearlos vacíos;
4. nunca sobrescribir archivos existentes;
5. nunca leer ni imprimir contenido;
6. nunca agregar valores automáticamente;
7. indicar cuáles fueron creados;
8. indicar cuáles ya existían;
9. recordar al desarrollador que debe completarlos;
10. ser idempotente.

Ejemplo conceptual:

```text
$ make setup-keys

keys/mongodb_uri    EXISTS
keys/client_id      CREATED
keys/client_secret  CREATED

Complete missing secret values manually.
Then run:
make db-check-config
make db-ping
```

Actualizar:

```text
keys/README.md
```

para documentar los tres archivos.

No cambiar la conexión Mongo actual para utilizar `client_id` o `client_secret`.

---

# Fase 2 — Organización de modelos

Crear una estructura clara bajo:

```text
backend/news/models/
```

Preferir separación por responsabilidad, por ejemplo:

```text
backend/news/models/
├── __init__.py
├── common.py
├── location.py
├── user.py
├── news.py
├── user_interaction.py
├── chat_session.py
├── ai_usage.py
└── audit_log.py
```

Puede ajustarse ligeramente si existe una razón técnica clara.

Evitar un único archivo gigante.

No introducir arquitectura innecesaria.

---

# Fase 3 — Estrategia de modelado

Utilizar modelos Python tipados y validables.

Puede utilizarse Pydantic si ya está disponible de forma coherente en el backend.

No introducir un ODM.

Los modelos deben:

- representar los documentos definidos en el diseño;
- soportar `ObjectId` de MongoDB;
- representar documentos embebidos;
- restringir enums;
- validar rangos definidos;
- utilizar fechas tipadas;
- distinguir campos requeridos y opcionales;
- permitir serialización apropiada para MongoDB.

No inventar campos.

No agregar abstracciones "por si acaso".

---

# Fase 4 — Modelo `Location`

Representar:

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

Debe representar ubicaciones reales del catálogo.

No agregar:

- GPS;
- latitude;
- longitude;
- userId;
- isSimulated.

La simulación pertenece al comportamiento de selección del usuario, no a la ubicación geográfica en sí.

---

# Fase 5 — Modelo `User`

Representar:

```text
_id
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

`onboarding`:

```text
completed
completedAt
selectedTopics
```

`inferredInterests[]`:

```text
topic
score
updatedAt
```

Validar:

```text
0 <= score <= 1
```

`firebaseUid` debe existir en el modelo.

No implementar Firebase Authentication.

---

# Fase 6 — Modelo `News`

Representar exactamente el diseño vigente.

Campos principales:

```text
_id
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

## Status

Únicamente:

```text
draft
published
```

No reintroducir:

```text
under_review
corrected
withdrawn
```

---

## Geographic scope

Representar:

```text
level
locationIds
```

`level`:

```text
city
region
country
international
```

---

## Verification

Representar:

```text
status
reviewedBy
reviewedAt
notes
```

Estados:

```text
confirmed
developing
insufficient_sources
conflicting_sources
```

No crear un `confidenceLevel` numérico para noticias.

---

## Sources

Cada source representa:

```text
name
url
sourceType
publishedAt
accessedAt
supports
```

`sourceType`:

```text
official
media
primary_source
witness
other
```

Validar que `url` tenga una estructura válida.

**No realizar requests HTTP desde el modelo.**

Una URL sintácticamente válida no implica que la noticia esté confirmada.

---

## Image

Representar:

```text
url
alt
type
credit
rights
aiDisclosure
```

`type`:

```text
photograph
illustration
ai_generated
ai_modified
none
```

Mantener coherencia con el diseño de Responsible AI.

No generar imágenes en este loop.

---

## AI assistance

Representar:

```text
summaryGenerated
topicsGenerated
imageGenerated
humanReviewed
```

---

## Tiempo de lectura

Representar:

```text
wordCount
estimatedReadingMinutes
```

Regla documentada:

```text
estimatedReadingMinutes = ceil(wordCount / 200)
```

Implementar una función pura reutilizable para calcular estos valores a partir de `content`.

Debe poder probarse sin MongoDB.

No usar IA para este cálculo.

---

# Fase 7 — Modelo `UserInteraction`

Representar:

```text
_id
userId
newsId
type
dwellTimeSeconds
context
createdAt
```

`type` únicamente:

```text
opened
read
```

No reintroducir:

```text
saved
shared
hidden
impression
location_change
```

`context`:

```text
simulatedLocationId
feedPosition
```

`dwellTimeSeconds` debe ser:

```text
>= 0
```

cuando exista.

`feedPosition` debe ser válido cuando exista.

No almacenar proporción de lectura porque puede derivarse.

---

# Fase 8 — Modelo `ChatSession`

Representar:

```text
_id
userId
simulatedLocationId
messages
createdAt
expiresAt
```

Cada mensaje:

```text
role
content
responseMetadata
createdAt
```

`role`:

```text
user
assistant
```

Para respuestas assistant, `responseMetadata` puede representar:

```text
strategy
intent
citedNewsIds
confidence
uncertainty
aiUsed
```

`strategy`:

```text
database_query
template
llm
```

`intent`:

```text
recent_news
regional_news
topic_news
news_detail
summarize
explain
unsupported
```

`confidence`:

```text
high
medium
low
```

Las sesiones tendrán una vigencia conceptual de:

```text
3600 segundos
```

El modelo debe permitir `expiresAt`.

La creación automática del TTL index corresponde a un loop posterior.

No implementar chatbot.

---

# Fase 9 — Modelo `AiUsage`

Representar:

```text
_id
feature
provider
model
userId
newsId
chatSessionId
inputTokens
outputTokens
estimatedCostUsd
createdAt
```

`feature`:

```text
chat
summary
image_generation
classification
```

Validar valores numéricos no negativos cuando corresponda.

Esta colección representa gasto de IA de la aplicación.

NO utilizarla para registrar consumo de OpenCode ni de los agentes de ingeniería.

---

# Fase 10 — Modelo `AuditLog`

Representar:

```text
_id
actorId
action
entityType
entityId
details
createdAt
```

`action` únicamente:

```text
news.created
news.updated
news.published
image.generated
```

`entityType`:

```text
news
```

No ampliar auditoría a otras entidades.

---

# Fase 11 — Enums compartidos

Evitar strings duplicados dispersos cuando un enum tenga significado compartido.

Crear enums únicamente donde aporten consistencia real.

Los valores persistidos deben ser strings legibles y estables.

No crear una jerarquía compleja de enums.

---

# Fase 12 — Diagrama de DB

Crear:

```text
docs/design/database/07-diagrama.md
```

Debe utilizar Mermaid cuando sea viable.

Debe mostrar las siete colecciones:

```text
locations
users
news
userInteractions
chatSessions
aiUsage
auditLogs
```

Representar las relaciones lógicas:

```text
users.simulatedLocationId -> locations._id

news.authorId -> users._id

news.geographicScope.locationIds -> locations._id

userInteractions.userId -> users._id
userInteractions.newsId -> news._id
userInteractions.context.simulatedLocationId -> locations._id

chatSessions.userId -> users._id
chatSessions.simulatedLocationId -> locations._id
chatSessions.messages[].citedNewsIds -> news._id

aiUsage.userId -> users._id
aiUsage.newsId -> news._id
aiUsage.chatSessionId -> chatSessions._id

auditLogs.actorId -> users._id
auditLogs.entityId -> news._id
```

Aclarar explícitamente que estas son referencias lógicas MongoDB y no foreign keys impuestas por el motor.

El documento debe incluir además una explicación breve de:

- documentos embebidos principales;
- catálogos;
- TTL futuro de `chatSessions`;
- qué datos se generan por uso y cuáles son catálogo.

El diagrama debe representar exactamente los modelos implementados al finalizar el loop.

---

# Fase 13 — Tests

Crear tests unitarios para los siete modelos.

Como mínimo cubrir:

## Location

- instancia válida;
- level inválido.

## User

- usuario válido;
- role inválido;
- inferred interest válido;
- score fuera de 0-1 rechazado;
- onboarding válido.

## News

- draft válido;
- published válido;
- status inválido;
- verification status inválido;
- source type inválido;
- URL inválida;
- image type inválido;
- geographic level inválido;
- cálculo de word count;
- cálculo de estimated reading minutes.

## UserInteraction

- opened;
- read;
- tipo eliminado rechazado;
- dwell time negativo rechazado.

## ChatSession

- sesión válida;
- roles;
- strategies;
- intents;
- confidence;
- metadata assistant.

## AiUsage

- features válidos;
- costo negativo rechazado;
- tokens negativos rechazados.

## AuditLog

- actions válidas;
- action fuera del catálogo rechazada;
- entityType distinto de news rechazado.

Los tests no deben:

- requerir Atlas;
- acceder a `keys/`;
- crear colecciones;
- insertar documentos.

---

# Fase 14 — Makefile

Mantener los targets existentes:

```text
make db-check-config
make db-ping
make db-test
```

Agregar:

```text
make setup-keys
```

Si es útil, `db-test` puede incluir los nuevos tests de modelos.

No romper los comandos existentes.

Verificar:

```text
make setup-keys
make setup-keys
```

La segunda ejecución debe ser segura e idempotente.

El agente no debe leer los archivos creados.

---

# Fase 15 — Documentación

Actualizar cuando corresponda:

```text
backend/news/README.md
keys/README.md
docs/design/database/README.md
```

Documentar:

- ubicación de modelos;
- siete colecciones;
- cómo ejecutar tests;
- `make setup-keys`;
- separación entre modelo lógico y creación física de colecciones;
- que Loop 02 no crea datos en Atlas.

No duplicar innecesariamente toda la documentación de diseño.

---

# Fase 16 — Verificación Atlas

La conexión Atlas ya fue comprobada manualmente mediante:

```text
make db-ping
```

Resultado reportado:

```text
MongoDB connection: OK
Database: ai_assisted_news
```

No es necesario volver a ejecutar `db-ping` si hacerlo requiere que el agente acceda al secreto.

Los tests de modelos deben funcionar completamente offline.

No crear nada en Atlas durante este loop.

---

# Fase 17 — Verificación de trazabilidad

Antes de cerrar:

```text
[ ] modelos sincronizados
[ ] documentación sincronizada
[ ] diagrama sincronizado
[ ] tests sincronizados
[ ] Makefile sincronizado
[ ] secrets/bootstrap sincronizados
```

Comprobar también:

```text
git status
git diff
git diff --cached
```

Verificar:

- ningún secreto tracked;
- ningún secreto mostrado;
- `backend/assistant/` sin modificaciones;
- ninguna colección creada;
- ningún documento insertado;
- ninguna operación destructiva;
- modelos coherentes con `docs/design/database/`.

---

# Commit

Si toda la Definition of Done se cumple, crear:

```text
feat: add news database models
```

No hacer push.

---

# Entregable

Crear:

```text
backend/loops/handoffs/02-db-models-result.md
```

Debe incluir:

## 1. Resultado

Completed / Partial / Blocked.

## 2. Models Implemented

Listado de los siete modelos y documentos embebidos.

## 3. Model Structure

Árbol relevante.

## 4. Validation Rules

Validaciones implementadas.

## 5. Reading Time

Implementación y tests.

## 6. Database Diagram

Ruta y resumen del diagrama.

## 7. Secrets Bootstrap

Resultado de `setup-keys`.

Confirmar que no se leyeron secretos.

## 8. Tests

Comandos y resultados exactos.

## 9. Traceability Verification

Estado de:

```text
models
documentation
diagram
tests
Makefile
secrets/bootstrap
```

## 10. Atlas

Confirmar:

```text
collections created: NO
documents inserted: NO
destructive operations: NO
```

## 11. Security

Confirmar:

```text
secret values exposed: NO
secret files tracked: NO
assistant modified: NO
```

## 12. Files Changed

Listado.

## 13. Decisions

Decisiones técnicas menores.

## 14. Blockers

Solo bloqueos reales.

## 15. Git

Commit y working tree final.

## 16. Information for Loop 03

Información necesaria para implementar validaciones e índices físicos MongoDB.

---

# Definition of Done

Loop 02 termina cuando:

- existen modelos Python para las siete colecciones;
- existen modelos para documentos embebidos necesarios;
- enums están restringidos;
- validaciones de dominio están implementadas;
- ObjectId puede representarse correctamente;
- tiempo de lectura se calcula sin IA;
- existen tests unitarios para los siete modelos;
- todos los tests relevantes pasan;
- existe `07-diagrama.md`;
- diagrama y modelos están sincronizados;
- existe `make setup-keys`;
- bootstrap es idempotente;
- `keys/README.md` está actualizado;
- no se duplicaron username/password de MongoDB;
- `client_id` y `client_secret` no son consumidos todavía;
- no se creó ninguna colección;
- no se insertó ningún documento;
- no se modificó `assistant/`;
- no se expuso ningún secreto;
- existe handoff;
- existe commit verificable.

---

# Stop Conditions

Detener y solicitar decisión humana si:

- los documentos de diseño se contradicen de forma que cambie el esquema;
- un campo necesario no está definido;
- se requiere agregar una octava colección;
- se considera necesario introducir un ODM;
- es necesario modificar `assistant/`;
- una prueba requiere leer secretos;
- se requiere crear datos reales en Atlas;
- aparece una operación destructiva;
- sería necesario cambiar una decisión funcional del diseño.

No resolver silenciosamente estas situaciones.

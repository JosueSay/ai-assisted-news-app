# Loop 07 — Verificación Final y Reproducibilidad de Base de Datos

## Objetivo

Cerrar formalmente el trabajo de diseño e infraestructura de base de datos de AI Assisted News App.

Este loop NO agrega funcionalidades.

Debe demostrar que un desarrollador nuevo puede partir del repositorio y reproducir de forma segura:

1. configuración local;
2. schema MongoDB;
3. catálogos;
4. noticias demo;
5. verificaciones;
6. conexión Atlas;
7. automatización existente.

También debe realizar una auditoría final de:

- modelos;
- schema;
- validators;
- índices;
- seeders;
- dataset demo;
- automatización;
- documentación;
- seguridad;
- tests;
- trazabilidad.

El resultado debe dejar la rama lista para PR.

---

# Skills

## Principal

Usar:

`.skills/code-reviewer/SKILL.md`

Este loop es principalmente una revisión integral.

## Seguridad

Usar:

`.skills/security-compliance/SKILL.md`

para revisar secretos, operaciones destructivas y superficie de configuración.

## Testing

Usar:

`.skills/test-driven-development/SKILL.md`

únicamente si durante la auditoría aparece un defecto que requiera modificar comportamiento.

No crear tests artificialmente si no existe un comportamiento faltante.

## Debugging

Si alguna verificación falla inesperadamente:

`.skills/systematic-debugging/SKILL.md`

antes de modificar código.

## Planning

`planning-with-files` solo si el agente necesita memoria adicional para la auditoría.

---

# Lecturas obligatorias

Leer:

- `AGENTS.md`;
- handoffs 00–06;
- `docs/design/database/`;
- `backend/news/`;
- `backend/news/models/`;
- `backend/news/schema/`;
- tests;
- `Makefile`;
- `docker-compose.yml`;
- `.gitignore`;
- `keys/README.md`;
- `.env.example` y configuración no secreta relacionada.

No repetir implementación de loops anteriores.

---

# Estado esperado heredado

## Schema

```text
Collections: 7/7
Validators: OK
Indexes: OK
TTL: OK
```

## Catálogos

```text
Locations: 16/16
Duplicates: 0
```

## Demo news

```text
News: 32/32
Countries: 16/16
Drafts: 4
Published: 28
Duplicates: 0
External: 0
```

## Tests

Baseline heredado:

```text
204 passed
```

## Automatización

Deben existir:

```text
setup-keys

db-check-config
db-ping

db-init
db-schema-check

db-seed-catalogs
db-seed-check

db-seed-news
db-news-check

db-bootstrap
db-verify

db-reseed-dry-run
db-reseed
```

---

# 1. Auditoría del diseño

Comparar explícitamente:

```text
docs/design/database/
        ↕
backend/news/models/
        ↕
backend/news/schema/
        ↕
seeders/generator
        ↕
tests
        ↕
Makefile
```

Detectar:

- campos documentados pero no implementados;
- campos implementados pero no documentados;
- enums divergentes;
- colecciones adicionales;
- índices divergentes;
- validators divergentes;
- referencias incorrectas;
- comandos obsoletos.

No corregir silenciosamente cambios funcionales.

---

# 2. Colecciones

Confirmar que el diseño sigue conteniendo exactamente:

```text
locations
users
news
userInteractions
chatSessions
aiUsage
auditLogs
```

No debe existir una colección MongoDB `topics`.

No debe existir ninguna colección añadida "por si acaso".

---

# 3. Modelos

Revisar los siete modelos y documentos embebidos.

Confirmar:

- ObjectId;
- enums;
- campos required/optional;
- rangos;
- fechas;
- serialización Mongo;
- tiempo de lectura;
- coherencia de imágenes IA;
- chat metadata;
- aiUsage;
- auditLogs.

No rediseñar modelos en este loop.

Si existe inconsistencia funcional importante, detener y reportar.

---

# 4. Schema físico

Revisar:

- siete validators;
- `validationLevel: strict`;
- `validationAction: error`;
- índices;
- unique;
- TTL.

Confirmar específicamente:

```text
users.firebaseUid UNIQUE
news.slug UNIQUE

chatSessions.expiresAt
expireAfterSeconds: 0
```

Revisar también los índices de Access Patterns existentes.

---

# 5. Decisiones pendientes conocidas

Auditar y documentar, pero NO resolver automáticamente:

## locations.countryCode unique

Actualmente no existe índice unique.

Determinar si continúa siendo una limitación aceptada/documentada.

No agregarlo automáticamente.

## Topics cerrados

El catálogo existe, pero los modelos mantienen strings.

No convertirlos automáticamente en enum.

## Demo authorId

Las noticias demo utilizan ObjectId sintético sin user persistido.

No crear user/admin automáticamente.

## GeographicScope international

Dataset demo actual utiliza country.

No ampliar dataset automáticamente.

Estas decisiones deben aparecer claramente en el cierre final.

---

# 6. Reproducibilidad desde cero — local

La prueba principal debe demostrar que una DB local nueva puede reconstruirse únicamente con comandos documentados.

NO destruir la DB local existente para demostrarlo si existe una forma más segura.

Preferir:

- database temporal dedicada;
- Mongo local temporal;
- nombre de DB aislado para verification.

Ejemplo conceptual:

```text
ai_assisted_news_verification
```

No utilizar Atlas para esta reconstrucción destructiva.

El flujo debe comprobar conceptualmente:

```text
DB inexistente
→ db-bootstrap
→ schema
→ 16 locations
→ 32 news
→ db-verify OK
```

La prueba debe aislarse de la DB local normal.

Después puede eliminarse únicamente la DB temporal creada específicamente para esta verificación si:

- está inequívocamente identificada como temporal;
- el loop autoriza explícitamente esa limpieza;
- nunca es Atlas.

Si existe duda, dejarla y reportarla en vez de borrar.

---

# 7. Reproducibilidad

Ejecutar dos veces el bootstrap contra la DB temporal.

Primera:

```text
schema created
locations inserted: 16
news inserted: 32
```

Segunda:

```text
locations inserted: 0
locations unchanged: 16
news inserted: 0
news unchanged: 32
```

Después:

```text
db-verify → OK
```

Esto demuestra reproducibilidad e idempotencia.

---

# 8. Setup de nuevo desarrollador

Validar documentalmente el flujo:

```bash
git clone ...
make setup-keys

# completar secretos cuando corresponda

make db-check-config
make db-bootstrap
make db-verify
```

Para modo local, un desarrollador debe poder trabajar sin Atlas.

Para Atlas, debe quedar claro:

- dónde colocar `mongodb_uri`;
- cómo seleccionar modo Atlas;
- qué comandos son seguros;
- cuál es destructivo.

No ejecutar secretos ni exponerlos.

---

# 9. Makefile audit

Revisar todos los targets `db-*`.

Clasificarlos:

## Safe / non-destructive

Por ejemplo:

```text
db-check-config
db-ping
db-init
db-schema-check
db-seed-catalogs
db-seed-check
db-seed-news
db-news-check
db-bootstrap
db-verify
db-reseed-dry-run
```

## Destructive

```text
db-reseed
```

Confirmar que no existan comandos destructivos ocultos o equivalentes como:

```text
db-reset
db-drop
db-clean
```

salvo infraestructura previa ajena claramente documentada.

---

# 10. Reseed audit

NO ejecutar reseed Atlas.

Revisar:

- ownership;
- `_id $in`;
- confirmaciones;
- diferenciación local/Atlas;
- preflight;
- failure handling;
- ausencia de drop;
- preservación de externos.

Ejecutar únicamente dry-run Atlas si es necesario.

El desarrollador ya verificó manualmente:

```text
Mode: atlas

locations to delete: 16
demo news to delete: 32

External:
locations=0
news=0

No changes performed.
```

No es necesario repetirlo sin motivo.

---

# 11. Atlas final verification

Solo operaciones no destructivas.

Ejecutar:

```bash
make db-verify NEWS_DB_MODE=atlas COMPOSE_PROFILES=
```

Resultado esperado:

```text
Database verification: OK
Schema: OK
Catalogs: OK
Demo news: OK
```

No ejecutar:

```text
db-reseed
```

contra Atlas.

---

# 12. Tests finales

Ejecutar:

```bash
make db-test
```

Baseline mínimo:

```text
204 passed
```

Si aparecen tests adicionales legítimos durante este loop, actualizar baseline.

Cero regresiones.

---

# 13. Security audit

Aplicar `security-compliance`.

Revisar:

- `.gitignore`;
- `keys/`;
- `.env`;
- `.env.example`;
- Docker mounts;
- Makefile;
- scripts DB;
- logs;
- handoffs;
- documentación.

Confirmar:

```text
secret values tracked: NO
secret values exposed: NO
keys read directly by agent: NO
```

Puede utilizarse `secret_scan.py` únicamente sobre rutas permitidas por `AGENTS.md`.

Nunca escanear `keys/`.

Comparar hallazgos contra baseline existente cuando corresponda.

---

# 14. Operaciones destructivas

Buscar en el código DB:

```text
drop_database
drop_collection
collection.drop
delete_many
delete_one
```

Clasificar cada operación encontrada.

Cualquier delete debe corresponder al reseed controlado.

No debe existir:

```text
delete_many({})
```

Confirmar que ningún flujo normal de bootstrap/seed/check elimina datos.

---

# 15. Code review integral

Aplicar `code-reviewer` sobre el conjunto relevante del trabajo DB, no únicamente el último commit.

Revisar especialmente:

- correctness;
- data safety;
- idempotencia;
- determinismo;
- MongoDB access patterns;
- validators;
- indexes;
- seed ownership;
- error handling;
- test quality;
- documentación;
- mantenibilidad.

Clasificar hallazgos:

```text
BLOCKER
MAJOR
MINOR
FOLLOW-UP
```

BLOCKER o MAJOR relacionados con correctness/data-loss deben resolverse antes del cierre.

MINOR/FOLLOW-UP pueden documentarse si no afectan el alcance.

---

# 16. Documentación final

Revisar todos los documentos:

```text
docs/design/database/
```

Crear:

```text
docs/design/database/12-verificacion-final.md
```

Debe resumir:

- arquitectura final;
- siete colecciones;
- catálogos;
- dataset demo;
- validators;
- índices;
- TTL;
- automatización;
- bootstrap;
- verify;
- reseed;
- seguridad;
- reproducibilidad;
- tests;
- comandos principales;
- decisiones pendientes conocidas.

No duplicar todos los documentos anteriores.

Debe servir como punto de entrada técnico final.

---

# 17. README

Revisar:

```text
backend/news/README.md
docs/design/database/README.md
```

Un desarrollador nuevo debe poder encontrar:

- cómo configurar;
- cómo levantar local;
- cómo bootstrap;
- cómo verificar;
- cómo usar Atlas;
- qué comando es destructivo;
- dónde está el diseño detallado.

---

# 18. Diagrama

Revisar:

```text
docs/design/database/07-diagrama.md
```

Confirmar que representa el estado final.

No agregar entidades operativas como seeders o scripts al ER conceptual.

---

# 19. Handoffs

Revisar que existan handoffs:

```text
00
01
02
03
04
05
06
```

No modificar handoffs históricos salvo error factual crítico.

El Loop 07 debe crear su propio handoff.

---

# 20. Git audit

Antes del cierre:

```bash
git status
git diff
git diff --check
git log --oneline
```

Confirmar:

- working tree esperado;
- secrets no tracked;
- cambios de este loop identificables;
- `backend/assistant/` no modificado;
- no existen archivos temporales de skills.

---

# 21. Correcciones permitidas

Este loop puede corregir:

- documentación incorrecta;
- tests faltantes para un defecto descubierto;
- bugs claros de automatización;
- errores de seguridad;
- inconsistencias menores entre implementación/documentación.

No puede introducir:

- features nuevas;
- colecciones nuevas;
- cambios funcionales de producto;
- Firebase;
- endpoints;
- chat;
- feed;
- nueva arquitectura.

Si una corrección cambia diseño aprobado, detener y solicitar decisión humana.

---

# 22. Revisión final de trazabilidad

Confirmar:

```text
[ ] collections
[ ] models
[ ] embedded models
[ ] validators
[ ] indexes
[ ] TTL
[ ] access patterns
[ ] locations
[ ] topics
[ ] demo news
[ ] reading time
[ ] seeders
[ ] checks
[ ] bootstrap
[ ] verify
[ ] reseed
[ ] tests
[ ] documentation
[ ] diagram
[ ] Makefile
[ ] Docker
[ ] secrets/bootstrap
[ ] handoffs
```

---

# 23. Estado final esperado

Local:

```text
schema: OK
locations: 16
news: 32
verify: OK
```

Atlas:

```text
schema: OK
locations: 16
news: 32
verify: OK
```

Tests:

```text
>= 204 passed
0 failed
```

Git:

```text
working tree clean after commit
```

---

# 24. Seguridad final

Confirmar:

```text
secret values exposed: NO
secret files tracked: NO
keys read directly: NO

assistant modified: NO

Atlas destructive operations: NO
external documents deleted: NO
drop database: NO
drop collections: NO
```

---

# Commit

Si no existen BLOCKER/MAJOR pendientes:

```text
docs: finalize database verification and reproducibility
```

Si fue necesario corregir código significativo, utilizar un Conventional Commit apropiado y documentarlo en el handoff.

No hacer push.

---

# Handoff

Crear:

```text
backend/loops/handoffs/07-db-final-verification-result.md
```

Debe incluir:

1. Resultado.
2. Skills utilizadas.
3. Arquitectura auditada.
4. Colecciones.
5. Modelos.
6. Validators.
7. Índices y TTL.
8. Catálogos.
9. Demo news.
10. Reproducibilidad local desde cero.
11. Segunda ejecución/idempotencia.
12. Setup nuevo desarrollador.
13. Makefile audit.
14. Reseed audit.
15. Atlas verification.
16. Tests finales.
17. Security audit.
18. Destructive operations audit.
19. Code review.
20. Documentación.
21. Diagrama.
22. Trazabilidad.
23. Decisiones pendientes.
24. Archivos modificados.
25. Git.
26. Blockers/follow-ups.
27. Estado final del proyecto DB.

---

# Definition of Done

Loop 07 termina cuando:

- arquitectura DB completa fue auditada;
- documentación e implementación coinciden;
- reproducción desde DB local limpia fue demostrada;
- segunda ejecución fue idempotente;
- Atlas fue verificado no destructivamente;
- tests completos pasan;
- Makefile fue auditado;
- reseed fue auditado;
- security-compliance fue aplicado;
- code-reviewer fue aplicado;
- no existen BLOCKER/MAJOR pendientes;
- documentación final existe;
- diagrama está actualizado;
- trazabilidad completa;
- secretos protegidos;
- Atlas no sufrió operaciones destructivas;
- existe handoff;
- existe commit;
- working tree queda limpio.

---

# Stop Conditions

Detener y solicitar decisión humana si:

- aparece BLOCKER/MAJOR que requiere cambiar diseño;
- documentación y código revelan una contradicción funcional;
- reproducibilidad desde cero falla por una decisión arquitectónica;
- se necesita modificar schema/modelos funcionalmente;
- se necesita eliminar datos Atlas;
- se necesita ejecutar reseed Atlas;
- se necesita acceder a `keys/`;
- se necesita modificar `backend/assistant/`;
- una corrección excede el alcance de infraestructura DB.

No resolver silenciosamente.

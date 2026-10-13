# Loop 06 — Automatización y Reseed Seguro

## Objetivo

Completar la automatización operativa de la base de datos de AI Assisted News App.

Al finalizar debe existir un flujo reproducible para:

1. preparar secretos;
2. inicializar schema;
3. sembrar catálogos;
4. sembrar noticias demo;
5. verificar schema;
6. verificar catálogos;
7. verificar noticias;
8. reconstruir de forma controlada los datos administrados por seeders.

Este loop introduce por primera vez una operación destructiva:

`reseed`

Debe estar diseñada para minimizar el riesgo de borrar datos ajenos.

NO implementar:

- drop database;
- drop collections;
- reset completo de MongoDB;
- eliminación indiscriminada;
- endpoints;
- Firebase;
- frontend;
- chatbot;
- feed;
- lógica de producción.

---

# Skills

## Principal

Usar:

`.skills/test-driven-development/SKILL.md`

Aplicar red → green → refactor.

## Seguridad

Este loop introduce operaciones destructivas, por lo que debe utilizarse:

`.skills/security-compliance/SKILL.md`

para revisar controles y failure modes.

No ejecutar `secret_scan.py` sobre `keys/`.

## Debugging

Si aparece un fallo inesperado:

`.skills/systematic-debugging/SKILL.md`

## Antes del commit

Aplicar:

`.skills/code-reviewer/SKILL.md`

sobre el diff completo.

`planning-with-files` únicamente si la complejidad real lo justifica.

---

# Lecturas obligatorias

Leer:

- `AGENTS.md`;
- handoffs 00–05;
- `docs/design/database/`;
- `backend/news/`;
- `backend/news/schema/`;
- catálogos;
- generator;
- seeders;
- checks;
- tests;
- `Makefile`;
- `docker-compose.yml`.

No repetir Loops anteriores.

---

# Estado heredado

Tenemos verificado en Atlas:

```text
Collections: 7/7
Validators: OK
Indexes: OK
TTL: OK

Locations: 16/16
Duplicates: 0

News: 32/32
Countries: 16/16
Drafts: 4
Published: 28
Duplicates: 0
External: 0
```

La segunda ejecución de ambos seeders produce:

```text
locations:
inserted: 0
unchanged: 16

news:
inserted: 0
unchanged: 32
```

Loop 06 no debe modificar esos contratos salvo necesidad explícita.

---

# 1. Objetivo del reseed

`reseed` significa:

> eliminar únicamente el dataset administrado por nuestros seeders y reconstruirlo desde las fuentes versionadas del repositorio.

Actualmente incluye:

- 16 `locations` controladas;
- 32 `news` demo controladas.

NO significa:

- vaciar toda la database;
- borrar users;
- borrar interacciones;
- borrar chats;
- borrar aiUsage;
- borrar auditLogs;
- borrar locations externas;
- borrar noticias externas.

---

# 2. Ownership del dataset

Antes de eliminar cualquier documento, el sistema debe poder demostrar que pertenece al dataset controlado.

## Locations

Identificar únicamente las 16 locations del catálogo mediante las identidades deterministas ya definidas.

Preferir una combinación segura basada en:

- `countryCode` esperado;
- `_id` determinista esperado;

cuando ambos estén disponibles.

No borrar una location únicamente porque `level == country`.

## News

Identificar únicamente las 32 noticias demo mediante:

- slugs esperados;
- `_id` deterministas esperados;

cuando ambos estén disponibles.

No borrar noticias por:

- status;
- topic;
- fecha;
- prefijo demasiado genérico.

La selección debe derivarse del dataset versionado.

---

# 3. Guard contra drift

Antes de reseed debe ejecutarse un preflight.

Debe comprobar:

- schema OK;
- catálogo esperado identificable;
- noticias demo identificables;
- ausencia de conflictos peligrosos;
- DB objetivo conocida;
- modo local/atlas conocido.

Si un documento con identidad controlada presenta una combinación inesperada que pueda indicar que fue reemplazado/modificado manualmente, NO eliminarlo silenciosamente.

Detener y reportar drift.

---

# 4. Dry run obligatorio

Implementar:

`make db-reseed-dry-run`

Debe ser completamente no destructivo.

Debe mostrar como mínimo:

```text
Database: ai_assisted_news
Mode: local | atlas

Controlled data:
- locations to delete: 16
- demo news to delete: 32

Preserved:
- users
- userInteractions
- chatSessions
- aiUsage
- auditLogs
- external locations
- external news

No changes performed.
```

Los conteos deben provenir de la inspección real, no estar impresos sin comprobar.

No mostrar secretos.

---

# 5. Confirmación humana

Implementar:

`make db-reseed`

Debe requerir confirmación explícita.

NO aceptar automáticamente:

- stdin vacío;
- Enter;
- `y`;
- `yes`.

Requerir una frase suficientemente específica.

Por ejemplo:

`RESEED ai_assisted_news`

Para Atlas, preferir una confirmación aún más explícita:

`RESEED ATLAS ai_assisted_news`

La implementación puede mejorar estas frases si mantiene el mismo nivel de seguridad.

Sin coincidencia exacta:

- abortar;
- exit code no cero;
- cero modificaciones.

---

# 6. No bypass accidental

No proporcionar un flag trivial como:

`--force`

que permita saltarse la confirmación humana en uso normal.

Los tests deben probar la lógica destructiva mediante mocks/fakes sin necesitar confirmación interactiva real.

Si se necesita una interfaz programática interna para tests, debe quedar claramente separada del CLI/Makefile humano.

---

# 7. Orden del reseed

Una vez autorizado:

1. validar target;
2. validar schema;
3. validar ownership;
4. eliminar únicamente 32 noticias demo controladas;
5. eliminar únicamente 16 locations controladas;
6. ejecutar seed de locations;
7. ejecutar seed de news;
8. ejecutar catalog check;
9. ejecutar news check;
10. ejecutar schema check.

Si falla una verificación previa:

- no borrar nada.

---

# 8. Referencias entre news y locations

Eliminar primero:

`news`

y después:

`locations`.

Reconstruir primero:

`locations`

y después:

`news`.

Así se mantiene el orden lógico de dependencias.

MongoDB no impone FK, pero el flujo debe respetar la relación conceptual.

---

# 9. Datos ajenos

Crear tests explícitos donde existan:

- location externa;
- news externa;
- user;
- userInteraction;
- chatSession;
- aiUsage;
- auditLog.

Después del reseed deben permanecer intactos.

El reseed debe modificar únicamente datos controlados.

---

# 10. Reseed y authorId

Las 32 noticias demo siguen utilizando el placeholder `authorId` aprobado en Loop 05.

Loop 06 NO resuelve autoría real.

No insertar users para satisfacer esa referencia.

---

# 11. Comando bootstrap completo

Agregar un comando no destructivo:

`make db-bootstrap`

Debe ejecutar conceptualmente:

```text
db-init
db-seed-catalogs
db-seed-news
db-schema-check
db-seed-check
db-news-check
```

Debe ser idempotente.

Debe servir para:

> clonar repo → configurar keys/env → levantar DB → obtener estructura + dataset demo.

No debe requerir confirmación porque no elimina datos.

---

# 12. Setup de desarrollador

Revisar:

`make setup-keys`

y documentación.

El flujo recomendado para alguien nuevo debe quedar aproximadamente:

```bash
make setup-keys

# humano completa archivos requeridos

make db-check-config
make db-bootstrap
```

En local debe poder funcionar sin Atlas.

Documentar claramente local vs Atlas.

---

# 13. Comando de verificación integral

Agregar:

`make db-verify`

Debe ser no destructivo.

Debe ejecutar:

- tests relevantes o checks operativos apropiados;
- schema check;
- catalog check;
- news check.

No debe reseedear.

Resultado conceptual:

```text
Database verification: OK
Schema: OK
Catalogs: OK
Demo news: OK
```

Evitar duplicar innecesariamente una suite completa de tests dentro de cada operación si eso vuelve el comando demasiado lento; documentar qué verifica exactamente.

---

# 14. No implementar reset/drop

NO crear:

`db-reset`
`db-drop`
`db-drop-database`
`db-clean-all`

Loop 06 únicamente autoriza reseed de datos controlados.

---

# 15. Implementación

Preferir módulos separados y pequeños, por ejemplo:

```text
backend/news/
├── reseed.py
├── reseed_check.py
└── ...
```

o una estructura equivalente coherente con el código actual.

No crear una abstracción compleja de migrations.

---

# 16. Resultado estructurado

La lógica interna de reseed debe devolver información estructurada equivalente a:

```text
deleted_locations
deleted_news
inserted_locations
inserted_news
preserved_external
```

para poder probarla sin parsear stdout.

No incluir datos sensibles.

---

# 17. Errores parciales

Diseñar comportamiento explícito ante fallos.

Como mínimo:

## Fallo antes de delete

Cero modificaciones.

## Fallo después de delete y antes de completar seed

Reportar claramente estado incompleto.

No afirmar rollback si MongoDB no lo realizó.

No introducir transacciones complejas sin justificarlo.

## Fallo de checks posteriores

Reportar que el reseed terminó pero la verificación falló.

No ocultarlo.

Documentar estas limitaciones.

---

# 18. Atomicidad

NO asumir atomicidad multi-colección.

El flujo debe ser honesto:

- las operaciones ocurren en pasos;
- puede existir fallo intermedio;
- `db-bootstrap`/seeders idempotentes permiten recuperación.

No introducir transactions multi-documento salvo necesidad demostrada.

---

# 19. Tests TDD

Cubrir como mínimo:

## Confirmation

- confirmación incorrecta → aborta;
- confirmación vacía → aborta;
- confirmación local exacta → permite;
- confirmación Atlas exacta → permite;
- frase local no autoriza Atlas.

## Dry run

- no escribe;
- reporta conteos reales;
- identifica externos;
- target correcto.

## Ownership

- reconoce locations controladas;
- reconoce news controladas;
- no clasifica externos como controlados;
- drift peligroso aborta.

## Reseed

- elimina news antes de locations;
- reconstruye locations antes de news;
- termina 16 + 32;
- segunda ejecución produce mismo dataset;
- preserva externos;
- preserva las otras cinco colecciones.

## Failure

- preflight fallido → cero deletes;
- fallo intermedio reportado correctamente.

## Bootstrap

- DB vacía → schema + 16 + 32;
- segunda ejecución → sin duplicados.

## Verify

- todo correcto → OK;
- schema drift → falla;
- catalog drift → falla;
- news drift → falla.

La suite normal permanece offline.

---

# 20. Local verification

Antes de cualquier prueba destructiva real:

`make db-test`

Después ejecutar:

`make db-reseed-dry-run`

Verificar visualmente el plan.

Solo después se puede probar `db-reseed` en Mongo local.

El agente está autorizado a realizar reseed destructivo SOLO en Mongo local durante este loop si:

- el dry run es correcto;
- los tests pasan;
- la DB target es inequívocamente local.

Después verificar:

```text
locations: 16
news: 32
schema: OK
catalogs: OK
news check: OK
```

---

# 21. Atlas

IMPORTANTE:

El agente NO está autorizado a ejecutar automáticamente `db-reseed` destructivo contra Atlas.

Puede ejecutar:

`db-reseed-dry-run`

contra Atlas.

La ejecución destructiva real de Atlas requiere confirmación humana fuera del agente.

El handoff debe entregar al desarrollador:

- dry-run observado;
- comando exacto;
- frase exacta requerida.

El humano decidirá si ejecutarlo.

---

# 22. Makefile

Mantener targets anteriores.

Agregar:

```text
db-bootstrap
db-verify
db-reseed-dry-run
db-reseed
```

No agregar comandos destructivos adicionales.

---

# 23. Documentación

Actualizar:

- `backend/news/README.md`;
- `docs/design/database/README.md`;
- documentación pertinente del Makefile.

Crear:

`docs/design/database/11-automatizacion-y-reseed.md`

Debe explicar:

- bootstrap;
- verify;
- ownership;
- dry-run;
- confirmación;
- orden;
- preservación de externos;
- local vs Atlas;
- failure modes;
- recuperación;
- por qué no existe drop/reset.

---

# 24. Diagrama

Revisar `07-diagrama.md`.

No debería requerir cambio estructural porque no se agregan colecciones.

Solo modificar si necesita una nota operativa realmente útil.

---

# 25. Security review

Aplicar `security-compliance`.

Evaluar como mínimo estos abuse cases:

1. usuario ejecuta reseed contra Atlas creyendo estar en local;
2. confirmación vacía/automática;
3. documento externo coincide parcialmente con patrón;
4. script elimina toda la colección;
5. secreto aparece en logs;
6. fallo parcial deja DB inconsistente.

Documentar controles implementados.

No ejecutar scanner sobre `keys/`.

---

# 26. Code review

Antes del commit aplicar `code-reviewer`.

Revisar especialmente:

- delete filters;
- ownership;
- target mode;
- confirmation;
- dry run;
- preservación de externos;
- failure handling;
- tests;
- documentación.

Cualquier hallazgo mayor debe corregirse.

---

# 27. Trazabilidad

Verificar:

```text
[ ] models
[ ] schema
[ ] catalogs
[ ] demo news
[ ] seeders
[ ] reseed
[ ] bootstrap
[ ] verify
[ ] tests
[ ] documentation
[ ] diagram
[ ] Makefile
[ ] secrets/bootstrap
```

---

# 28. Seguridad final

Confirmar:

```text
secret values exposed: NO
keys read directly: NO
assistant modified: NO

drop database executed: NO
drop collection executed: NO
external documents deleted: NO

Atlas destructive reseed executed by agent: NO
```

---

# Commit

Si Definition of Done está completa:

`feat: add safe database reseed automation`

No hacer push.

---

# Handoff

Crear:

`backend/loops/handoffs/06-db-automation-result.md`

Debe incluir:

1. Resultado.
2. Skills utilizadas.
3. Bootstrap.
4. Verify.
5. Ownership.
6. Dry run.
7. Confirmation.
8. Reseed algorithm.
9. Failure handling.
10. Tests.
11. Local dry run.
12. Local reseed.
13. Local final state.
14. Atlas dry run.
15. Atlas manual command.
16. Atlas required confirmation.
17. Security review.
18. Code review.
19. Makefile.
20. Documentation.
21. Trazabilidad.
22. Seguridad.
23. Archivos modificados.
24. Decisiones.
25. Blockers.
26. Git.
27. Información para Loop 07.

---

# Definition of Done

Loop 06 termina cuando:

- existe `db-bootstrap`;
- bootstrap es idempotente;
- existe `db-verify`;
- existe dry-run de reseed;
- dry-run no escribe;
- ownership es explícito;
- reseed requiere confirmación humana fuerte;
- Atlas y local tienen confirmaciones diferenciadas;
- no existe bypass trivial;
- reseed elimina únicamente datos controlados;
- externos se preservan;
- otras cinco colecciones se preservan;
- orden delete/rebuild es correcto;
- failure modes están documentados;
- tests pasan;
- local reseed fue probado;
- Atlas dry-run fue probado si entorno lo permite;
- agente NO ejecutó reseed destructivo en Atlas;
- security-compliance fue aplicado;
- code-reviewer fue aplicado;
- documentación está sincronizada;
- Makefile está sincronizado;
- ningún secreto fue expuesto;
- existe handoff;
- existe commit.

---

# Stop Conditions

Detener y solicitar decisión humana si:

- no puede demostrarse ownership antes de borrar;
- el reseed requeriría borrar documentos externos;
- se necesita drop collection/database;
- se necesita modificar schema/modelos;
- se requiere leer `keys/`;
- se necesita ejecutar reseed destructivo en Atlas para completar automáticamente el loop;
- se necesita modificar `backend/assistant/`.

No resolver silenciosamente.

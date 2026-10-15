# Loop 05 — Generador de noticias demo

## Objetivo

Implementar un generador reproducible de noticias de desarrollo/demo para AI Assisted News App.

Las noticias generadas deben permitir probar posteriormente:

- feed por ubicación simulada;
- feed por topics;
- noticias locales/nacionales/internacionales;
- estados de verificación;
- fuentes;
- imágenes y disclosure de IA;
- tiempo estimado de lectura;
- chat basado en noticias publicadas;
- personalización futura.

Este loop implementa únicamente:

- generación determinista de noticias demo;
- validación con los modelos existentes;
- persistencia segura/idempotente;
- comprobación del dataset;
- tests;
- Makefile;
- documentación;
- verificación local y Atlas.

NO implementar:

- IA real;
- llamadas a APIs;
- scraping;
- generación real de imágenes;
- chatbot;
- feed;
- personalización;
- users demo;
- userInteractions;
- chatSessions;
- aiUsage;
- auditLogs;
- reseed destructivo.

---

# Skills

## Principal

Usar:

`.skills/test-driven-development/SKILL.md`

Aplicar:

red → green → refactor

## Complementaria

Usar `planning-with-files` únicamente si la complejidad real lo justifica.

## Fallos inesperados

Usar:

`.skills/systematic-debugging/SKILL.md`

antes de intentar fixes.

## Antes del commit

Usar:

`.skills/code-reviewer/SKILL.md`

sobre el diff completo.

No utilizar otras skills sin trigger real.

---

# Lecturas obligatorias

Antes de modificar código leer:

- `AGENTS.md`;
- handoffs 00–04;
- `docs/design/database/`;
- `backend/news/models/`;
- `backend/news/schema/`;
- `backend/news/topics.py`;
- implementación de catálogos/seeders;
- `backend/news/README.md`;
- `Makefile`.

No reinterpretar el esquema aprobado.

---

# Estado heredado

Loop 04 dejó:

- 7 colecciones físicas;
- 7 validators;
- 10 índices;
- 16 locations;
- 14 topics versionados;
- catálogo idempotente;
- `db-seed-check`;
- 148 tests;
- local y Atlas verificados.

Atlas fue comprobado manualmente con:

```text
Catalog check: OK
Locations: 16/16
Duplicates: 0

Locations inserted: 0
Locations unchanged: 16

Database schema: OK
Collections: 7/7
Validators: OK
Indexes: OK
TTL: OK
```

No repetir Loop 04.

---

# 1. Principio del generador

El generador debe producir noticias sintéticas de desarrollo.

Las noticias NO representan acontecimientos reales.

Debe quedar explícitamente documentado que son:

`DEMO / SYNTHETIC DATA`

No utilizar noticias reales ni inventar hechos atribuyéndolos a organizaciones reales.

No usar IA.

No usar Internet.

No usar APIs externas.

---

# 2. Reproducibilidad

La generación debe ser determinista.

La misma configuración debe producir:

- mismos slugs;
- mismos títulos;
- mismos topics;
- mismas locations;
- mismos estados;
- mismo contenido;
- mismos timestamps de fixture cuando corresponda;
- mismos IDs cuando sea necesario.

No depender de:

- random sin seed;
- fecha/hora actual;
- UUID aleatorio;
- ObjectId aleatorio cuando afecte identidad del dataset.

El objetivo es que dos desarrolladores puedan generar el mismo dataset lógico.

---

# 3. Cantidad inicial

Generar exactamente:

`32 noticias demo`

Razón:

- 2 noticias por cada uno de los 16 países.

Esto permite comprobar distribución geográfica sin crear un dataset excesivo.

No generar más durante este loop.

---

# 4. Distribución geográfica

Cada uno de los 16 países del catálogo debe tener exactamente:

`2 noticias`

Las noticias deben utilizar:

`geographicScope.level = country`

y referenciar mediante `locationIds` el `_id` real/determinista correspondiente al país.

No duplicar locations dentro de `news`.

No agregar nuevas locations.

---

# 5. Cobertura internacional

Además de las 32 noticias country-level, necesitamos poder probar consultas internacionales sin crear más documentos.

Una noticia puede incluir topic:

`internacional`

cuando el contenido sintético corresponda conceptualmente.

NO cambiar `geographicScope.level` de las 32 noticias a `international` arbitrariamente.

Si el diseño exige documentos específicamente `international` para probar ese nivel y eso obliga a superar 32 noticias, detener esa decisión y reportarla antes de ampliar el dataset.

---

# 6. Topics

Todas las noticias deben utilizar exclusivamente valores definidos en:

`backend/news/topics.py`

Cada noticia debe tener:

- mínimo 1 topic;
- preferiblemente 1–3 topics;
- sin duplicados internos.

El dataset debe cubrir los 14 topics al menos una vez cuando sea razonablemente posible.

No introducir nuevos topics.

---

# 7. Estados de publicación

El dataset debe permitir probar:

`draft`
`published`

Distribución propuesta:

- 28 `published`;
- 4 `draft`.

Los drafts deben estar distribuidos entre diferentes países.

Los drafts:

- no deben tener `publishedAt`;
- deben cumplir el modelo existente.

Las published:

- deben tener `publishedAt`;
- deben tener tiempos de lectura coherentes.

---

# 8. Verification status

Cubrir los cuatro estados:

- `confirmed`;
- `developing`;
- `insufficient_sources`;
- `conflicting_sources`.

La mayoría puede ser `confirmed`, pero los otros tres deben aparecer varias veces para permitir probar UI/chat.

No asignar confidence numérico.

---

# 9. Sources

Cada noticia debe tener fuentes sintéticas claramente identificables como demo.

NO utilizar dominios reales de medios u organizaciones.

Utilizar dominios reservados/seguros para ejemplos cuando el modelo requiera HTTP(S), por ejemplo:

`https://example.com/...`

Los nombres deben dejar claro que son fuentes demo.

Ejemplo conceptual:

`Demo News Source`

No afirmar que `example.com` respalda hechos reales.

Las noticias `confirmed` deben permitir probar múltiples fuentes cuando sea útil.

Las `insufficient_sources` deben representar claramente ese escenario.

Las `conflicting_sources` deben contener fuentes sintéticas que permitan representar contradicción.

No implementar fact checking.

---

# 10. Imágenes

No generar imágenes reales.

Las noticias pueden utilizar:

- `none`;
- `illustration`;
- `ai_generated`;
- `ai_modified`;
- `photograph`;

únicamente como fixtures para probar comportamiento del modelo/UI.

Para `ai_generated` y `ai_modified` debe cumplirse `aiDisclosure`.

Las URLs, si existen, deben utilizar recursos sintéticos/placeholder seguros y cumplir las validaciones actuales.

No descargar imágenes.

No hacer requests HTTP.

El dataset debe incluir al menos:

- una `ai_generated`;
- una `ai_modified`;
- una `illustration`;
- una `photograph`;
- una `none`.

---

# 11. AI Assistance

Los campos `aiAssistance` deben ser coherentes con la noticia demo.

No registrar `aiUsage`, porque no se realizará ninguna llamada IA.

Especialmente:

`imageGenerated`

debe respetar las reglas del modelo.

---

# 12. Tiempo de lectura

NO hardcodear manualmente valores incoherentes.

Utilizar las funciones existentes:

- `count_words`;
- `estimate_reading_minutes`;
- `compute_reading_time`;

o la interfaz equivalente implementada.

Cada published debe terminar con:

`wordCount`
`estimatedReadingMinutes`

coherentes con `content`.

El dataset debe incluir contenidos de distintas longitudes para probar al menos:

- ~1 minuto;
- ~2 minutos;
- >=3 minutos.

No inflar artificialmente todos los contenidos solo para conseguir tiempos largos.

---

# 13. Autor

`news.authorId` requiere referencia a `users`.

Loop 05 tiene prohibido crear users demo.

Por tanto, NO inventar silenciosamente un usuario persistido.

Antes de implementar persistencia de news, revisar cómo el dataset/demo existente resuelve `authorId`.

Si actualmente existe un mecanismo aprobado/determinista de fixture que permite validar noticias sin insertar users, puede reutilizarse únicamente si no viola referencias conceptuales.

Si persistir las noticias exige necesariamente crear un user/admin demo, DETENER esa parte y solicitar decisión humana.

No crear users sin autorización.

---

# 14. Identidad de noticias

`slug` es la identidad natural del dataset demo.

Los slugs deben:

- ser deterministas;
- ser únicos;
- ser estables;
- ser legibles;
- no depender de `_id`.

El seeder debe comprobar existencia por `slug`.

No modificar noticias existentes con el mismo slug.

No sobrescribir contenido.

---

# 15. Persistencia idempotente

Crear un comando:

`make db-seed-news`

Debe:

1. asegurar schema;
2. asegurar catálogo;
3. generar/obtener las noticias demo;
4. validar cada noticia con `News`;
5. insertar únicamente las faltantes;
6. conservar existentes;
7. no eliminar nada;
8. no modificar documentos existentes.

Resultado esperado inicial:

`inserted: 32`

Segunda ejecución:

`inserted: 0`
`unchanged: 32`

Esto aplica únicamente si la decisión de `authorId` permite persistencia.

---

# 16. Check no destructivo

Crear:

`make db-news-check`

Debe inspeccionar sin modificar.

Debe comprobar como mínimo:

- cantidad esperada;
- slugs únicos;
- 16 países cubiertos;
- 2 noticias por país;
- topics válidos;
- cobertura de topics;
- estados draft/published;
- verification statuses;
- coherencia básica de imágenes;
- tiempos de lectura;
- ausencia de duplicados del dataset.

Si encuentra documentos ajenos:

- reportarlos;
- no eliminarlos;
- distinguir dataset esperado de documentos externos.

No asumir que `news` siempre contendrá únicamente fixtures.

---

# 17. Generador vs Seeder

Separar conceptualmente:

`generar fixtures`
de
`persistir fixtures`

Debe ser posible probar la generación sin MongoDB.

Preferir funciones puras para construir las noticias demo.

El generador no debe conectarse por sí mismo a Atlas.

La capa de seed es la responsable de persistencia.

---

# 18. Tests

Aplicar TDD.

Cubrir como mínimo:

## Generator

- exactamente 32;
- slugs únicos;
- determinismo;
- 2 por país;
- 16 países;
- topics válidos;
- cobertura de topics;
- distribución 28 published / 4 draft;
- cuatro verification statuses presentes;
- imágenes requeridas presentes;
- disclosures IA coherentes;
- todas validan con `News`;
- tiempos de lectura coherentes.

## Seeder

- DB sin fixtures → inserta esperadas;
- segunda ejecución → 0 inserts;
- existente por slug → unchanged;
- no modifica existente;
- no elimina documento ajeno;
- no toca otras colecciones;
- documento inválido no persiste.

## Check

- dataset correcto → OK;
- slug faltante → drift;
- duplicado → drift;
- país incompleto → drift;
- topic inválido → drift;
- documento externo → reportado sin eliminar.

La suite normal debe seguir siendo offline.

---

# 19. Local

Antes de Atlas:

`make db-test`
`make db-init`
`make db-seed-catalogs`
`make db-seed-news`
`make db-seed-news`
`make db-news-check`
`make db-schema-check`

Verificar que únicamente:

- `locations`;
- `news`;

contengan datos creados por estos loops.

Las otras cinco colecciones deben permanecer sin fixtures.

---

# 20. Atlas

Solo después de:

- tests completos;
- local exitoso;
- idempotencia local;
- decisión `authorId` resuelta.

Usar interfaces seguras.

No leer `keys/`.

Ejecutar equivalente a:

`make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-seed-news`
`make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-news-check`

y repetir seed para idempotencia.

No eliminar noticias existentes.

Si Atlas contiene noticias ajenas, conservarlas y reportarlas.

---

# 21. Makefile

Mantener todos los targets existentes.

Agregar:

`db-seed-news`
`db-news-check`

No implementar todavía:

`db-reseed`
`db-reset`
`db-drop`

Eso corresponde al Loop 06.

---

# 22. Documentación

Actualizar según corresponda:

- `backend/news/README.md`;
- `docs/design/database/README.md`;
- `docs/design/database/07-diagrama.md`.

Crear:

`docs/design/database/10-generador-noticias-demo.md`

Documentar:

- propósito;
- carácter sintético;
- 32 noticias;
- distribución;
- determinismo;
- topics;
- verification;
- imágenes;
- sources;
- tiempo de lectura;
- idempotencia;
- comandos;
- limitaciones.

---

# 23. Trazabilidad

Antes de cerrar:

- [ ] modelos revisados
- [ ] schema revisado
- [ ] locations revisadas
- [ ] topics revisados
- [ ] generator sincronizado
- [ ] seeder sincronizado
- [ ] checks sincronizados
- [ ] tests sincronizados
- [ ] documentación sincronizada
- [ ] diagrama revisado
- [ ] Makefile sincronizado
- [ ] secrets/bootstrap revisados

---

# 24. Seguridad

Confirmar:

- secrets exposed: NO;
- keys read directly: NO;
- users inserted: NO;
- userInteractions inserted: NO;
- chatSessions inserted: NO;
- aiUsage inserted: NO;
- auditLogs inserted: NO;
- documents deleted: NO;
- collections dropped: NO;
- indexes dropped: NO;
- database dropped: NO;
- external APIs called: NO;
- AI APIs called: NO.

---

# 25. Code Review

Antes del commit aplicar `code-reviewer`.

Revisar especialmente:

- determinismo;
- fixtures sintéticos;
- idempotencia;
- referencias;
- slugs;
- operaciones Mongo;
- modificación accidental de documentos;
- cobertura de tests;
- seguridad.

Corregir bloqueadores antes del commit.

---

# Commit

Si toda la Definition of Done está satisfecha:

`feat: add deterministic demo news generator`

No hacer push.

---

# Handoff

Crear:

`backend/loops/handoffs/05-news-generator-result.md`

Debe incluir:

1. Resultado.
2. Skills utilizadas.
3. Dataset generado.
4. Distribución geográfica.
5. Topics.
6. Estados.
7. Verification.
8. Sources.
9. Imágenes.
10. Tiempo de lectura.
11. Autor/referencias.
12. Determinismo.
13. Seeder.
14. Check.
15. Tests.
16. Resultado local.
17. Resultado Atlas.
18. Idempotencia.
19. Makefile.
20. Documentación.
21. Trazabilidad.
22. Seguridad.
23. Code review.
24. Archivos modificados.
25. Decisiones.
26. Blockers.
27. Git.
28. Información para Loop 06.

---

# Definition of Done

Loop 05 termina cuando:

- existe generador determinista;
- produce exactamente 32 noticias, salvo Stop Condition autorizada;
- cubre los 16 países;
- utiliza únicamente topics permitidos;
- cubre estados/verification/imágenes necesarios;
- todas las noticias validan con `News`;
- tiempos de lectura son coherentes;
- no usa IA ni APIs externas;
- existe seeder idempotente si `authorId` está resuelto;
- existe check no destructivo;
- tests pasan;
- no hay regresiones;
- local está verificado;
- Atlas está verificado si procede;
- Makefile está sincronizado;
- documentación está sincronizada;
- code-reviewer fue aplicado;
- no se eliminó información;
- existe handoff;
- existe commit.

---

# Stop Conditions

Detener y solicitar decisión humana si:

- persistir news requiere crear un user/admin demo no autorizado;
- se necesita cambiar modelos/schema;
- se necesita modificar índices;
- se necesita agregar locations;
- se necesita agregar topics;
- se necesita superar 32 noticias para cumplir un requisito importante;
- se encuentran noticias Atlas incompatibles que requerirían modificación/eliminación;
- se requiere reseed;
- se requiere acceder directamente a keys/;
- se requiere usar IA/API externa;
- se necesita modificar backend/assistant/.

No resolver silenciosamente.

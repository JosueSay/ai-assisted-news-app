# Loop 05 — News Generator Result

## 1. Resultado

Completed.

Se implementó el generador determinista de noticias demo con TDD
(red → green → refactor): 32 noticias sintéticas (DEMO / SYNTHETIC DATA),
2 por cada uno de los 16 países a nivel `country`, 28 `published` / 4
`draft`, 4 verification statuses, 14 topics cubiertos, 5 tipos de imagen,
tiempos de lectura coherentes y variados. Seeder idempotente por `slug` que
solo escribe en `news` (nunca crea users), check no destructivo, comandos
Makefile, documentación y trazabilidad. Verificado en local (Docker) y Atlas
con idempotencia real en ambos. No se implementó reseed, feed, chat,
frontend ni Firebase; no se modificó `backend/assistant/`.

## 2. Skills utilizadas

| Skill | Uso |
| --- | --- |
| `test-driven-development` (principal) | Red: `test_demo_news.py` (módulo inexistente), luego `test_seed_news.py` + `test_news_check.py` (módulos inexistentes). Green: `demo_news.py` (iterado hasta 12/12: las largas requirieron 3 rondas de ampliación para alcanzar >=401 palabras), `seed_news.py` + `news_check.py` (13/13 a la primera). Refactor: `_spec_sources` de una pasada, eliminación de `_source` muerto, `coherence_issues` en vez de `reading_time_issues` para reportes precisos. |
| `planning-with-files` | No utilizada: el loop trae plan explícito y la tarea se siguió con los todos de la sesión. |
| `systematic-debugging` | No utilizada: el único fallo intermedio fue un assertion esperado en TDD (tier >=3 min), resuelto ampliando fixtures, no un bug. |
| `code-reviewer` | Aplicada antes del commit sobre el diff completo (el script `review_diff.py` no cubre untracked, se revisó manualmente en orden correctness→safety→maintainability→performance→tests). Hallazgos menores corregidos abajo. |
| `security-compliance` | No utilizada: sin cambios de secretos (el loop la excluye salvo trigger real). |

Modelo utilizado: el de esta sesión (ver respuesta final).

## 3. Dataset generado

32 noticias en `backend/news/demo_news.py` (`_SPECS`), función pura
`get_demo_news_documents()` sin conexión a MongoDB. Identidad natural `slug`
(`demo-<cc>-<nn>-<tema>`, únicos, estables, legibles). `_id` deterministas
fijos por posición (`6720...0001`–`6720...0020` hex), timestamps de fixture
fijos (base `2026-09-01` para published con offset determinista, base
`2026-09-05` para drafts). Keywords `[topic, demo, sintetico]`.

## 4. Distribución geográfica

16/16 países con exactamente 2 noticias cada uno, todas con
`geographicScope.level = country` y `locationIds` = `_id` determinista del
catálogo (`CATALOG_LOCATION_IDS`). Sin duplicar locations ni agregar nuevas.

## 5. Topics

Solo valores de `topics.py`, 1–3 por noticia, sin duplicados internos. Los 14
topics aparecen al menos una vez. `internacional` se usa donde el contenido
ficticio lo justifica (clubes de cocina, postales entre escuelas, foro de
plazas) sin cambiar `geographicScope.level` (sigue `country`).

## 6. Estados

28 `published` (con `publishedAt` y lectura coherente) y 4 `draft` (MX, ES,
JP, ZA — países distintos), todos sin `publishedAt`. Los drafts prueban que
lo no publicado no alimenta feed/chat.

## 7. Verification

`confirmed` 20, `developing` 5, `insufficient_sources` 3, `conflicting_sources`
4. Sin confidence numérico. `reviewedBy`/`reviewedAt` en `null` en todas las
fixtures; `notes` declara `DEMO / SYNTHETIC DATA` y el escenario de cada
estado.

## 8. Sources

Todas ficticias: `Demo News Source N (<slug>)` con
`https://example.com/demo/...`. Confirmadas 2–3 fuentes; developing 2;
insufficient 1 deliberada; conflicting 2 con `supports` opuestos dentro de la
ficción. Sin fact checking, sin requests HTTP.

## 9. Imágenes

Sin imágenes reales. `photograph` 9, `illustration` 7, `ai_generated` 4,
`ai_modified` 3, `none` 9. Las `ai_*` llevan `aiDisclosure`; las `none`,
`url`/`alt` nulos; resto con placeholder `https://example.com/demo/img/...`.
`aiAssistance.imageGenerated` coincide con `image.type == ai_generated`
(verificado por test). Sin `aiUsage`.

## 10. Tiempo de lectura

Calculado solo con `compute_reading_time` (200 ppm, mínimo 1), nunca
hardcodeado. Published: 12 con 1 min, 12 con 2 min, 4 con >=3 min. Drafts
también computados (el modelo lo permite) pero no exigidos.

## 11. Autor/referencias

`authorId` = `DEMO_NEWS_AUTHOR_ID` (placeholder sintético determinista,
documentado en el módulo). El diseño satisface `news.authorId -> users._id`
como referencia lógica ObjectId sin foreign keys (01-colecciones,
07-diagrama); modelo y validator solo exigen tipo ObjectId, por lo que
persistir NO requiere insertar ningún user y la Stop Condition no se activó.
No se creó ningún usuario ni admin demo (local y Atlas terminan con
`users: 0`). La correspondencia con un usuario real queda como decisión
humana pendiente (ver §26).

## 12. Determinismo

Dos llamadas a `get_demo_news_documents()` devuelven listas iguales (test
dedicado + slugs estables). Sin azar, sin hora actual, sin IDs aleatorios en
la identidad del dataset.

## 13. Seeder

`backend/news/seed_news.py`: asegura schema, valida las 32 con `News` antes
de escribir (una inválida aborta sin persistir nada), inserta solo faltantes
por `slug`, conserva existentes sin modificar, no elimina nada y no escribe
fuera de `news`. Resultado: `inserted: 32` / segunda `inserted: 0,
unchanged: 32`.

## 14. Check

`backend/news/news_check.py`: solo lectura de `news`. Comprueba cantidad,
slugs únicos, 16 países con 2 noticias, topics válidos y cobertura de los 14,
draft/published, verification, coherencia de imágenes/disclosures y tiempos
de lectura; reporta ajenos sin eliminarlos. `News check: OK` en local y Atlas.

## 15. Tests

`make db-test` → **173 passed** (148 base + 25 nuevos), offline, sin Atlas:

| Archivo | Tests | Cubre |
| --- | --- | --- |
| `test_demo_news.py` | 12 | 32 exactas, slugs únicos/estables, determinismo, 2×16 países, topics válidos/cobertura, 28/4, 4 verification, fuentes demo, 5 imágenes + disclosures, validación `News`, lectura coherente/variada, carácter sintético |
| `test_seed_news.py` | 6 | vacía→32, idempotencia 0/32, existente no se modifica, ajeno preservado, nada fuera de `news`, inválido aborta sin persistir |
| `test_news_check.py` | 7 | OK, faltante→drift, duplicado→drift, país incompleto→drift, topic inválido→drift, externo reportado sin borrar, solo-lectura |

## 16. Resultado local

```text
make db-test            → 173 passed
make db-init            → unchanged (7 colecciones, 7 validators, 10 índices)
make db-seed-catalogs   → inserted 0, unchanged 16
make db-seed-news       → inserted 32, unchanged 0
make db-seed-news       → inserted 0, unchanged 32
make db-news-check      → OK, 32/32, 16/16, drafts 4 / published 28, duplicates 0, external 0
make db-schema-check    → OK (7/7, validators, índices, TTL)
```

Conteos directos: `locations` 16, `news` 32, `users`/`userInteractions`/
`chatSessions`/`aiUsage`/`auditLogs` 0. Tras el refactor se repitió
`db-seed-news` → `inserted: 0, unchanged: 32` y check OK, probando que el
código final genera un dataset idéntico al persistido.

## 17. Resultado Atlas

Solo con interfaces seguras (`make NEWS_DB_MODE=atlas COMPOSE_PROFILES= ...`,
sin leer `keys/`):

```text
db-seed-news (1ra)  → inserted 32, unchanged 0
db-seed-news (2da)  → inserted 0, unchanged 32
db-news-check       → OK, 32/32, 16/16, drafts 4 / published 28, duplicates 0, external 0
```

Atlas no tenía noticias del dataset ni ajenos: terminó con exactamente las 32
esperadas. Nada eliminado ni modificado.

## 18. Idempotencia

Local y Atlas: segunda ejecución `inserted: 0, unchanged: 32`, check OK.
Evidencia en §16 y §17, más re-verificación local post-refactor.

## 19. Makefile

Mantenidos todos los targets. Agregados:

```make
db-seed-news   # siembra el dataset demo (asegura schema, idempotente por slug, solo news)
db-news-check  # inspección no destructiva del dataset (solo lectura, exit 1 si drift)
```

No se implementaron `db-reseed`/`db-reset`/`db-drop` (Loop 06).

## 20. Documentación

- Creado `docs/design/database/10-generador-noticias-demo.md` (propósito,
  carácter sintético, 32 noticias, distribución, determinismo, topics,
  verification, imágenes, sources, lectura, autor, idempotencia, comandos,
  seed vs reseed, limitaciones).
- `docs/design/database/README.md`: fila del documento 10.
- `docs/design/database/07-diagrama.md`: nota del dataset demo (sin entidades
  nuevas; `authorId` sintético documentado).
- `backend/news/README.md`: nuevos archivos, comandos `db-seed-news` /
  `db-news-check`, párrafo Loop 05, tests nuevos, nota de seguridad del seeder.

## 21. Trazabilidad

| Elemento | Revisado | Cambió |
| --- | --- | --- |
| modelos | Sí, `News`/lectura/topics intactos, sin campos nuevos | No |
| schema | Sí, validators/índices sin tocar; seeders solo aseguran schema | No |
| locations | Sí, 16 códigos reutilizados como `locationIds` | No |
| topics | Sí, 14 valores usados sin agregar ninguno | No |
| generator | Nuevo, puro y determinista | Sí |
| seeder | Nuevo, solo-`news`, por `slug` | Sí |
| checks | Nuevo, solo lectura | Sí |
| tests | Sí, 173 passed | Sí (+25) |
| documentación | Sí, 10 + READMEs + diagrama | Sí |
| diagrama | Sí, sin entidades nuevas | Nota mínima |
| Makefile | Sí, targets existentes intactos + 2 nuevos | Sí |
| secrets/bootstrap | Sí, sin secretos nuevos; sin lecturas de `keys/` | No |

## 22. Seguridad

```text
secrets exposed: NO
keys read directly: NO (Atlas solo vía interfaces make; overrides por CLI en local)
external APIs called: NO
AI APIs called: NO
users inserted: NO (local y Atlas terminan con users: 0)
documents deleted: NO
collections dropped: NO
indexes dropped: NO
database dropped: NO
assistant modified: NO
```

## 23. Code review

Revisión manual del diff completo (correctness, safety, maintainability,
performance, tests) tras descartar el script por no cubrir untracked:

- **Mayor: ninguno.** Sin bloqueadores.
- **Menor 1 (corregido):** edición que eliminó por error el guard
  `if self.external:` dejando el append incondicional; restaurado y
  verificado (check OK en ambos modos tras el fix).
- **Menor 2 (corregido):** `_source()` invocado 3 veces por fuente;
  reemplazado por `_spec_sources()` de una pasada y eliminado el helper muerto.
- **Menor 3 (corregido):** fallos de disclosure caían en
  `reading_time_issues`; renombrado a `coherence_issues` con etiqueta propia.
  Sin dependencias en tests; suite 173 tras el cambio.
- **Menor 4 (corregido):** indentación incidental de 2 líneas preexistentes en
  `backend/news/README.md`; restaurada.
- Verificado: sin stragglers (`reading_time_issues` no aparece en el árbol),
  seeder sin escrituras fuera de `news`, checks sin escritura, fixtures sin
  atribuciones reales, tests con nombres de comportamiento.

## 24. Archivos modificados

```text
M Makefile
M backend/news/README.md
M docs/design/database/07-diagrama.md
M docs/design/database/README.md
+ backend/news/demo_news.py
+ backend/news/seed_news.py
+ backend/news/news_check.py
+ backend/news/tests/test_demo_news.py
+ backend/news/tests/test_seed_news.py
+ backend/news/tests/test_news_check.py
+ docs/design/database/10-generador-noticias-demo.md
+ backend/loops/handoffs/05-news-generator-result.md (este archivo)
```

## 25. Decisiones

1. **Estructura plana** (`demo_news.py`, `seed_news.py`, `news_check.py`):
   convención establecida por Loops 02–04 e importada por los tests.
2. **Placeholder `authorId` determinista sin persistir users**: el diseño solo
   exige referencia lógica ObjectId (sin FK), así que la persistencia no
   requiere users; no se inventó admin demo y la autoría real queda pendiente
   (§26). Alternativa descartada: bloquear toda persistencia; no procedía
   porque la Stop Condition exige inserción *necesaria* de users, que no existe.
3. **`reviewedBy = null` en todas las fixtures**: minimiza referencias
   pendientes a un único campo (`authorId`).
4. **Seeder sin `seed_catalog_data`**: para no escribir en `locations`; el
   catálogo es prerrequisito documentado (`db-seed-catalogs` antes). En tests
   offline las locations quedan vacías y el seed igual es válido.
5. **Contenido redactado a mano** (no plantillas): párrafos distintos por
   noticia con marcos ficticios coherentes; niveles de longitud por
   ampliación iterativa guiada por tests.
6. **`planning-with-files` no usada**: plan del loop suficiente.

## 26. Blockers

Ninguno bloqueó el loop. Decisiones humanas pendientes (no bloqueantes):

1. **Autoría real**: asignar `authorId`/`reviewedBy` a `users` reales cuando
   exista el flujo editorial (futuro loop). El placeholder sintético debe
   reemplazarse o mapearse entonces.
2. **Nivel `international` como `geographicScope`**: si se necesita probar ese
   nivel con documentos dedicados, decidir si se amplía el dataset más allá de
   32 (Stop Condition reportada, no resuelta silenciosamente).
3. **Reseed destructivo**: sigue pendiente de Loop 06 con autorización explícita.

## 27. Git

Commit (sin push, Conventional Commits):

```text
feat: add deterministic demo news generator
```

Verificado pre-commit: `make db-test` (173 passed), `db-seed-news`
(idempotente), `db-news-check` OK, `git diff` completo revisado,
`git diff --check` limpio, `git status` (solo archivos del loop 05 +
handoff), sin secretos en staging, sin cambios en `backend/assistant/`. Hash
en respuesta final.

## 28. Información para Loop 06

- Partir del dataset verificado en local y Atlas (32/32 OK en ambos).
- `db-seed-news` + `db-news-check` disponibles y probados en ambos modos.
- `seed_demo.py` (5 noticias + demo user con upsert) sigue existiendo pero es
  previo al Loop 05: no usarlo como referencia de autoría; el dataset vigente
  es el de `demo_news.py` y no crea users.
- Reseed/reset/drop siguen sin implementarse: corresponden al Loop 06 con
  autorización explícita.
- Si Loop 06 toca `news`, debe preservar los 32 slugs o reportar drift con
  `db-news-check`.

# Loop 04 — Catalog Seeders Result

## 1. Resultado

Completed.

Se implementaron los catálogos y seeders del Loop 04 con TDD (red → green →
refactor): 16 locations a nivel `country` con identidad `countryCode`, catálogo
estático versionado de 14 topics (sin colección MongoDB), seeder idempotente por
clave natural, inspección no destructiva, comandos Makefile, documentación y
trazabilidad. Verificado en local (Docker) y Atlas con idempotencia real.
No se generaron noticias, no se implementó reseed, no se modificó
`backend/assistant/`.

## 2. Skills utilizadas

| Skill | Uso |
| --- | --- |
| `test-driven-development` (principal) | Red: 4 archivos de tests primero (2 errores de colección + campos inexistentes). Green: `topics.py`, refactor de `seed_catalog.py`, `seed_check.py`, Makefile. Refactor: corrección de test de solo-lectura, sincronización de READMEs. |
| `planning-with-files` | No utilizada: el loop trae plan explícito y la tarea es una unidad coherente seguida con la lista de todos del prompt. |
| `systematic-debugging` | No utilizada: no hubo fallos inesperados (el único error intermedio fue el RED esperado). |
| `code-reviewer` | Aplicada antes del commit sobre el diff completo + checklist de la skill. Sin bloqueadores; 1 hallazgo menor documentado abajo. |
| `security-compliance` | No utilizada: sin cambios de secretos (el loop la excluye salvo trigger real). |

Modelo utilizado: el de esta sesión (ver respuesta final).

## 3. Locations implementadas

16 países a nivel `country`, códigos ISO correctos y únicos:

```text
CA Canadá, MX México, GT Guatemala, CR Costa Rica, AR Argentina, BR Brasil,
CU Cuba, JM Jamaica, ES España, FR Francia, JP Japón, CN China, EG Egipto,
ZA Sudáfrica, AU Australia, NZ Nueva Zelanda
```

Cada documento valida con el modelo `Location`: `level=country`, `city`/`region`
nulos, `active=true`, sin GPS, sin `isSimulated`. Los datos ya existían en
`seed_catalog.py` (PR #2) y se conservaron intactos.

## 4. Topics implementados

Nuevo `backend/news/topics.py` (catálogo estático, sin colección MongoDB, sin
validator ni índices):

```text
actualidad, tecnologia, ciencia, economia, negocios, politica, deportes, salud,
educacion, cultura, entretenimiento, medio_ambiente, seguridad, internacional
```

API mínima: `get_topics()`, `is_valid_topic()` (membresía exacta),
`normalize_topic()` (solo recorte + minúsculas; `Tecnología` y `technology` se
rechazan, sin traducciones ni plegado de acentos). Sin IA.

## 5. Estrategia de identidad/idempotencia

- Identidad natural: `countryCode`. El seeder usa
  `find_one({"countryCode": code})`; si existe cuenta `unchanged` y no escribe;
  si falta hace `insert_one` con `_id` determinista fijo por código.
- Cambio respecto al PR #2: antes `replace_one` por `_id` (sobrescribía y no
  detectaba duplicados por código). Ahora un documento previo con el mismo
  código pero distinto `_id` no se duplica ni se reescribe; un ajeno (`US`)
  se preserva.
- `CatalogSeedResult` renombrado a `inserted`/`unchanged` (lenguaje del loop);
  `seed_demo.py` actualizado al nuevo campo. Segunda ejecución:
  `inserted: 0, unchanged: 16`.
- No se agregó índice único sobre `countryCode` (decisión pendiente con Loop 03).
  Limitación conocida: `find_one` + `insert_one` no es atómico; con ejecución
  concurrente podría duplicar. El uso es un operador por Makefile, documentado.

## 6. Tests

`make db-test` → **148 passed** (126 base + 22 nuevos), offline, sin Atlas:

| Archivo | Tests | Cubre |
| --- | --- | --- |
| `test_topics.py` (nuevo) | 8 | catálogo exacto, unicidad, formato estable, válida/inválida, normalización, no-string |
| `test_catalog_data.py` (nuevo) | 5 | 16 entradas, códigos esperados, sin duplicados, nombres, validación con `Location` |
| `test_seed_catalog.py` (ampliado 2→6) | 6 | vacía→16, idempotencia 0/16, existente no duplica ni se modifica, ajeno preservado, otras colecciones sin documentos, inválido no persiste |
| `test_seed_check.py` (nuevo) | 5 | OK, faltante→drift, duplicado→drift, inesperado reportado sin borrar, solo-lectura |
| `test_schema_initialize.py` (helper) | +`find` | `FakeCollection.find()` mínimo para el check offline |

## 7. Resultado local

Con `NEWS_DB_MODE=local COMPOSE_PROFILES=news-local` (overrides por CLI, sin
leer ni modificar `.env`):

```text
make db-test            → 148 passed
make db-init            → 7 colecciones, 7 validators, 10 índices
make db-seed-catalogs   → inserted 16, unchanged 0
make db-seed-catalogs   → inserted 0, unchanged 16
make db-seed-check      → OK, 16/16, duplicates 0
make db-schema-check    → OK (7/7, validators, índices, TTL)
```

Inspección directa en Mongo local: 16 locations, 16 `countryCode` distintos,
0 niveles no-`country`, 0 inactivos, 0 documentos en las otras 6 colecciones.
`news.topics` demo existentes (`actualidad`, `tecnologia`, `economia`,
`cultura`, `deportes`) pertenecen al catálogo; `topics` verificado en contenedor
(14, válida/inválida correctas).

## 8. Resultado Atlas

Solo con interfaces seguras (`make NEWS_DB_MODE=atlas COMPOSE_PROFILES= ...`,
stderr descartado en operaciones de conexión, sin leer `keys/`):

```text
db-check-config   → atlas, ai_assisted_news, MongoDB credential: configured
db-seed-catalogs  → inserted 16, unchanged 0
db-seed-catalogs  → inserted 0, unchanged 16
db-seed-check     → OK, 16/16, duplicates 0
```

Atlas no tenía catálogo previo ni ajenos: terminó con exactamente las 16
entradas, sin duplicados ni inesperados. Nada eliminado. (Credencial admin
`missing`: irrelevante, solo afecta al panel admin.)

## 9. Segunda ejecución/idempotencia

Local y Atlas: segunda ejecución `inserted: 0, unchanged: 16`, check OK.
Evidencia en secciones 7 y 8.

## 10. Makefile

Mantenidos todos los comandos. Agregados:

```make
db-seed-catalogs  # siembra solo catálogos autorizados, asegura schema, idempotente
db-seed-check     # inspección no destructiva (solo lectura, exit 1 si drift)
```

`db-seed-catalog` (singular) se conserva como alias. Ninguno pide confirmación
(no destructivos). No se implementó reseed.

## 11. Documentación

- Creado `docs/design/database/09-catalogos-y-seeders.md` (16 países y por qué,
  identidad `countryCode`, topics y por qué no es colección, idempotencia,
  comandos, seed vs reseed, decisión pendiente de validación cerrada).
- `docs/design/database/README.md`: fila del documento 09.
- `docs/design/database/07-diagrama.md`: nota de 16 países + topics estático
  (sin entidades nuevas; topics no es colección).
- `backend/news/README.md`: archivos `topics.py`/`seed_check.py`, comandos
  `db-seed-catalog(s)`/`db-seed-check`, párrafo Loop 04, tests nuevos.

## 12. Trazabilidad

| Elemento | Revisado | Cambió |
| --- | --- | --- |
| modelos | Sí, `Location`/strings de topics intactos | No |
| schema | Sí, validators/índices sin tocar; seeder solo asegura schema existente | No |
| catálogos | Sí, 16 códigos + 14 topics | Sí (topics nuevo) |
| seeders | Sí, identidad por `countryCode`, sin escrituras ajenas | Sí |
| documentación | Sí, 09 + READMEs + diagrama | Sí |
| diagrama | Sí, sin entidades nuevas | Nota mínima |
| tests | Sí, 148 passed | Sí (+22) |
| Makefile | Sí, alias conservado + 2 targets | Sí |
| secrets/bootstrap | Sí, sin secretos nuevos; `setup-keys`/`keys/README.md` ya cubren 4 archivos | No |

## 13. Seguridad

```text
secret values exposed: NO
keys/ leído: NO (.env no leído; overrides por CLI)
secret files tracked: NO (git ls-files keys → solo README, verificado en commit)
assistant modified: NO
users/userInteractions/chatSessions/aiUsage/auditLogs/news insertados: NO
documentos/colecciones/índices eliminados: NO
reseed: NO
```

## 14. Archivos modificados

```text
M Makefile
M backend/news/README.md
M backend/news/seed_catalog.py
M backend/news/seed_demo.py
M backend/news/tests/test_schema_initialize.py  (helper find)
M backend/news/tests/test_seed_catalog.py
M docs/design/database/07-diagrama.md
M docs/design/database/README.md
+ backend/news/topics.py
+ backend/news/seed_check.py
+ backend/news/tests/test_topics.py
+ backend/news/tests/test_catalog_data.py
+ backend/news/tests/test_seed_check.py
+ docs/design/database/09-catalogos-y-seeders.md
+ backend/loops/handoffs/04-catalog-seeders-result.md (este archivo)
```

No incluidos en el commit: `backend/loops/04-catalog-seeders.md` y
`backend/prompts/04-catalog-seeders.md` (cambios preexistentes a esta sesión,
archivos del loop, no implementación).

## 15. Review findings

Code-reviewer sobre el diff completo (correctness, safety, maintainability,
performance, tests):

- **Mayor: ninguno.** Sin bloqueadores.
- **Menor 1 (aceptado, sin cambio):** `check_catalog_data` ordena códigos con
  `sorted()`; un documento sin `countryCode` (clave `None`) rompería el
  ordenado mixto. Imposible en Mongo real (validator exige `countryCode`
  string); no se agrega defensa especulativa.
- **Menor 2 (documentado, sin cambio):** sin índice único en `countryCode`, el
  seed concurrente podría duplicar (§5). Uso previsto: un operador por
  Makefile. La decisión del índice único queda pendiente con Loop 03.
- Verificado: sin stragglers del renombre (`locations_upserted` restante solo
  en `DemoSeedResult`, fuera de alcance); `db-seed-catalog` alias intacto;
  tests con nombres de comportamiento; asserts significativos.

## 16. Decisiones

1. **Estructura plana** (`seed_catalog.py`, `topics.py`, `seed_check.py`) en vez
   de `seeders/` paquete: convención ya establecida e importada por
   `seed_demo.py`; el loop permite ajustarla.
2. **Insert-if-missing por `countryCode`** en vez de `replace_one` por `_id`:
   nunca modifica ni duplica existentes; `_id` determinista solo en inserción.
3. **Validación cerrada de topics en modelos: NO implementada.** Convertir
   strings libres en enum cerrado es cambio funcional significativo; el
   catálogo existe standalone. Decisión humana pendiente (documentada en 09).
4. **Índice único `locations.countryCode`: NO creado.** Pendiente con Loop 03
   según Stop Conditions; reportado, no resuelto silenciosamente.
5. **`unexpected` cuenta como drift** (check `ok=False`, exit 1), coherente con
   `schema/check.py` (`unexpected_collections` → no-OK). Ajenos se reportan,
   nunca se borran.
6. **`planning-with-files` no usada**: plan del loop suficiente; progreso en
   todos de la sesión.

## 17. Blockers

Ninguno. Sin decisiones humanas pendientes salvo las ya reportadas como
pendientes de diseño (índice único `countryCode`, validación cerrada de
topics, futuro reseed), ninguna bloquea este loop.

## 18. Git

Commit (sin push, Conventional Commits):

```text
feat: add database catalog seeders
```

Verificado pre-commit: `git diff` completo revisado, `git status` (solo
archivos del loop 04 + handoff), `git diff --check` limpio, 148 tests passed,
sin secretos en staging, sin cambios en `backend/assistant/`. Hash en respuesta
final.

## 19. Información para Loop 05

- Partir de catálogo verificado en local y Atlas (16/16 OK en ambos).
- `db-seed-catalogs` + `db-seed-check` disponibles y probados en ambos modos.
- Topics demo existentes pertenecen al catálogo; validación cerrada pendiente.
- No generar noticias demo en Loop 04 (cumplido: 0 docs en `news` local tras
  seed; Atlas seed solo tocó `locations` + estructura).
- `seed_demo.py` sigue funcional (tests 2/2) y consume el nuevo resultado.

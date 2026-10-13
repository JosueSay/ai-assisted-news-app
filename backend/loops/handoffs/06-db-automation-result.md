# Loop 06 — DB Automation Result

## 1. Resultado

Completed.

Se implementó la automatización operativa con TDD (red → green → refactor):
`db-bootstrap` idempotente, `db-verify` solo-lectura, `db-reseed-dry-run` no
destructivo y `db-reseed` destructivo controlado con ownership versionado,
preflight, confirmación exacta diferenciada por modo y orden
news→locations / locations→news. Verificado en local (reseed real dos
veces, 16+32, checks OK) y Atlas (solo dry-run + checks no destructivos).
Sin secretos expuestos, sin `drop`, sin bypass. No se adelantó Loop 07.

## 2. Skills utilizadas

| Skill | Uso |
| --- | --- |
| `test-driven-development` (principal) | Red: 3 archivos de tests primero (31 tests, fallo inicial `ModuleNotFoundError: news.reseed` como corresponde). Green: `reseed.py`, `bootstrap.py`, `verify.py`, `reseed_dry_run.py` + Makefile. Refactor: ajuste de 1 aserción (honestidad sobre rollback), fix de indentación en README. |
| `security-compliance` | Threat model de 6 abuse cases (§17), secret scan en rutas acotadas (`backend/news`, `Makefile`, doc 11): 9 hallazgos preexistentes también en baseline sin mis cambios; 0 nuevos. Scanner nunca ejecutado sobre `keys/`. |
| `systematic-debugging` | No utilizada: ningún fallo inesperado (el único fallo intermedio fue aserción propia en TDD, causa raíz inmediata). |
| `code-reviewer` | Aplicada sobre el diff completo + grep de deletes/drops/CONFIRM. 1 hallazgo menor corregido (indentación del árbol en README). Sin bloqueadores. |
| `planning-with-files` | No utilizada: el loop trae plan explícito. |

Modelo utilizado: el de esta sesión (ver respuesta final).

## 3. Bootstrap

`backend/news/bootstrap.py`: `initialize_schema` + `seed_catalog_data` +
`seed_news_data` + `check_schema`/`check_catalog_data`/`check_news_data`.
Idempotente, sin deletes, sin confirmación. Local (DB ya poblada por Loop
05): `inserted 0, unchanged 16/32, Bootstrap: OK`.

## 4. Verify

`backend/news/verify.py`: solo lectura (`check_schema`, `check_catalog_data`,
`check_news_data`). Verifica schema (colecciones, validators, índices, TTL),
16 locations y 32 news. Local y Atlas: `Database verification: OK`.
Documenta exactamente qué verifica en el propio formato y en el doc 11.

## 5. Ownership

`classify_controlled()` en `backend/news/reseed.py`: locations por
`countryCode` + `_id` determinista (`CATALOG_LOCATION_IDS`); news por `slug`
+ `_id` determinista (`get_demo_news_documents()`). Externos contados como
preservados, nunca eliminables. Drift (duplicado o `_id` inesperado en
identidad controlada) aborta con cero modificaciones.

## 6. Dry run

`backend/news/reseed_dry_run.py` + `plan_dry_run()`: inspección real,
cero escrituras (tests lo prueban por snapshot + contadores). Local y
Atlas: `locations to delete: 16, demo news to delete: 32`, externos 0/0,
`No changes performed.`

## 7. Confirmation

`expected_confirmation()` / `is_confirmation_valid()`: local
`RESEED ai_assisted_news`, Atlas `RESEED ATLAS ai_assisted_news`.
Coincidencia exacta o aborto (vacío, Enter, `y`, `yes`, base incorrecta).
Frase local jamás autoriza Atlas (test dedicado). CLI lee `CONFIRM` del
entorno; Makefile lo reenvía con `-e CONFIRM="$(CONFIRM)"`. Sin `--force`;
tests usan `execute_reseed()` programático, separado del CLI humano.

## 8. Reseed algorithm

`execute_reseed()`: confirmación → target → preflight (schema + ownership)
→ `delete_many({"_id": {"$in": [...]}})` en news (32) y luego locations
(16) → seed locations → seed news → checks. Resultado estructurado
(`deleted_locations/deleted_news/inserted_locations/inserted_news/
preserved_external`, orden, checks). Orden verificado por test de log.

## 9. Failure handling

- Previo a delete: aborto con `aborted=True`, cero modificaciones
  (confirmación, modo/base, schema, drift; DB vacía aborta por schema e
  indica usar bootstrap).
- Intermedio: `incomplete=True` + error parcial honesto, declara
  explícitamente `No rollback was performed` y recuperación vía
  `db-bootstrap` (test con seed saboteado).
- Posterior: `verification_failed=True` con flags por check, sin ocultar
  (externos preservados reportan drift estricto honestamente).

## 10. Tests

`make db-test` → **204 passed** (173 base + 31 nuevos), offline:

| Archivo | Tests | Cubre |
| --- | --- | --- |
| `test_reseed.py` | 22 | 5 confirmación, 5 ownership/drift, 2 dry-run, 7 reseed (orden, 16+32, idempotencia, externos, 5 colecciones, filtros, no-drop), 3 fallos |
| `test_bootstrap.py` | 3 | vacía→schema+16+32, segunda sin duplicados, preserva ajenos sin deletes |
| `test_verify.py` | 6 | OK, 3 drifts, solo-lectura |

Fakes `TrackedFakeCollection/TrackedFakeDatabase` (extienden los de Loop
03): registran orden, prohíben `delete_many({})` y solo aceptan `_id $in`.

## 11. Local dry run

```text
=== AI Assisted News — Reseed Dry Run ===
Database: ai_assisted_news
Mode: local
Controlled data:
- locations to delete: 16
- demo news to delete: 32
Preserved: users, userInteractions, chatSessions, aiUsage, auditLogs,
external locations, external news
External (preserved, not deleted): locations=0 news=0
No changes performed.
```

## 12. Local reseed

Autorizado por el loop (target inequívocamente local). Sin `CONFIRM`
abortó con exit 1 y cero cambios (guard probado en real). Con
`CONFIRM="RESEED ai_assisted_news"`:

```text
Deleted demo news: 32
Deleted locations: 16
Inserted locations: 16
Inserted news: 32
Preserved external: 0
Order: delete_news, delete_locations, seed_locations, seed_news, checks
Verification: OK (schema, catalogs, demo news).
```

## 13. Local final state

`db-verify` OK tras el reseed; segundo reseed idéntico (32/16 → 16/32,
checks OK). Estado: schema 7/7, locations 16/16, news 32/32, resto de
colecciones intactas (0 docs ajenos creados por el loop).

## 14. Atlas dry run

Solo dry-run + checks no destructivos (reseed real prohibido al agente):

```text
Database: ai_assisted_news
Mode: atlas
- locations to delete: 16
- demo news to delete: 32
External: locations=0 news=0
No changes performed.
```

`db-verify` y `db-schema-check` en Atlas: OK (7/7, validators, índices,
TTL). Comando usado:
`make db-reseed-dry-run NEWS_DB_MODE=atlas COMPOSE_PROFILES=`.

## 15. Atlas manual command

Para que el desarrollador lo ejecute manualmente cuando lo decida:

```bash
make db-reseed-dry-run NEWS_DB_MODE=atlas COMPOSE_PROFILES=
make db-reseed NEWS_DB_MODE=atlas COMPOSE_PROFILES= CONFIRM="RESEED ATLAS ai_assisted_news"
```

## 16. Atlas required confirmation

```text
RESEED ATLAS ai_assisted_news
```

Debe coincidir exactamente (variable `CONFIRM`). La frase local
`RESEED ai_assisted_news` jamás autoriza Atlas.

## 17. Security review

Threat model (abuso → impacto → mitigación):

1. Reseed contra Atlas creyendo estar en local → escritura masiva
   equivocada → modo desde settings + frases diferenciadas + `Mode`
   visible en dry-run; tests.
2. Confirmación vacía/automática → borrado accidental → match exacto,
   falsy aborta, `CONFIRM` sin default autorizante; probado sin CONFIRM
   en local real (abortó, exit 1).
3. Externo coincide parcialmente → borrado ajeno → ownership exige
   identidad completa; parcial = drift o preservado; tests.
4. Script elimina colección completa → pérdida total → solo `_id $in`
   versionado, sin `delete_many({})`, sin filtros amplios, sin `drop`;
   fakes rechazan borrados amplios; grep confirma 2 deletes acotados.
5. Secreto en logs → exposición → outputs solo con db/mode/conteos;
   secret scan sin hallazgos nuevos (9 preexistentes = baseline).
6. Fallo parcial inconsistente → estado oculto → `incomplete` honesto,
   sin claim de rollback, recuperación documentada; tests.

`keys/` nunca leído (solo existencia previa); `backend/assistant/`
intacto.

## 18. Code review

Revisión del diff completo (correctness→safety→maintainability→
performance→tests) + grep de deletes/drops/CONFIRM:

- **Mayor: ninguno.**
- **Menor 1 (corregido):** indentación del árbol de tests rota en
  `backend/news/README.md`; restaurada.
- Verificado: deletes acotados, ownership completo, target/mode
  validados, dry-run sin escritura, preservación, failure honesto,
  tests de comportamiento, docs sincronizadas.

## 19. Makefile

Mantenidos todos los targets. Agregados: `db-bootstrap`, `db-verify`,
`db-reseed-dry-run`, `db-reseed` (con reenvío `-e CONFIRM`). Ningún
comando destructivo adicional (`db-reset`/`db-drop` no existen).

## 20. Documentation

- Creado `docs/design/database/11-automatizacion-y-reseed.md`
  (bootstrap, verify, ownership, dry-run, confirmación, orden,
  preservación, local vs Atlas, failure modes, recuperación, por qué no
  hay drop/reset).
- `docs/design/database/README.md`: fila del documento 11.
- `docs/design/database/07-diagrama.md`: nota operativa mínima (orden y
  preservación; sin entidades nuevas).
- `backend/news/README.md`: módulos, comandos, tests y notas de
  seguridad del reseed.
- `keys/README.md`: sin cambios (no hay secretos nuevos; `CONFIRM` es
  entrada CLI, no archivo).

## 21. Trazabilidad

| Elemento | Revisado | Cambió |
| --- | --- | --- |
| modelos | Sí, intactos | No |
| schema | Sí, solo lectura/asegurado | No |
| catalogs | Sí, reutilizados como identidades | No |
| demo news | Sí, reutilizadas como identidades | No |
| seeders | Sí, reutilizados sin modificar | No |
| reseed | Nuevo núcleo + CLI | Sí |
| bootstrap | Nuevo | Sí |
| verify | Nuevo | Sí |
| tests | Sí, 204 passed | Sí (+31) |
| documentation | Sí, 11 + READMEs + diagrama | Sí |
| diagram | Sí, sin entidades nuevas | Nota mínima |
| Makefile | Sí, targets intactos + 4 nuevos | Sí |
| secrets/bootstrap | Sí, sin secretos nuevos | No |

## 22. Seguridad

```text
secret values exposed: NO
keys read directly: NO
assistant modified: NO
drop database executed: NO
drop collection executed: NO
external documents deleted: NO
Atlas destructive reseed executed by agent: NO
```

## 23. Archivos modificados

```text
M Makefile
M backend/news/README.md
M docs/design/database/07-diagrama.md
M docs/design/database/README.md
+ backend/news/reseed.py
+ backend/news/reseed_dry_run.py
+ backend/news/bootstrap.py
+ backend/news/verify.py
+ backend/news/tests/test_reseed.py
+ backend/news/tests/test_bootstrap.py
+ backend/news/tests/test_verify.py
+ docs/design/database/11-automatizacion-y-reseed.md
+ backend/loops/handoffs/06-db-automation-result.md (este archivo)
```

## 24. Decisiones

1. **Cuatro módulos pequeños** (`reseed`, `reseed_dry_run`, `bootstrap`,
   `verify`) siguiendo la convención plana de Loops 02–05.
2. **`CONFIRM` como variable de entorno** (sin `--force`): simple,
   auditable, aborta en vacío; Makefile la reenvía al contenedor.
3. **Reseed en DB vacía aborta** (schema previo falla) e indica bootstrap:
   separa responsabilidades en vez de mezclar seed con reseed.
4. **Checks estrictos post-reseed**: externos preservados se reportan
   como drift sin ocultarlo (§17), en vez de relajar los checks de Loops
   04/05.
5. **`setup-keys`/`keys/README.md` sin cambios**: no hay secretos nuevos.
6. **Local sin `.env`**: se usó `.env.example` como base; los defaults del
   Makefile (`NEWS_DB_MODE=local`) bastaron.

## 25. Blockers

Ninguno bloqueó el loop. Pendiente humano (no bloqueante): ejecutar el
reseed real en Atlas (§15–16) cuando lo decida; el dataset Atlas ya está
verificado (16/32 OK) así que no es urgente.

## 26. Git

Commit (sin push, Conventional Commits):

```text
feat: add safe database reseed automation
```

Verificado pre-commit: `make db-test` (204 passed), `git diff`,
`git diff --check` limpio, `git status` (solo archivos del loop 06 +
handoff), sin secretos en staging, sin cambios en `backend/assistant/`.

## 27. Información para Loop 07

- Partir de local y Atlas verificados (16/32 OK en ambos tras este loop).
- Automatización disponible: `db-bootstrap`, `db-verify`,
  `db-reseed-dry-run`, `db-reseed CONFIRM="..."`.
- `authorId` sigue placeholder sintético (Loop 05, pendiente); el reseed
  lo preserva tal cual.
- Si Loop 07 toca `news`/`locations`, el reseed sigue siendo la vía de
  reconstrucción; cualquier identidad nueva debe entrar a `demo_news.py`/
  `seed_catalog.py` antes de reseedear.

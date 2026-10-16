# Local Bootstrap Drift Diagnosis — Result

## Identificación y objetivo

- Loop: `local-bootstrap-drift-diagnosis`.
- Fecha: 2026-10-15.
- Estado: diagnóstico completado, sin commit ni push.
- Objetivo: explicar el fallo de `db-bootstrap` / `db-verify` durante el arranque
  local guiado y permitir continuar sin eliminar datos existentes.
- Handoffs previos revisados: `chatbot-provider-selection-result.md` y
  `news-shared-contract-result.md`.
- Skill aplicada: `.skills/systematic-debugging/SKILL.md`; reproducción,
  localización del chequeo estricto y comparación con el seeder histórico.

## Evidencia y causa

El usuario reportó esquema y catálogos correctos, 32 noticias insertadas y
`Demo news: DRIFT`. Se ejecutó únicamente el inspector de noticias, de solo lectura:

```bash
docker compose --profile tools run --rm news-tools python -m news.news_check
```

Resultado: exit 1, `News: 37/32`, `Countries: 16/16`, `Drafts: 4 Published: 28`,
`Duplicates: 0`, `External: 5`. No se reportaron faltantes, temas inválidos,
temas sin cubrir ni problemas de coherencia en las 32 fixtures canónicas.

Los cinco slugs externos coinciden con `DEMO_NEWS` de `backend/news/seed_demo.py`:

- `liga-comunitaria-canchas-vecindario`;
- `mercado-digital-comunitario`;
- `paseo-peatonal-comercio-descanso`;
- `ruta-lectura-aire-libre`;
- `sensores-huertos-urbanos`.

La causa es la coexistencia del dataset histórico de cinco noticias con las 32
fixtures aprobadas. `NewsCheckResult.ok` trata cualquier noticia externa como
drift; bootstrap y verify propagan ese resultado. Es el comportamiento diseñado,
documentado en `docs/design/database/11-automatizacion-y-reseed.md` y cubierto por
`test_news_check_reports_external_without_deleting`. La comprobación estricta del
dataset demo no representa por sí sola un fallo de conexión o esquema.

## Decisiones y cambios

- Conservar las 37 noticias y los checks estrictos aprobados.
- Continuar la prueba local con API, chat y frontend. El arranque no ejecuta
  `db-verify` como condición de salud.
- No ejecutar reseed ni eliminar documentos; el reseed controlado tampoco es una
  herramienta para retirar noticias externas.
- No modificar modelos, esquema, seeders ni verificadores.
- Único archivo creado durante este diagnóstico: este handoff.

## Verificaciones

- Inspector real de noticias sobre la DB local: diferencia reproducida y acotada
  a cinco slugs externos. El inspector no escribe en MongoDB.
- Se revisaron el código del checker, bootstrap, verify, seeder histórico,
  documentación aprobada y test existente de preservación de noticias externas.
- Comparación con `42285068fc8571a933a9ca47d03e0b98e3386f67` de modelos, schema,
  seeders, fixtures, news_check, bootstrap, verify y diagrama: sin diferencias.
- No se añadieron ni ejecutaron tests unitarios: no hay cambios de comportamiento.
- `git diff --check`: correcto.
- Staging vacío. Working tree conserva los cambios anteriores sin commit y añade
  este documento. No se modifica historia Git.
- No se abrió ni modificó contenido de `keys/`; no se hicieron llamadas a IA.

## Trazabilidad

- [x] Modelos: revisados, sin cambios.
- [x] Documentación: diagnóstico registrado; contrato estricto aprobado conservado.
- [x] Diagrama: revisado, sin cambio estructural.
- [x] Tests: revisado el caso existente de noticias externas; sin cambios.
- [x] Makefile: revisado, sin cambios en este diagnóstico.
- [x] Secrets/bootstrap: mismos requisitos y comportamiento, sin cambios.

## Continuidad y pendientes

Sin bloqueo para iniciar los servicios. Siguiente paso guiado:

```bash
docker compose up -d news-api chatbot frontend
docker compose ps
```

El resultado de `db-verify` seguirá siendo no cero mientras existan noticias
externas; no se afirma que la verificación integral haya pasado. Cualquier
eliminación requeriría una decisión humana explícita y queda fuera del diagnóstico.

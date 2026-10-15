Ejecuta:

backend/loops/07-db-final-verification.md

Este es el loop final del trabajo de base de datos.

NO implementes nuevas funcionalidades.

## Preparación

Lee:

- AGENTS.md;
- Loop 07 completo;
- handoffs 00–06;
- docs/design/database/;
- backend/news/;
- Makefile;
- docker-compose.yml;
- configuración y documentación relevante.

Comprende primero el sistema completo antes de modificar archivos.

## Skills

Skill principal:

.skills/code-reviewer/SKILL.md

Debes revisar el trabajo completo de DB, no únicamente el último commit.

También debes utilizar:

.skills/security-compliance/SKILL.md

para auditoría final de seguridad.

Usa test-driven-development únicamente si descubres un defecto real que necesite corrección.

Usa systematic-debugging si alguna verificación falla inesperadamente.

planning-with-files solo si la auditoría necesita memoria multi-fase.

Respeta AGENTS.md por encima de cualquier skill.

## Objetivo

Demostrar que el trabajo DB es:

- correcto;
- reproducible;
- idempotente;
- documentado;
- seguro;
- utilizable por un desarrollador nuevo.

No adelantes trabajo de backend/producto.

## Reproducibilidad local

Debes probar una reconstrucción desde cero usando una DB local temporal y aislada.

No destruyas la DB local normal.

No uses Atlas para esta prueba destructiva.

Demuestra:

DB nueva
→ bootstrap
→ 7 colecciones
→ 16 locations
→ 32 news
→ verify OK
→ segundo bootstrap
→ 0 duplicados
→ verify OK

Si necesitas limpiar la DB temporal después, hazlo únicamente si puedes demostrar inequívocamente que es la DB temporal creada por esta sesión.

Nunca uses un drop genérico contra una DB configurable.

## Atlas

Solo operaciones no destructivas.

Ejecuta:

make db-verify NEWS_DB_MODE=atlas COMPOSE_PROFILES=

NO ejecutes db-reseed contra Atlas.

El desarrollador ya verificó manualmente el dry-run de Loop 06; no es necesario repetir operaciones sin valor adicional.

## Tests

Ejecuta:

make db-test

Baseline mínimo:

204 passed.

Cero regresiones.

## Auditoría

Compara explícitamente:

docs
↔ models
↔ schema
↔ validators/indexes
↔ datasets
↔ automation
↔ tests

Busca inconsistencias reales.

No cambies diseño solo para "mejorarlo".

## Decisiones pendientes

No resuelvas automáticamente:

- unique de locations.countryCode;
- validación cerrada de topics;
- authorId sintético;
- geographicScope international dedicado.

Audítalas y déjalas documentadas como follow-ups si siguen siendo válidas.

## Seguridad

Aplica security-compliance.

Nunca escanees keys/.

Revisa especialmente:

- secretos tracked;
- .env;
- Docker mounts;
- comandos destructivos;
- delete filters;
- reseed;
- logs.

Confirma que Atlas no reciba operaciones destructivas durante este loop.

## Code review

Aplica code-reviewer al sistema DB completo.

Clasifica hallazgos:

BLOCKER
MAJOR
MINOR
FOLLOW-UP

Corrige BLOCKER/MAJOR únicamente cuando la corrección esté dentro del alcance del Loop 07.

Si requiere cambiar diseño, detente.

## Documentación

Crear:

docs/design/database/12-verificacion-final.md

Debe funcionar como resumen técnico final y punto de entrada para nuevos desarrolladores.

Actualizar READMEs únicamente cuando exista información desactualizada o faltante.

## Verificación final

Antes del commit:

make db-test

git status
git diff
git diff --check

Confirma:

secret values exposed: NO
secret files tracked: NO
keys read directly: NO
assistant modified: NO
Atlas destructive operations: NO
external documents deleted: NO
drop database on Atlas: NO
drop collections: NO

## Commit

Si no existen BLOCKER/MAJOR pendientes:

docs: finalize database verification and reproducibility

Si hubo corrección de código significativa, usa un mensaje apropiado y explícala en el handoff.

No hagas push.

## Handoff

Crear:

backend/loops/handoffs/07-db-final-verification-result.md

Sigue exactamente la estructura requerida por Loop 07.

## Respuesta final

Reporta únicamente:

1. estado;
2. handoff;
3. modelo;
4. skills utilizadas;
5. reproducibilidad desde cero;
6. idempotencia;
7. tests;
8. Atlas verification;
9. security audit;
10. destructive operations audit;
11. code review findings;
12. documentación;
13. decisiones pendientes/follow-ups;
14. trazabilidad;
15. archivos modificados;
16. commit;
17. estado final de Git;
18. blockers.

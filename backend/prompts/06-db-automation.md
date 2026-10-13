Ejecuta:

backend/loops/06-db-automation.md

## Preparación

Lee:

- AGENTS.md;
- Loop 06 completo;
- handoffs 00–05;
- docs/design/database/;
- backend/news/;
- Makefile;
- docker-compose.yml.

No repitas Loops anteriores.

## Skills obligatorias

Principal:

.skills/test-driven-development/SKILL.md

Usa red → green → refactor.

Por tratarse de operaciones destructivas también debes utilizar:

.skills/security-compliance/SKILL.md

No ejecutes secret_scan.py sobre keys/.

Si aparece un fallo inesperado:

.skills/systematic-debugging/SKILL.md

Antes del commit:

.skills/code-reviewer/SKILL.md

No cargues otras skills sin trigger real.

## Objetivo

Implementa únicamente la automatización definida por Loop 06:

- db-bootstrap;
- db-verify;
- db-reseed-dry-run;
- db-reseed.

No adelantes Loop 07.

## Restricción crítica

Tienes autorización para probar reseed destructivo únicamente contra MongoDB LOCAL.

NO ejecutes db-reseed destructivo contra Atlas.

Para Atlas:

- dry-run: permitido;
- checks no destructivos: permitidos;
- reseed real: requiere ejecución manual posterior por el desarrollador.

No intentes rodear esta restricción.

## TDD

Implementa primero tests para:

- confirmación;
- ownership;
- dry-run;
- reseed;
- preservación;
- failures;
- bootstrap;
- verify.

Después implementación mínima y refactor.

## Seguridad

Antes de cualquier delete:

1. target mode conocido;
2. database conocida;
3. schema válido;
4. ownership comprobado;
5. dry-run coherente;
6. confirmación exacta.

Nunca uses:

delete_many({})

Nunca uses filtros amplios como:

{status: ...}
{level: ...}
{topics: ...}

Los deletes deben derivarse exclusivamente de las identidades versionadas del dataset controlado.

No uses drop.

## Confirmación

Local y Atlas deben requerir frases diferentes.

Una confirmación local jamás debe autorizar Atlas.

No agregues --force como bypass.

## Local

Después de tests offline:

1. dry-run;
2. inspecciona resultado;
3. reseed local;
4. db-verify;
5. segunda comprobación/idempotencia apropiada.

Está autorizado.

## Atlas

Ejecuta únicamente:

- dry-run;
- checks no destructivos.

No ejecutes reseed real.

Incluye en el handoff el comando y confirmación exacta para que el desarrollador pueda hacerlo manualmente.

## Reviews

Antes del commit:

1. aplica security-compliance;
2. corrige problemas;
3. aplica code-reviewer al diff completo;
4. corrige problemas;
5. ejecuta regression final.

## Verificación final

Confirma:

secret values exposed: NO
keys read directly: NO
assistant modified: NO
drop database executed: NO
drop collection executed: NO
external documents deleted: NO
Atlas destructive reseed executed by agent: NO

Ejecuta:

make db-test
git diff
git diff --check
git status

## Commit

Solo si Definition of Done completa:

feat: add safe database reseed automation

No hagas push.

## Handoff

Crear:

backend/loops/handoffs/06-db-automation-result.md

Sigue exactamente la estructura del loop.

## Continuidad

Si cambia agente/modelo:

- conservar working tree;
- leer AGENTS.md + loop + prompt;
- revisar diff/status;
- ejecutar tests relevantes;
- continuar desde estado real;
- no repetir trabajo válido.

## Respuesta final

Reporta únicamente:

1. estado;
2. handoff;
3. modelo;
4. skills;
5. tests;
6. bootstrap;
7. verify;
8. local dry-run;
9. local reseed;
10. Atlas dry-run;
11. comando manual Atlas;
12. confirmación Atlas requerida;
13. security review;
14. code review;
15. trazabilidad;
16. seguridad;
17. commit;
18. blockers.

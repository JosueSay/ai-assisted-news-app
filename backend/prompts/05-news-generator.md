Ejecuta:

backend/loops/05-news-generator.md

## Preparación

Lee primero:

- AGENTS.md;
- Loop 05 completo;
- handoffs 00–04;
- docs/design/database/;
- backend/news/models/;
- backend/news/schema/;
- backend/news/topics.py;
- seeders/checks existentes;
- Makefile.

No repitas Loops 00–04.

## Skills

Usa obligatoriamente como principal:

.skills/test-driven-development/SKILL.md

Sigue:

red → green → refactor

Usa planning-with-files únicamente si la complejidad real lo justifica.

Si aparece un fallo inesperado, activa systematic-debugging antes de intentar fixes.

Antes del commit aplica code-reviewer sobre el diff completo.

No cargues skills sin trigger real.

## Objetivo

Implementa exclusivamente el generador determinista de noticias demo definido en Loop 05.

No adelantes Loop 06.

No implementes reseed/reset/drop.

No implementes frontend, feed, chat ni Firebase.

No utilices IA ni APIs externas.

## Regla crítica: authorId

Antes de persistir cualquier noticia determina cómo el diseño actual satisface:

news.authorId -> users._id

Loop 05 NO autoriza crear users.

No inventes silenciosamente un admin demo.

Si la persistencia requiere necesariamente insertar un user/admin:

DETENTE antes de persistir en local o Atlas.

Completa todo lo que pueda realizarse offline:

- generator;
- fixtures;
- tests;
- documentación;

y reporta la decisión humana requerida.

No conviertas esta Stop Condition en una decisión propia.

## Fixtures

Todo contenido debe ser claramente sintético.

No atribuyas acontecimientos inventados a organizaciones, gobiernos, medios o personas reales.

Usa fuentes demo y dominios reservados.

No hagas requests HTTP.

## Trabajo

Trabaja incrementalmente:

leer
→ test RED
→ implementación mínima
→ GREEN
→ refactor
→ siguiente comportamiento
→ generator completo
→ tests
→ evaluar authorId
→ persistencia local si está autorizada
→ idempotencia
→ check
→ Atlas si procede
→ documentación
→ code review
→ correcciones
→ regression
→ handoff
→ commit

No declares una fase completa sin evidencia.

## Seguridad

Nunca leas directamente keys/.

No elimines ni modifiques documentos existentes para conseguir que los checks pasen.

No insertes datos en colecciones distintas de news durante este loop.

No uses aiUsage porque no habrá llamadas IA.

## Atlas

No tocar Atlas hasta:

- tests offline OK;
- local OK;
- authorId resuelto;
- idempotencia local OK.

Si existe Stop Condition, NO intentes rodearla.

## Verificación final

Antes del commit:

- make db-test;
- checks del dataset;
- git diff;
- git diff --check;
- git status;
- code-reviewer.

Confirma explícitamente:

secrets exposed: NO
keys read directly: NO
external APIs called: NO
AI APIs called: NO
documents deleted: NO
collections dropped: NO
database dropped: NO
assistant modified: NO

## Commit

Solo si la Definition of Done está satisfecha:

feat: add deterministic demo news generator

No hagas push.

Si el loop queda bloqueado por authorId u otra Stop Condition, no inventes una solución para poder crear el commit.

## Continuidad

Si cambia el modelo/agente:

- conservar working tree;
- leer AGENTS.md + loop + prompt;
- revisar git status/diff;
- ejecutar tests;
- continuar desde el estado real;
- no reiniciar trabajo válido.

## Respuesta final

Reporta únicamente:

1. estado;
2. handoff;
3. modelo;
4. skills utilizadas;
5. dataset generado;
6. tests;
7. resolución/estado de authorId;
8. resultado local;
9. resultado Atlas;
10. idempotencia;
11. code review;
12. trazabilidad;
13. seguridad;
14. commit;
15. blockers/decisiones humanas.

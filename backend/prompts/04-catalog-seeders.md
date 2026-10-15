Ejecuta:

backend/loops/04-catalog-seeders.md

Lee primero:

- AGENTS.md
- el loop completo;
- handoffs 00–03;
- docs/design/database/;
- backend/news/models/;
- backend/news/schema/;
- Makefile.

## Skills obligatorias

Usa como skill principal:

.skills/test-driven-development/SKILL.md

Sigue red → green → refactor.

Usa planning-with-files únicamente si determinas que la tarea realmente requiere planificación multi-fase.

Si aparece un fallo inesperado:
usa systematic-debugging antes de proponer fixes.

Antes del commit:
usa code-reviewer para revisar el diff completo.

Respeta todos los guardarraíles de AGENTS.md.

## Objetivo

Implementa únicamente los catálogos y seeders definidos por Loop 04.

No adelantes Loop 05.

No generes noticias.

No implementes reseed.

No modifiques backend/assistant/.

## Forma de trabajo

Trabaja incrementalmente:

leer
→ test que falla
→ implementación mínima
→ test pasa
→ refactor
→ siguiente comportamiento
→ tests completos
→ local
→ Atlas si corresponde
→ idempotencia
→ documentación
→ code review
→ correcciones
→ regression
→ handoff
→ commit

No marques una fase como completa sin evidencia.

## Atlas

Primero completa tests y verificación local.

Solo después utiliza las interfaces seguras existentes para Atlas.

Nunca leas directamente keys/.

No elimines datos existentes para hacer que el test pase.

Si Atlas contiene datos incompatibles, detente y repórtalo.

## Cambio de modelo/agente

Si esta sesión se interrumpe:

- conserva el working tree;
- el siguiente agente debe leer AGENTS.md, loop y prompt;
- revisar git status/diff;
- ejecutar tests relevantes;
- continuar desde la primera tarea pendiente;
- no reiniciar el loop.

## Commit

Solo si Definition of Done está completa:

feat: add database catalog seeders

No hagas push.

## Respuesta final

Reporta únicamente:

1. estado;
2. handoff;
3. modelo utilizado;
4. skills utilizadas;
5. tests y resultado;
6. resultado local;
7. resultado Atlas;
8. idempotencia;
9. resultado del code review;
10. trazabilidad;
11. seguridad;
12. commit;
13. blockers/decisiones humanas.

Ejecuta:

backend/loops/08-real-news-images.md

## Preparación

Lee:

- AGENTS.md;
- Loop 08 completo;
- handoffs 05–07;
- docs/design/database/;
- backend/news/demo_news.py;
- modelos, seeders y checks relacionados;
- Makefile.

No implementes funcionalidades fuera del Loop 08.

## Skills

Principal:

.skills/test-driven-development/SKILL.md

Sigue red → green → refactor.

Antes del commit:

.skills/code-reviewer/SKILL.md

Usa systematic-debugging únicamente ante fallos inesperados.

Usa security-compliance solo si aparece su trigger real.

## Objetivo

Reemplaza las imágenes placeholder no funcionales del dataset demo por imágenes reales y accesibles para desarrollo/demo.

No confundas "imagen real" con "evidencia real del acontecimiento":

las noticias son sintéticas y cualquier fotografía debe utilizarse únicamente como representación ilustrativa del tema.

## Investigación

Puedes investigar fuentes públicas apropiadas para las imágenes cuando el entorno disponga de acceso web.

Prioriza:

- URLs HTTPS estables;
- procedencia clara;
- derechos/licencia documentables;
- recursos adecuados para demo.

No uses Google Images ni hotlinks arbitrarios de medios.

No uses URLs aleatorias.

No inventes licencias.

Si no puedes verificar procedencia/licencia, no uses la imagen.

## IA

No etiquetes una fotografía externa normal como ai_generated o ai_modified.

Si mantener esos fixtures requiere assets realmente generados/modificados y no existen, activa la Stop Condition y reporta la decisión necesaria.

## TDD

Primero agrega tests offline para las nuevas invariantes.

Los tests normales no deben acceder a Internet.

Después implementa el cambio mínimo.

Crea un check HTTP explícito separado para verificar disponibilidad real.

## Persistencia

No conviertas db-seed-news en updater.

Actualiza fixtures versionadas.

Para local puedes utilizar el reseed seguro existente después de:

- tests;
- image check;
- dry-run.

NO ejecutes reseed destructivo contra Atlas.

Entrega el comando manual para que el desarrollador lo haga después de revisar el handoff.

## Verificación

Ejecuta como mínimo:

make db-test
make db-news-images-check

Después:

- reseed/check local;
- db-verify local;
- dry-run Atlas.

No declares éxito si alguna imagen requerida está rota.

## Review

Aplica code-reviewer al diff completo.

Corrige BLOCKER/MAJOR dentro del alcance.

## Seguridad

Confirma:

secret values exposed: NO
keys read directly: NO
external API credentials used: NO
external documents modified: NO
Atlas destructive reseed executed by agent: NO
assistant modified: NO

## Commit

Si Definition of Done completa:

fix: use real images for demo news

No hagas push.

## Handoff

Crear:

backend/loops/handoffs/08-real-news-images-result.md

## Respuesta final

Reporta únicamente:

1. estado;
2. handoff;
3. modelo;
4. skills;
5. fuente(s) de imágenes;
6. licencias/créditos;
7. cantidad de imágenes actualizadas;
8. tests;
9. HTTP image check;
10. resultado local;
11. Atlas dry-run;
12. comando manual Atlas;
13. code review;
14. seguridad;
15. commit;
16. blockers/decisiones humanas.

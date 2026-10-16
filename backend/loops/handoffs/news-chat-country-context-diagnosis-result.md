# News Chat Country Context Diagnosis — Result

## Identificación y objetivo

- Loop de diagnóstico: `news-chat-country-context-diagnosis`.
- Fecha: 2026-10-15.
- Estado: causa reproducida; comportamiento pendiente de corrección.
- Objetivo solicitado: explicar la respuesta del chat que afirma no tener países
  y cita únicamente cinco noticias históricas.
- Handoff anterior revisado: `local-bootstrap-drift-diagnosis-result.md`.
- Skill aplicada: `.skills/systematic-debugging/SKILL.md`.

## Reproducción y evidencia

El usuario confirmó su mensaje exacto: `que noticias tienes por pais`.
Se reprodujeron la clasificación y selección mediante funciones existentes y
consultas de solo lectura a la MongoDB local, dentro de `news-tools`. No se llamó
al chatbot HTTP ni al proveedor OpenAI.

Resultados observados:

- `classify_message(..., has_news_context=False)` produce `recent_news`, sin códigos
  de país y sin selección de ubicación personal.
- La base contiene 33 noticias publicadas: 28 canónicas y cinco históricas.
- `LISTING_LIMIT` es 5 y la selección reciente ordena por `publishedAt` descendente.
- Las cinco publicaciones más recientes son las demos históricas del 3 y 4 de
  octubre de 2026. Las fixtures canónicas empiezan en septiembre de 2026.
- Las cinco tienen referencias geográficas que se resuelven a `GT` en `locations`.
- `news_context` envía únicamente `id`, `title`, `summary`,
  `verificationStatus`, `sources` y `publishedAt` para un listado. Omite
  `geographicScope` y no resuelve los nombres/códigos del catálogo.

Las cinco seleccionadas son las mismas que citó la respuesta del usuario. Su
verificación `confirmed` y ausencia de fuentes explican la confianza media
calculada por `compute_confidence`; esa confianza no evalúa si se contestó
correctamente la petición de agrupación por país.

## Causa y alcance

La infraestructura sí conecta el chat con la DB compartida. La integración del
contexto pierde la relación geográfica antes de llegar al modelo. Además, el
clasificador reconoce países concretos y ubicación personal, pero no representa
la solicitud genérica de listar por país. El modelo recibe cinco noticias sin
campos de país y no puede resolver esa carencia desde el contexto autorizado.

No es evidencia de que las 32 fixtures falten ni de que la API key esté mal. La
revisión anterior no cubrió esta combinación de consulta genérica, contexto LLM
y coexistencia con el dataset histórico.

## Cambios, verificaciones y decisiones

- Único archivo creado en este diagnóstico: este handoff.
- Se inspeccionaron `intent.py`, `retrieval.py`, `service.py`, `prompts/news.md`,
  fixtures canónicas, seeder histórico y tests existentes.
- Reproducción local de solo lectura: exit 0, clasificación y cinco resultados
  coincidentes con la respuesta reportada.
- No se añadieron tests ni se implementó una corrección: la solicitud de este
  turno fue explicar la causa.
- No se modificaron modelos, esquema, catálogos, seeders ni documentos MongoDB.
- No se abrieron archivos de `keys/` ni se hicieron llamadas de IA.
- No se registran costos o tokens de la conversación del usuario: no se consultó
  su historial ni telemetría.
- `git diff --check`: correcto. Sin commit, push ni cambios staged; se conserva el
  trabajo anterior y se añade este documento.

## Trazabilidad y continuidad

- [x] Modelos: revisados, sin cambios.
- [x] Documentación: evidencia y limitación del consumidor registradas.
- [x] Diagrama: sin cambios estructurales de MongoDB.
- [x] Tests: revisados los existentes; falta cobertura de este caso para la corrección.
- [x] Makefile: revisado, sin cambios necesarios para el diagnóstico.
- [x] Secrets/bootstrap: mismos requisitos, sin cambios.

Pendiente: representar la petición genérica por país y resolver las referencias
de las noticias contra el catálogo para el contexto de respuesta, con pruebas de
regresión y sin alterar el contrato de DB aprobado. La eliminación de las cinco
noticias históricas no resuelve por sí sola la omisión geográfica ni la clasificación.

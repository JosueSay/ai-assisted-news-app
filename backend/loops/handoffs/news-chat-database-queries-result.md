# News Chat Database Queries — Result

## Identificación y objetivo

- Loop: `news-chat-database-queries`.
- Fecha: 2026-10-15.
- Estado: implementado y verificado; pendiente de que el usuario recree su chatbot.
- Handoff anterior: `news-chat-country-context-diagnosis-result.md`, leído antes
  de implementar; también se revisaron los resultados de bootstrap y contrato compartido.
- Autorización: corregir la consulta por país, el conteo que devolvía cinco noticias
  y el prompt, con acceso efectivo a la DB aprobada en `4228506`.

## Skills aplicadas

| Skill | Evidencia |
| --- | --- |
| `systematic-debugging` | Causa anterior reproducida: clasificación reciente, muestra de cinco y pérdida de geografía. |
| `test-driven-development` | Quince regresiones fallaron antes de implementar; un caso adicional reprodujo la consulta por país con artículo abierto. Veinte regresiones nuevas pasan. |
| `planning-with-files` | Plan y memoria temporal en `/tmp/news-chat-db-queries/task_plan.md`; no se incluyen en Git. |
| `code-reviewer` | Revisión de filtros, referencias, enums existentes, contenido publicado, diff y baseline protegido. |
| `security-compliance` | Tests sin keys/red de IA, escaneo acotado y tabla de controles incluida abajo. |
| OpenAI Docs | Se consultó la documentación oficial de prompt engineering sobre contexto relevante e instrucciones. No se cambian modelo, SDK ni tarifas. |

Referencia oficial consultada:
<https://developers.openai.com/api/docs/guides/prompt-engineering>.

## Cambios

- `backend/assistant/news_chat/intent.py`: reconoce conteos y agrupación por país;
  reutiliza `recent_news`, `regional_news` y `topic_news`. Los indicadores nuevos
  son internos del plan, sin campos/enums nuevos en MongoDB o en el HTTP.
- `backend/assistant/news_chat/retrieval.py`: `count_documents` cuenta la selección
  completa. País/tema se filtran en MongoDB antes de limitar ejemplos. Se resuelven
  referencias geográficas contra `locations`, explicitando IDs sin correspondencia.
- `backend/assistant/news_chat/service.py`: conteos y grupos se resuelven como
  `database_query`, sin llamar al proveedor. Un conteo general distingue total,
  `published` y `draft`; no muestra contenido de borradores. El grupo por país
  cuenta publicaciones y cita un ejemplo por país disponible. Los ejemplos se
  deduplican en `citedNewsIds` cuando una publicación cubre varios países.
- El contexto para otras respuestas con IA añade inventario real, cantidad de
  ejemplos, coincidencias y marca de muestra, topics y ubicaciones resueltas.
- `backend/assistant/prompts/news.md`: prohíbe equiparar muestra y total, usar
  respuestas viejas como inventario actual o inventar países desde títulos/perfiles.
  La verificación de una muestra no se generaliza a toda la colección.
- `backend/assistant/config.py` y `docker-compose.yml`: default del prompt news
  `news-v2`; los modos históricos conservan `assistant-v1` y configuración explícita.
- `.env.example`: documenta la versión opcional del prompt. No se modifica el `.env` real.
- `backend/assistant/tests/test_news_database_queries.py`: veinte casos nuevos.
  `news_fakes.py` admite count_documents, campos anidados y filtros de arreglos.
- `tests/integration/test_news_shared_contract.py`: prueba MongoDB real con los
  datasets canónico y mixto, cobertura de países y cambio de conteo después de
  crear un nuevo borrador mediante la API administrativa de prueba.
- Documentación sincronizada en `backend/assistant/README.md`,
  `docs/architecture/contrato-compartido-noticias.md` y `PR_DESCRIPTION.md`.
- Este handoff cierra el loop y conserva las limitaciones del diagnóstico anterior.

## Pruebas y comandos

Se utilizó la imagen de pruebas con el código montado, sin red ni `keys/`, mediante:

```bash
docker run --rm --network none \
  -e OPENAI_API_KEY_FILE=/tmp/missing-key -e API_GPT= -e CHATBOT_PROVIDER=stub \
  -v /home/donmathiuz/ai-assisted-news-app/backend:/app:ro \
  ai-assisted-news-app-contract-tests:local \
  python -m pytest -c assistant/pyproject.toml assistant/tests news/tests -q -rs -p no:cacheprovider
make news-integration-test
```

Resultados:

- Red inicial: 15 fallos reprodujeron las dos consultas reales y la falta de
  inventario/geografía. Red adicional: artículo abierto desviaba el grupo a `explain`.
- Suite backend final: **294 passed, 2 skipped**. Los omitidos son el smoke HTTP
  externo y la comprobación del archivo TypeScript fuera del montaje offline.
- Veinte regresiones nuevas: incluyen ambos mensajes exactos, más de 200 noticias,
  conteos por país/tema y ubicación elegida, cero publicaciones con borradores,
  actualización de conteos, referencias sin resolver y muestra parcial de cinco.
- MongoDB 8 efímera: **1 passed**. Conteos reales 32/28/4 con las fixtures aprobadas,
  37/33/4 con cinco demos históricas y 38/33/5 tras crear un borrador administrativo.
  Grupos cubren todas las ubicaciones con noticias publicadas; solo se citan publicaciones.
- API/chat mantienen los 14 filtros canónicos, misma identidad admin, validators,
  índices y TTL. `aiUsage` vacío en la integración con stub.
- Ruff check/format, Compose config quiet y `git diff --check`: correctos.
  Ruff sobre bind readonly necesitó `--no-cache`; se corrigió el orden de imports.
- Escaneo seguro acotado: cero hallazgos en código de consultas, prompt, configuración,
  test nuevo y fakes. Un hallazgo `mongodb-uri` en la prueba de integración corresponde
  a la URI del contenedor temporal; no contiene credenciales y no se reproduce su valor.
- Comparación Git contra `4228506` de modelos/schema/TOPICS/seeders/fixtures/
  bootstrap/reseed/news_check/verify/07-diagrama: sin diferencias.

Los tests no consultan Atlas ni montan DB/volúmenes del usuario. El harness retiró
solo sus contenedores/red propios al terminar. No se hicieron llamadas reales a
OpenAI ni se leyeron archivos secretos. La redacción de una respuesta real del
modelo no se evalúa en este loop; conteos y grupos funcionan sin el modelo.

## Decisiones y límites

- La cantidad no está fijada a 32 o 37: se obtiene de la colección actual en cada
  consulta. Los borradores aportan únicamente su cantidad, sin títulos ni contenido.
- Las consultas son filtros estructurados del backend, no ejecución de MongoDB
  arbitraria generada por el usuario o el modelo.
- No se elimina ni excluye silenciosamente ninguna noticia histórica existente.
  El `DRIFT` del verificador estricto de las 32 fixtures seguirá presente si la
  DB del usuario conserva las cinco publicaciones históricas.
- El listado por país presenta cantidades y un ejemplo, no todos los artículos.
  Las noticias de varios países pueden contarse en varios grupos, como indica la respuesta.
- La búsqueda por texto libre conserva su ventana de 200 noticias; conteos y filtros
  estructurados de listados no dependen de esa ventana.
- No se implementa aquí el catálogo completo de capacidades del diagrama JEV.
- No hay nuevas dependencias, colecciones, índices, enums ni operaciones destructivas.

## Controles de seguridad revisados

| Riesgo | Control y evidencia |
| --- | --- |
| Ejecutar consultas arbitrarias del mensaje | Filtros generados desde países/topics conocidos e IDs validados; no eval ni queries suministradas por el modelo. |
| Confundir cinco ejemplos con el total | count_documents sobre toda la selección, inventario explícito y regresión con 242 documentos. |
| Inventar ubicación desde perfil o título | Resolución por ObjectId contra catálogo y test con referencia inexistente. |
| Exponer contenido de borradores | Todas las citas consultan status published; prueba con solo cuatro borradores sin títulos en respuesta. |
| Usar secretos o datos reales en tests | Imagen sin keys, pruebas offline y MongoDB temporal en red interna sin puertos/volúmenes persistentes. |

## Trazabilidad, Git y continuación

- [x] Modelos revisados y sin cambios; mismo contrato aprobado.
- [x] Documentación sincronizada con consultas y límites.
- [x] Diagrama revisado; sin cambios estructurales de DB, `07-diagrama.md` intacto.
- [x] Tests sincronizados: veinte regresiones y MongoDB real temporal.
- [x] Makefile revisado; los comandos existentes cubren tests e integración.
- [x] Secrets/bootstrap revisados; mismos archivos y seeders, sin cambios necesarios.

Sin commit ni push. Staging vacío; working tree conserva el trabajo anterior y
añade este loop. No se modifican `.env`, contenido de `keys/` ni datos de la DB local.
No se recreó el chatbot del usuario automáticamente: el proceso anterior sigue
usando el código importado hasta que se aplique el cambio.

Para aplicar el código montado y el default de versión en Compose, sin rebuild:

```bash
docker compose up -d --force-recreate chatbot
```

Después, en `http://localhost:8081`, repetir las mismas dos preguntas. El conteo debe
reflejar la DB actual (37 total / 33 publicadas / 4 borradores si no hubo otros cambios).
El grupo por país debe incluir el catálogo con publicaciones, en lugar de negar
la información geográfica. «Noticias de México» permite probar además la elaboración
por OpenAI con contexto de país cuando esté habilitado y exista presupuesto.

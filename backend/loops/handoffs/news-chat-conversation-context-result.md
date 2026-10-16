# News Chat Conversation Context — Result

## Identificación y objetivo

- Loop: `news-chat-conversation-context`.
- Fecha: 2026-10-15.
- Estado: corrección implementada y verificada; pendiente de recrear el proceso del usuario.
- Objetivo: que los seguimientos del chat usen la sesión vigente, especialmente la
  secuencia reportada «de que paises son» → oferta del asistente → «ok si hazlo».
- Handoff previo leído: `news-chat-database-queries-result.md`.
- No se leyeron conversaciones reales de MongoDB: la reproducción usa el ejemplo
  proporcionado por el usuario y fixtures de prueba.

## Causa

El frontend conserva sessionId/expiresAt y mensajes en AsyncStorage, y reenvía el
sessionId con cada mensaje. El backend guarda los turnos embebidos y envía al
proveedor los últimos diez mensajes cuando utiliza IA. Sin embargo, clasificaba
la petición actual antes de aprovechar ese historial: «ok si hazlo» terminaba
como `unsupported` y nunca llegaba al modelo. Otras referencias buscaban noticias
nuevas por términos en lugar de usar las citadas en la respuesta anterior.

## Skills

- `systematic-debugging`: inspección frontend → sesión → clasificación → plan → proveedor.
- `test-driven-development`: nueve regresiones fallaron antes de implementar; una
  regresión adicional detectó pérdida de contexto después de un rechazo ajeno a noticias.
- `planning-with-files`: plan fuera del árbol versionado en `/tmp/news-chat-followups-plan.md`.
- `code-reviewer`: revisión de continuidad, referencias, nuevos turnos explícitos,
  aislamiento por usuario, expiración y comparación con el baseline `4228506`.
- `security-compliance`: revisión acotada, pruebas sin keys, escaneo seguro y controles abajo.
- OpenAI Docs: documentación oficial de historial de conversación, sin cambiar SDK,
  modelo, proveedor ni política de almacenamiento externo:
  <https://developers.openai.com/api/docs/guides/conversation-state>.

## Cambios y archivos

- Nuevo `backend/assistant/news_chat/conversation.py`: resuelve seguimientos con los
  mensajes existentes de la sesión, reconstruyendo filtros en memoria. Las consultas
  completas nuevas reemplazan los filtros; las consultas elípticas pueden conservar
  país, tema u operación de conteo. No se añade estado persistido.
- `intent.py`: indicadores internos de uso de citas previas y posición de una referencia.
- `service.py`: consulta la sesión validada antes de resolver el mensaje. Los
  seguimientos pueden conservar toda la selección previa, sin truncarla a tres
  noticias ni sustituirla por artículos recientes ajenos. Las referencias por posición
  usan el orden original y se vuelven a consultar con status published.
- Un rechazo ajeno al dominio no borra el contexto de noticias. Una consulta de
  noticias sin coincidencias deja vacía su selección para no reciclar otra anterior.
- `prompts/news.md`: interpreta aceptaciones y referencias con el historial, solicita
  aclaración cuando una oferta tenía varias opciones y usa lenguaje de aplicación
  sin exponer nombres de campos internos. No debe prometer filtros sin datos resueltos.
- `config.py`, `docker-compose.yml` y `.env.example`: default/documentación `news-v3`.
  Los modos históricos conservan su configuración. El `.env` real no se modifica.
- Nuevo `backend/assistant/tests/test_news_conversation.py`: diecisiete regresiones
  de conversaciones, límites de contexto, publicación, dueño y expiración.
- `tests/integration/test_news_shared_contract.py`: tres turnos reales sobre MongoDB
  temporal mantienen la sesión, sus seis mensajes y las mismas citas.
- `backend/assistant/README.md`, `docs/architecture/contrato-compartido-noticias.md`
  y `PR_DESCRIPTION.md`: comportamiento, versión y validación sincronizados.
- Este handoff registra la evidencia y la continuación.

## Comandos, pruebas y resultados

Los tests offline ejecutan código montado readonly en la imagen de pruebas, con
`--network none`, sin keys y con OPENAI_API_KEY_FILE apuntando a un archivo inexistente:

```text
python -m pytest -c assistant/pyproject.toml assistant/tests/test_news_conversation.py -q -p no:cacheprovider
python -m pytest -c assistant/pyproject.toml assistant/tests news/tests -q -rs -p no:cacheprovider
make news-integration-test
```

- Red inicial: 9 failed, 4 passed. Reprodujo «ok si hazlo», referencias de país,
  resúmenes, cambio de país con tema/conteo y referencias ordinales.
- Red adicional: 1 failed, 14 passed al volver a noticias tras una petición no admitida.
- Suite backend final: **311 passed, 2 skipped**. Se omiten el smoke HTTP externo y
  la comprobación del TypeScript que queda fuera del montaje offline.
- Diecisiete pruebas nuevas pasan. Incluyen el ejemplo exacto de tres turnos,
  conservación de más de tres citas, reconstrucción con otra instancia del servicio,
  cambios explícitos de consulta, selección vacía, ordinal fuera de rango y
  exclusión de artículos que pasan a borrador.
- Integración con MongoDB 8 temporal: **1 passed**. Misma sesión para «Noticias de
  México» → «de que paises son» → «ok si hazlo», seis mensajes embebidos y TTL 3600.
  Continúan pasando los conteos 32/28/4 y 37/33/4, filtros de los 14 topics,
  citas, identidad administrativa y validación de esquema.
- La prueba con proveedor falso verifica que la oferta anterior llega en history
  y las mismas noticias llegan en context. No se hacen llamadas OpenAI reales.
- Ruff check/format sobre archivos afectados, Compose config quiet y git diff --check:
  correctos. Se retiraron imports de prueba no utilizados.
- Escaneo seguro de conversation/intent/service/prompt/test nuevo: cero hallazgos.
- Comparación contra `4228506` de modelos, schema, TOPICS, catálogo, seeders, fixtures,
  bootstrap, verify y diagrama: sin diferencias. Staging vacío.

## Decisiones y límites

- La memoria pertenece únicamente a la sesión activa del usuario: las verificaciones
  de dueño y expiresAt se ejecutan antes de resolver el historial. No se extiende el TTL.
- Los últimos diez mensajes se envían al modelo como antes. Los filtros se reconstruyen
  con el historial embebido existente; no se prometen recuerdos entre sesiones ni
  persistencia de todos los detalles de una conversación larga dentro del contexto LLM.
- Una aceptación de varias alternativas puede requerir aclaración; no significa que
  se haya perdido el historial. El prompt pide no elegir opciones arbitrariamente.
- No se ejecutan instrucciones MongoDB del texto del usuario o del modelo.
- La redacción concreta de una respuesta OpenAI se deja para la prueba manual; el
  alcance verificado aquí es la selección y el envío correcto del contexto/historial.
- No hay cambios de modelos, esquema, seeders, índices, secretos ni dependencias.

## Controles revisados

| Riesgo | Control y evidencia |
| --- | --- |
| Historial de otro usuario o sesión vencida | Carga por userId y expiresAt antes de resolver; regresión con otro usuario y +3601 segundos. |
| Citar un artículo que ya no está publicado | Nueva lectura status published por IDs; prueba al convertir una cita en borrador. |
| Elegir otra noticia al cambiar el conjunto publicado | El ordinal se aplica a los IDs originales antes de volver a consultar. |
| Arrastrar filtros a una petición nueva | Solo seguimientos reconocidos heredan contexto; nueva petición explícita y dominio ajeno probados. |
| Secretos o costos reales durante tests | Sin keys/red de IA; MongoDB efímera sin volúmenes del usuario y proveedores de prueba. |

## Trazabilidad y Git

- [x] Modelos revisados: sin cambios frente al PR aprobado.
- [x] Documentación sincronizada con seguimientos y límites.
- [x] Diagrama revisado: sin cambio estructural; `07-diagrama.md` intacto.
- [x] Tests sincronizados: diecisiete regresiones y flujo MongoDB real.
- [x] Makefile revisado: comandos existentes suficientes, sin cambios necesarios.
- [x] Secrets/bootstrap revisados: mismos requisitos, sin cambios.

Sin commit ni push. El working tree conserva los cambios previos y añade este loop;
staging vacío. No se abrió ni modificó contenido de keys/, ni se modificaron datos de
la DB del usuario. El harness retiró solo sus recursos temporales de prueba.

## Volver a probar

```bash
docker compose up -d --force-recreate chatbot
```

En la misma conversación de la web: «Noticias de México», «de qué países son» y
«ok sí hazlo». El seguimiento debe mantener las citas y dejar de clasificarse como
unsupported. Si la oferta anterior contiene varias alternativas, debe pedir cuál
se desea. La prueba no requiere reseed, cambios de keys ni creación de otra DB.

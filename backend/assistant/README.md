# Asistente modular

Copia modularizada del chatbot de `G-T-NOVU-Prototipo/chatbot`. Conserva FastAPI, la Responses API,
el endpoint `/chat`, el encadenamiento mediante `previous_response_id` y el cliente de terminal. La
copia no depende del resto del prototipo original.

## Qué cambió

- El prompt ya no está escrito dentro del código: vive en [`prompts/system.md`](prompts/system.md).
- El proveedor de IA es intercambiable: `openai` para uso real y `stub` para pruebas locales.
- El contexto es intercambiable: sin DB, una proyección `assistant_contexts` o las colecciones NOVU.
- MongoDB sólo se consulta; este servicio no escribe saldos, usuarios ni movimientos.
- Docker Compose incluye MongoDB, el servicio `chatbot` y el servicio `tests`.
- La imagen de ejecución instala sólo dependencias de producción; la etapa `test` agrega pytest y ruff.

## Ejecutar con Docker

Compose levanta el chatbot en [modo news](#modo-news) con `stub`, por lo que permite validar el
flujo sin clave ni costo. Necesita la base de noticias inicializada:

```bash
cd /ruta/a/ai-assisted-news-app
make env-local
make db-init && make db-seed-catalog && make db-seed-demo
docker compose up --build
```

- API: `http://localhost:8010`
- Swagger: `http://localhost:8010/docs`
- Salud: `GET http://localhost:8010/health`

Prueba manual con las noticias demo:

```bash
curl -X POST http://localhost:8010/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Ultimas noticias","user":{"id":"guest:demo","displayName":"Demo"}}'
```

Ejecutar la suite dentro del mismo Compose, incluyendo un smoke test HTTP contra el contenedor:

```bash
make chatbot-test
```

Limpiar los servicios y el volumen demo:

```bash
docker compose down -v
```

Para usar OpenAI, guardar la key en `keys/openai_api_key` (nunca en `.env`) y definir en el
`.env` de la raíz:

```dotenv
CHATBOT_PROVIDER=openai
NEWS_CHAT_INPUT_USD_PER_MILLION=<precio de entrada del modelo>
NEWS_CHAT_OUTPUT_USD_PER_MILLION=<precio de salida del modelo>
```

No se debe agregar `.env` al repositorio.

## Editar el prompt

Modificá [`prompts/system.md`](prompts/system.md). Compose monta el directorio como volumen de sólo
lectura y el servicio carga el archivo en cada turno; no hace falta reconstruir la imagen. En otros
entornos, `CHATBOT_PROMPT_FILE` puede apuntar a otro archivo absoluto o relativo a esta carpeta.

Actualizá también `CHATBOT_PROMPT_VERSION` cuando el cambio sea relevante para trazabilidad.

## API HTTP

```json
POST /chat
{
  "message": "Resumime mis preferencias",
  "user_id": "demo-user",
  "previous_response_id": null
}
```

`user_id` es opcional. Si se omite, el chatbot responde sin contexto de Mongo. En una integración de
producción el frontend no debe decidir libremente ese valor: la API principal debe obtenerlo de la
sesión autenticada y llamar a este servicio por una red privada o con autenticación entre servicios.

`previous_response_id` conserva el comportamiento del chatbot copiado. OpenAI necesita almacenar la
respuesta para poder encadenarla. Si la política de datos exige `store=false`, la alternativa es
persistir el historial propio en Mongo y enviarlo en cada turno, como hacía el backend integrado de
NOVU.

## Modo news

Es el modo que usa la aplicación de noticias (`MONGODB_CONTEXT_MODE=news`, activado en el
`docker-compose.yml` de la raíz). En este modo `/chat` cambia de contrato y cumple
`docs/design/database/04-criterios-de-chat-y-costos.md`:

```json
POST /chat
{
  "message": "Resume las noticias de Guatemala",
  "sessionId": null,
  "newsId": null,
  "locationId": null,
  "user": { "id": "guest:<uuid>", "displayName": "Invitado", "email": "" }
}
```

- Lee únicamente noticias `published` de la base `ai_assisted_news`, con la misma configuración
  que `backend/news` (`NEWS_DB_MODE`, `NEWS_MONGODB_*`; en Atlas la URI sale de
  `keys/mongodb_uri`). Reutiliza los modelos de `backend/news/models` para escribir documentos
  válidos según los validators.
- La conversación se guarda embebida en `chatSessions` con `expiresAt = createdAt + 3600 s`; el
  historial se envía al modelo en cada turno con `store=false`, en lugar de `previous_response_id`.
- La intención (`recent_news`, `regional_news`, `topic_news`, `news_detail`, `summarize`,
  `explain`, `unsupported`) se clasifica con reglas, sin IA (`news_chat/intent.py`).
- Con `CHATBOT_PROVIDER=openai` responde con el modelo (`strategy = "llm"`) usando las noticias
  como contexto autorizado y registra cada llamada en `aiUsage`. Requiere `keys/openai_api_key`,
  `NEWS_CHAT_INPUT_USD_PER_MILLION` y `NEWS_CHAT_OUTPUT_USD_PER_MILLION`.
- Con `stub`, sin presupuesto (`NEWS_AI_BUDGET_USD`, 20 por defecto) o si OpenAI falla, responde
  con los campos de las noticias (`strategy = "database_query"`) y no consume presupuesto.
  Peticiones fuera del dominio: `strategy = "template"`, sin IA.
- `confidence`: `low` si no hay noticias o alguna no está `confirmed`; `high` si todas están
  confirmadas y cada una tiene dos o más fuentes, o una `official`/`primary_source`; `medium`
  en el resto.
- `user.id` es un identificador provisional `<proveedor>:<id>` que se guarda en
  `users.firebaseUid` hasta que exista Firebase Authentication. **No está autenticado.**

Variables propias del modo: `CHAT_SESSION_TTL_SECONDS`, `NEWS_AI_BUDGET_USD`,
`NEWS_CHAT_INPUT_USD_PER_MILLION`, `NEWS_CHAT_OUTPUT_USD_PER_MILLION`,
`NEWS_CHAT_DEFAULT_LOCATION_CODE` y `OPENAI_API_KEY_FILE`. El prompt es `prompts/news.md`.

Los modos `projection` y `novu` se conservan sin cambios para el uso original del asistente.

## Ejecución local sin Docker

Desde `backend/`:

```bash
python3 -m venv assistant/.venv
source assistant/.venv/bin/activate
python -m pip install -r assistant/requirements-dev.txt
python -m uvicorn assistant.app:app --reload --port 8010
```

Terminal:

```bash
python -m assistant.cli
```

Pruebas:

```bash
python -m pytest assistant/tests
python -m ruff check assistant
```

## MongoDB

La configuración recomendada es una proyección de lectura segura:

```dotenv
MONGODB_URI=mongodb://localhost:27017/assistant
MONGODB_DATABASE=assistant
MONGODB_CONTEXT_MODE=projection
MONGODB_CONTEXT_COLLECTION=assistant_contexts
MONGODB_USER_ID_TYPE=string
```

Para conectar directamente el esquema financiero heredado:

```dotenv
MONGODB_CONTEXT_MODE=novu
MONGODB_USER_ID_TYPE=objectid
MONGODB_DATABASE=novu
```

La explicación de consultas, campos, esquema recomendado, índices y cambios de integración está en
[`docs/database.md`](docs/database.md).

## Estructura

```text
assistant/
├── app.py                   # FastAPI, dependencias y ciclo de vida
├── config.py                # variables de entorno
├── prompts.py               # carga del prompt externo
├── prompts/system.md        # prompt editable
├── prompts/news.md          # prompt del modo news
├── news_chat/               # modo news: intención, noticias, sesiones y aiUsage
├── providers/               # OpenAI y stub
├── repositories/            # MongoDB o contexto vacío
├── service.py               # orquestación del turno
├── tests/                   # unitarias y smoke test
└── Dockerfile
```

El `docker-compose.yml` está en la raíz del proyecto porque este directorio contiene únicamente el
servicio del asistente, no un backend completo.

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

El modo predeterminado de Compose usa `stub`, por lo que permite validar el flujo sin clave ni costo:

```bash
cd /ruta/a/ai-assisted-news-app
docker compose up --build
```

- API: `http://localhost:8010`
- Swagger: `http://localhost:8010/docs`
- Salud: `GET http://localhost:8010/health`

Prueba manual con el contexto demo sembrado en MongoDB:

```bash
curl -X POST http://localhost:8010/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"¿Qué sabés de mí?","user_id":"demo-user"}'
```

Ejecutar la suite dentro del mismo Compose, incluyendo un smoke test HTTP contra el contenedor:

```bash
docker compose --profile test up --build \
  --abort-on-container-exit --exit-code-from tests tests
```

Limpiar los servicios y el volumen demo:

```bash
docker compose down -v
```

Para usar OpenAI:

```bash
cp .env.example .env
# Editar .env y definir API_GPT
CHATBOT_PROVIDER=openai API_GPT='...' docker compose up --build
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
├── providers/               # OpenAI y stub
├── repositories/            # MongoDB o contexto vacío
├── service.py               # orquestación del turno
├── tests/                   # unitarias y smoke test
└── Dockerfile
```

El `docker-compose.yml` está en la raíz del proyecto porque este directorio contiene únicamente el
servicio del asistente, no un backend completo.

# News Chat Integration — Result

## 1. Objetivo

Conectar el chatbot existente del equipo (`backend/assistant`) a la aplicación de noticias para
que lea las noticias de `ai_assisted_news`, con pantalla en el frontend, cumpliendo
`docs/design/database/04-criterios-de-chat-y-costos.md`.

Decisiones humanas (2026-10-11):

- Se usa el servicio `backend/assistant` (puerto 8010), no un chat aparte.
- Se elimina el módulo `backend/news/chat` creado en un primer intento.
- Alcance: backend y pantalla de chat en el frontend Expo.
- Diseño completo: `chatSessions` con TTL de 3600 s, `aiUsage` por cada llamada real a IA,
  `citedNewsIds` y `confidence`.

Esto modifica `backend/assistant`, lo que `AGENTS.md` prohibía; `AGENTS.md` se actualizó para
reflejar la decisión.

## 2. Cambios realizados

`backend/assistant/`:

- `config.py`: nuevo `MONGODB_CONTEXT_MODE=news` y variables del chat. La API key se lee de
  `keys/openai_api_key` (`OPENAI_API_KEY_FILE`) si `API_GPT` no está definida.
- `providers/`: historial propio (`history`, con `store=false`) y tokens de uso en
  `ProviderResponse`. Sin cambios de comportamiento para los modos existentes.
- `news_chat/`: `intent.py` (clasificación determinista), `retrieval.py` (noticias `published`,
  filtros y confianza), `service.py` (usuarios, sesiones, IA, presupuesto y `aiUsage`),
  `schemas.py` y `database.py` (conexión con la configuración de `backend/news`).
- `app.py`: en modo news, `/chat` usa el contrato de noticias. También corrige un fallo previo:
  sin `API_GPT`, un mensaje vacío devolvía 503 en lugar de 422.
- `prompts/news.md`, `Dockerfile` (contexto `backend/`, copia `news/`),
  `Dockerfile.dockerignore`, tests y documentación.

Resto del repositorio:

- `docker-compose.yml`: `chatbot` en modo news, conectado a `news-mongo` o Atlas; `tests` con el
  nuevo contexto de build; el frontend recibe `EXPO_PUBLIC_ASSISTANT_API_BASE_URL`.
- Frontend: `chatService.ts` (cliente de `POST :8010/chat`), `ChatScreen.tsx`, rutas
  `#/asistente` y botón "Preguntar al asistente"; cada invitado recibe un UUID propio.
- `Makefile`: `chatbot-up`, `chatbot-test`, `keys/openai_api_key` en `setup-keys` y variables del
  chat en `env-local`/`env-atlas`.
- `.env.example`, `frontend/.env.example`, `keys/README.md`, `AGENTS.md`, `README.md`,
  `backend/news/README.md`, `backend/assistant/README.md`, `backend/assistant/docs/database.md`.
- `backend/news/chat` se eliminó; `backend/news/api.py` queda como en `main`.

## 3. Decisiones tomadas

- Con `CHATBOT_PROVIDER=openai`, toda petición con noticias que la respalden se responde con el
  modelo (`llm`) y genera un registro en `aiUsage`. Sin noticias o fuera de dominio no se llama
  al modelo.
- Con `stub` (por defecto en Compose), sin presupuesto o si OpenAI falla: `database_query` con los
  campos de la noticia, sin costo.
- Presupuesto: antes de cada llamada se compara la suma de `estimatedCostUsd` más el peor caso de
  la llamada con `NEWS_AI_BUDGET_USD` (20).
- Los precios del modelo no se inventan: `NEWS_CHAT_INPUT_USD_PER_MILLION` y
  `NEWS_CHAT_OUTPUT_USD_PER_MILLION` son obligatorios con `openai` (503 explícito si faltan).
- El historial vive en `chatSessions` y se envía en cada turno (`store=false`), así la
  conversación expira con la sesión y no queda guardada en OpenAI.
- Un mensaje sin términos propios ("¿y eso?") se trata como seguimiento de lo último citado; uno
  con términos que no aparecen en ninguna noticia es `unsupported`.
- Se filtran en memoria las 200 noticias publicadas más recientes; no se crean índices nuevos.
- Los modos `projection` y `novu` del assistant se conservan.

## 4. Decisiones pendientes

1. **Identidad sin autenticar.** `users.firebaseUid` recibe un id provisional que envía el cliente
   (`guest:<uuid>`, `google:<id>`, `admin:<usuario>`). Cualquiera que conozca un id puede escribir
   como ese usuario. Reemplazar por el UID verificado de Firebase cuando se implemente.
2. **Precios y modelo** para habilitar `CHATBOT_PROVIDER=openai`.
3. **Volumen de noticias.** Si el scraper aumenta mucho el volumen, evaluar un índice de texto o
   filtros en la consulta (cambio en `08-indices-y-validacion.md`).
4. **Servicio `mongo` (base `assistant`)** sigue en Compose aunque el chatbot ya no lo usa en modo
   news. Decidir si se mueve a un perfil opcional.

## 5. Comandos ejecutados

```text
python -m pytest assistant/tests news/tests -q   (venv local: requirements-dev de ambos)
python -m ruff check assistant
npx tsc --noEmit
npx vitest run
uvicorn del assistant en modo news con datos demo en memoria + peticiones HTTP
npx expo start --web (compilación del bundle)
```

Docker no estaba disponible en el entorno: no se ejecutaron `make chatbot-test` ni el
`docker compose` real contra MongoDB. La UI no se probó visualmente en navegador ni dispositivo.

## 6. Tests y resultados

- Backend: 174 tests pasan (48 del assistant, incluidos los nuevos del modo news, y 126 de
  `backend/news`). El smoke test contra contenedor queda omitido sin Docker. `ruff` sin errores.
- Frontend: `tsc` sin errores; `vitest` 7 tests pasan.
- Servidor real (uvicorn) en modo news con catálogo y noticias demo en memoria: `/health` con
  `mongodb_connected: true`, CORS para `http://localhost:8081`, conversación de varios turnos
  con la misma sesión (regional, resumen, seguimiento, fuera de dominio, sin resultados) y 422
  para cuerpos inválidos.
- Expo web compila el bundle (2264 módulos) con la pantalla del asistente.

## 7. Bloqueos

Ninguno para `stub`. `openai` requiere `keys/openai_api_key` y los precios.

## 8. Commit

Cambios divididos en varios commits en la rama `feat/news-chat` (ver `git log`). Los dos
primeros commits de la rama agregaron `backend/news/chat`, que un commit posterior elimina.

## 9. Trazabilidad

```text
[x] modelos sincronizados        — sin cambios: el assistant usa ChatSession, AiUsage y User de backend/news
[x] documentación sincronizada   — AGENTS.md, READMEs, keys/README.md, assistant/docs/database.md
[x] diagrama sincronizado        — sin cambios estructurales: 07-diagrama.md no cambia
[x] tests sincronizados          — tests del modo news (assistant) y del cliente de chat (frontend)
[x] Makefile sincronizado        — chatbot-up, chatbot-test, setup-keys y variables de .env
[x] secrets/bootstrap sincronizados — keys/openai_api_key en setup-keys, keys/README.md y Compose
```

No cambian colecciones, campos, enums, índices, validators ni TTL.

## 10. Para el siguiente loop

- Probar: `make setup-keys`, `make env-local`, `make db-init`, `make db-seed-catalog`,
  `make db-seed-demo`, `docker compose up --build`, abrir `http://localhost:8081` y la pestaña
  "Asistente". `make chatbot-test` ejecuta la suite del assistant y el smoke test.
- Habilitar IA: completar `keys/openai_api_key` y definir en `.env` `CHATBOT_PROVIDER=openai`,
  `NEWS_CHAT_INPUT_USD_PER_MILLION` y `NEWS_CHAT_OUTPUT_USD_PER_MILLION`.
- El scraper solo necesita insertar noticias `published` válidas en `news`.

# feat: integrar MongoDB con el feed y agregar administracion de noticias

## Resumen

Este PR conecta la aplicacion de noticias con una base MongoDB independiente, incorpora la
inicializacion segura de su esquema fisico y agrega una API local para consultar y administrar
noticias.

El frontend deja de utilizar un dataset estatico en texto plano. El feed ahora obtiene sus datos
exclusivamente desde la API conectada a MongoDB y muestra un estado vacio o de error cuando la
base no contiene noticias o no esta disponible.

## Cambios principales

### MongoDB y configuracion

- Agrega soporte para MongoDB local mediante Docker y para MongoDB Atlas.
- Agrega `make env-local` y `make env-atlas` para generar el `.env` no secreto.
- Mantiene la URI de Atlas exclusivamente en `keys/mongodb_uri`; nunca se escribe en `.env`.
- Agrega `make setup-keys`, idempotente y sin sobrescritura de secretos existentes.
- Separa la base `ai_assisted_news` de la base y colecciones del assistant historico.
- Agrega comandos para inicializar, verificar y operar la base:
  - `make db-init`
  - `make db-schema-check`
  - `make db-check-config`
  - `make db-ping`
  - `make db-seed-catalog`
  - `make db-seed-demo`
  - `make news-db-up`
  - `make news-db-down`
  - `make news-api-up`

### Esquema de base de datos

- Materializa las siete colecciones aprobadas:
  - `locations`
  - `users`
  - `news`
  - `userInteractions`
  - `chatSessions`
  - `aiUsage`
  - `auditLogs`
- Agrega validators MongoDB `$jsonSchema` estrictos.
- Agrega indices unicos para `users.firebaseUid` y `news.slug`.
- Agrega el TTL de una hora para `chatSessions.expiresAt`.
- Agrega indices de consulta para feeds, interacciones, consumo de IA y auditoria.
- La inicializacion es idempotente y no elimina documentos, colecciones ni indices.
- Agrega deteccion de drift mediante `make db-schema-check`.
- Sincroniza modelos, tests, Makefile y documentacion de diseno.

### API de noticias

- Agrega un servicio FastAPI independiente en `backend/news/`.
- Expone los siguientes endpoints:
  - `GET /health`
  - `GET /news`
  - `GET /news/{slug}`
  - `GET /locations`
  - `POST /admin/login`
  - `POST /admin/news`
- Lee y escribe exclusivamente en `ai_assisted_news`.
- Agrega autenticacion local para las operaciones administrativas.
- Registra la creacion de noticias y su auditoria en MongoDB.
- No modifica ni reutiliza `backend/assistant/`.

### Frontend y administracion

- Conecta el feed con `news-api` mediante `EXPO_PUBLIC_NEWS_API_BASE_URL`.
- Agrega acceso administrativo desde la pantalla de login.
- Agrega la ruta `#/admin/nueva` y un formulario para crear noticias o borradores.
- Permite configurar categoria, ubicacion, verificacion, fuente e imagen.
- Restringe la seccion de creacion a sesiones con rol `admin`.
- Agrega estados de carga, exito, error y feed vacio.
- Mantiene busqueda, categorias, noticias relacionadas y guardados sobre datos recibidos de la API.

### Eliminacion del dataset estatico

- Elimina `frontend/src/data/demoArticles.ts`.
- Elimina `DEMO_ARTICLES`, `FEATURED_ARTICLE_ID`, `SECONDARY_ARTICLE_IDS` e `isDemo`.
- Elimina el fallback local: si la API falla, el frontend no muestra noticias embebidas.
- Conserva fixtures pequenos dentro de las pruebas unitarias solamente.
- `make db-seed-demo` sigue siendo opcional y persiste sus documentos en MongoDB; no funciona
  como dataset embebido ni como fallback del frontend.

## Flujo de configuracion

### MongoDB local

```bash
make env-local
make setup-keys
make db-init
make db-seed-catalog
docker compose up -d --build news-api frontend
```

Servicios locales:

```text
Frontend: http://localhost:8081
API:      http://localhost:8020
MongoDB:  localhost:27018
```

### MongoDB Atlas

```bash
make env-atlas
make setup-keys
# Completar manualmente keys/mongodb_uri
make db-check-config
make db-ping
make db-init
```

`make env-atlas` solo configura la ruta al archivo secreto. La URI nunca queda almacenada en el
`.env`.

## Verificacion realizada

```bash
npm run typecheck
npm test -- --run
make db-test
git diff --check
docker compose up -d --build news-api frontend
curl http://localhost:8020/health
curl http://localhost:8020/news
```

Resultados:

- TypeScript: correcto.
- Frontend: 3 pruebas aprobadas.
- Backend y base de datos: 126 pruebas aprobadas.
- `git diff --check`: sin errores.
- `news-api`: saludable y conectada a `ai_assisted_news` en modo local.
- `frontend`: responde correctamente en el puerto `8081`.
- La respuesta de `/news` no contiene el campo `isDemo`.

## Seguridad y operaciones

- No se incluyen valores secretos en el codigo, `.env`, tests ni documentacion.
- No se leyo ni imprimio el contenido de los archivos dentro de `keys/`.
- No se ejecutaron eliminaciones masivas, drops ni reseeds destructivos.
- Los documentos que ya existian en MongoDB se conservaron.
- Los tests normales no requieren credenciales reales de Atlas.
- La implementacion del chatbot de noticias permanece fuera del alcance de este PR.

## Checklist

- [x] Modelos y esquema MongoDB sincronizados.
- [x] Validators e indices sincronizados.
- [x] Diagrama y documentacion de base de datos actualizados.
- [x] Makefile y Docker Compose actualizados.
- [x] Bootstrap de secretos documentado y sincronizado.
- [x] Dataset estatico del frontend eliminado.
- [x] Tests frontend y backend aprobados.
- [x] Sin secretos incluidos en los cambios.
- [x] Sin operaciones destructivas sobre MongoDB.

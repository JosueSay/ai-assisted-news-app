# ai-assisted-news-app

## Ejecucion con Docker Compose

El Compose de la raiz levanta MongoDB, el servicio `chatbot` y el frontend Expo:

```bash
docker compose up --build
```

- Frontend Expo/Metro: `http://localhost:8081`
- Chatbot API: `http://localhost:8010`
- Swagger del chatbot: `http://localhost:8010/docs`
- MongoDB: `localhost:27017`

Si Expo Go no conecta desde el telefono por la red local, usa tunel:

```bash
EXPO_HOST=tunnel docker compose up --build
```

En modo `lan`, Docker puede mostrar un QR con la IP interna del contenedor. Para Expo Go en un
telefono fisico, tambien puedes anunciar la IP real de tu computadora:

```bash
REACT_NATIVE_PACKAGER_HOSTNAME=192.168.1.50 docker compose up --build frontend
```

## Backend assistant

El chatbot modularizado, su documentación de MongoDB, Dockerfile, Docker Compose y pruebas están en
[`backend/assistant`](backend/assistant/README.md).

El [`docker-compose.yml`](docker-compose.yml) de la raíz levanta MongoDB, el servicio `chatbot`, el
frontend Expo y, opcionalmente, el perfil de pruebas.

## Estructura de la plantilla

```text
ai-assisted-news-app/
├── backend/
│   ├── assistant/          # chatbot implementado y sus pruebas
│   ├── services/           # servicios backend futuros
│   └── tests/              # pruebas compartidas del backend
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   └── services/
│   └── tests/
├── docs/
│   ├── api/
│   ├── architecture/
│   ├── decisions/
│   └── testing/
├── tests/
│   ├── integration/
│   └── e2e/
└── docker-compose.yml
```

Las carpetas nuevas son únicamente estructura y documentación. Cada servicio futuro debe incluir su
propio `README.md` y un directorio `tests/` desde el inicio.

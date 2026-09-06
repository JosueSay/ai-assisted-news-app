# ai-assisted-news-app

## Backend assistant

El chatbot modularizado, su documentación de MongoDB, Dockerfile, Docker Compose y pruebas están en
[`backend/assistant`](backend/assistant/README.md).

El [`docker-compose.yml`](docker-compose.yml) de la raíz levanta MongoDB, el servicio `chatbot` y,
opcionalmente, el perfil de pruebas.

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

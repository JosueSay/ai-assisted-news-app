# ai-assisted-news-app

## Ejecutar noticias en desarrollo

Para una configuración local nueva (los comandos `env-*` reemplazan el `.env` raíz):

```bash
make env-local
make setup-keys
docker compose --profile tools build news-tools news-api chatbot frontend
make db-bootstrap
make db-verify
docker compose up -d --build news-api chatbot frontend
```

- Frontend Expo: `http://localhost:8081`
- API de noticias: `http://localhost:8020/docs`
- Chatbot de noticias: `http://localhost:8010/docs`
- MongoDB local de noticias: `localhost:27018`, base `ai_assisted_news`

`db-bootstrap` usa los seeders aprobados del PR #5: 16 países y 32 noticias
sintéticas (28 publicadas, 4 borradores). No modifica ni elimina documentos
existentes. `db-seed-demo` es un comando legacy independiente y no se necesita.

Para Atlas usa `make env-atlas` y completa manualmente `keys/mongodb_uri`.
Los modelos y el esquema son los mismos. Los datos demo son para desarrollo;
la API y el chat no ejecutan seeders al arrancar.

## Chat y contrato compartido

La pestaña Asistente consume `chatbot` en modo news y comparte los modelos,
catálogo y configuración de `backend/news/`. El prompt es
`backend/assistant/prompts/news.md`. `stub` responde con datos de la DB sin llamar
al modelo; OpenAI requiere el archivo de key y precios descritos en el README del
assistant. El acceso admin al chat utiliza el mismo token que la API.

```bash
make news-contract        # genera catálogo y tipos TypeScript desde Python
make news-contract-check  # detecta contratos desactualizados sin conectar a DB
```

Consulta [el contrato compartido](docs/architecture/contrato-compartido-noticias.md).
Los [siguientes pasos de arquitectura del chat](docs/architecture/chatbot-jev-code-llm-pendientes.md)
comparan el estado actual con el diagrama JEV + CODE + LLM y proponen seis loops de implementación.
Para un teléfono físico configura las dos URLs `EXPO_PUBLIC_*_API_BASE_URL` con la
IP LAN de tu computadora. El túnel de Expo solo publica Metro. Puedes anunciar la
IP de Metro con `REACT_NATIVE_PACKAGER_HOSTNAME=<IP LAN>` al iniciar Compose.

## Elegir el proveedor del chat

Después de `make env-local` o `make env-atlas`, selecciona el modo sin reemplazar
el resto del `.env`:

```bash
make chatbot-stub      # responde con datos y plantillas, sin API de IA
make chatbot-up        # aplica la selección al contenedor
```

Para OpenAI:

```bash
make chatbot-api       # alias: make chatbot-openai
make chatbot-up
```

El modo API requiere completar manualmente `keys/openai_api_key` y configurar
`NEWS_CHAT_INPUT_USD_PER_MILLION` y `NEWS_CHAT_OUTPUT_USD_PER_MILLION` con los precios
del modelo usado. Puedes definirlos en `.env` o pasarlos como argumentos a Make;
`OPENAI_MODEL` también puede pasarse de esa manera. Los valores proporcionados se
persisten en `.env`; nunca se copia allí la key ni se asignan tarifas por defecto.

El selector comprueba que el archivo de key exista y tenga tamaño mayor que cero,
sin leer su contenido. La aplicación valida la credencial al utilizar el proveedor.
Si faltan requisitos o los precios son inválidos, el selector falla sin cambiar
la configuración. No levanta servicios ni hace llamadas a IA automáticamente.
Funciona tanto con MongoDB local como con Atlas. `make env-local`/`env-atlas`
vuelven a generar el modo `stub`; selecciona el proveedor después de esos comandos.

`make chatbot-config-test` ejecuta las pruebas de configuración sin Docker ni secretos.

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

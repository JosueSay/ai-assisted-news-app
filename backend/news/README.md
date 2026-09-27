# Módulo de base de datos — AI Assisted News App

## Propósito

Infraestructura mínima, independiente y segura para conectar la aplicación de noticias a su
propia base de datos MongoDB Atlas.

**No** depende del asistente existente (`backend/assistant/`).
**No** es un servicio HTTP.
Los modelos representan el esquema lógico: este módulo no crea colecciones, índices ni datos en Atlas.

## Estructura

```text
backend/news/
├── __init__.py              # Docstring del módulo
├── config.py                # Configuración no secreta (NewsSettings)
├── secret_loader.py         # Carga segura de secretos desde archivos
├── database.py              # Conexión MongoDB (cliente, ping, cierre)
├── check_config.py          # Verificación de configuración (CLI)
├── ping.py                  # Prueba de conectividad (CLI)
├── models/
│   ├── __init__.py          # Enums compartidos
│   ├── reading_time.py      # Cálculo de tiempo de lectura
│   ├── location.py          # Catálogo de ubicaciones
│   ├── user.py              # Usuarios con onboarding e intereses
│   ├── news.py              # Noticias con verificación, fuentes, imagen
│   ├── user_interaction.py  # Registro de interacciones de lectura
│   ├── chat_session.py      # Sesiones temporales de chat
│   ├── ai_usage.py          # Consumo de IA y control de presupuesto
│   └── audit_log.py         # Auditoría de acciones administrativas
├── .env.example
├── README.md
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_secret_loader.py        # 8 tests
    ├── test_config.py               # 4 tests
    ├── test_database.py             # 6 tests
    ├── test_check_config.py         # 3 tests
    ├── test_reading_time.py         # 8 tests
    ├── test_location_model.py       # 5 tests
    ├── test_user_model.py           # 9 tests
    ├── test_news_model.py           # 20 tests
    ├── test_user_interaction_model.py  # 9 tests
    ├── test_chat_session_model.py   # 12 tests
    ├── test_ai_usage_model.py       # 9 tests
    └── test_audit_log_model.py      # 6 tests
```

## Siete colecciones

| Colección | Naturaleza | Estado actual |
| --- | --- | --- |
| `locations` | Catálogo precargado | Modelo implementado (Loop 02) |
| `users` | Persistente | Modelo implementado (Loop 02) |
| `news` | Persistente | Modelo implementado (Loop 02) |
| `userInteractions` | Persistente | Modelo implementado (Loop 02) |
| `chatSessions` | Temporal con TTL | Modelo implementado (Loop 02) |
| `aiUsage` | Persistente | Modelo implementado (Loop 02) |
| `auditLogs` | Persistente | Modelo implementado (Loop 02) |

Loop 02 implementa los modelos Python. Las colecciones se crearán físicamente en loops posteriores.

## Dependencias

- Python 3.10+
- PyMongo
- python-dotenv
- Pydantic

## Configuración

### 1. Preparar secretos

```bash
make setup-keys
```

Esto crea `keys/mongodb_uri`, `keys/client_id` y `keys/client_secret` si no existen.
Luego completar manualmente `keys/mongodb_uri` con la URI de Atlas.

Ver `keys/README.md` para más detalles.

### 2. Configurar variables de entorno

```bash
cp backend/news/.env.example backend/news/.env
```

Variables disponibles:

| Variable | Default | Descripción |
| --- | --- | --- |
| `NEWS_MONGODB_DATABASE` | `ai_assisted_news` | Nombre de la base de datos |
| `NEWS_MONGODB_URI_FILE` | `../../keys/mongodb_uri` | Ruta al archivo con la URI |
| `NEWS_MONGODB_REQUIRED` | `true` | Si es obligatoria para operar |
| `NEWS_MONGODB_TIMEOUT_MS` | `5000` | Timeout de conexión en ms |

## Comandos disponibles (Makefile)

```bash
make setup-keys        # Prepara archivos de secretos faltantes
make db-check-config   # Verifica configuración sin exponer secretos
make db-ping           # Prueba conectividad MongoDB (requiere credencial)
make db-test           # Ejecuta tests unitarios (no requiere Atlas)
```

## Separación respecto de assistant/

- `backend/news/` es independiente de `backend/assistant/`.
- La base de datos por defecto es `ai_assisted_news`, no `assistant`.
- No reutiliza modelos, repositorios ni configuración del asistente.
- No modifica `backend/assistant/` en absoluto.

## Seguridad

- `db-ping` nunca muestra la URI.
- `db-check-config` solo reporta `configured` / `missing` / `invalid`.
- `db-ping` no crea colecciones, no inserta ni modifica datos.

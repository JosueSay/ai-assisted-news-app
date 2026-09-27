# Módulo de base de datos — AI Assisted News App

## Propósito

Infraestructura mínima, independiente y segura para conectar la aplicación de noticias a su
propia base de datos MongoDB Atlas.

**No** depende del asistente existente (`backend/assistant/`).
**No** es un servicio HTTP.
**No** crea colecciones, índices ni datos.

## Estructura

```text
backend/news/
├── __init__.py         # Docstring del módulo
├── config.py           # Configuración no secreta (NewsSettings)
├── secret_loader.py    # Carga segura de secretos desde archivos
├── database.py         # Conexión MongoDB (cliente, ping, cierre)
├── check_config.py     # Verificación de configuración (CLI)
├── ping.py             # Prueba de conectividad (CLI)
├── .env.example        # Ejemplo de variables de entorno
├── README.md           # Este archivo
├── scripts/            # Scripts auxiliares (futuro)
└── tests/              # Tests unitarios
```

## Dependencias

- Python 3.10+
- PyMongo (se instalará junto con el proyecto)
- python-dotenv (para carga de `.env` en desarrollo local)

## Configuración

### 1. Crear la credencial MongoDB

La URI de Atlas **no** va en `.env`. Va en un archivo ignorado por Git:

```bash
echo 'mongodb+srv://usuario:contraseña@cluster.xxxxx.mongodb.net/' > keys/mongodb_uri
```

Ver `keys/README.md` para más detalles.

### 2. Configurar variables de entorno

Copiar y ajustar:

```bash
cp backend/news/.env.example backend/news/.env
```

Variables disponibles:

| Variable | Default | Descripción |
| --- | --- | --- |
| `NEWS_MONGODB_DATABASE` | `ai_assisted_news` | Nombre de la base de datos |
| `NEWS_MONGODB_URI_FILE` | `../../keys/mongodb_uri` (relativo a `backend/news/`) | Ruta al archivo con la URI |
| `NEWS_MONGODB_REQUIRED` | `true` | Si es obligatoria para operar |
| `NEWS_MONGODB_TIMEOUT_MS` | `5000` | Timeout de conexión en ms |

## Comandos disponibles (Makefile)

```bash
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
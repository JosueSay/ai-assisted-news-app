# Loop 01 — Database Foundation Result

## 1. Resultado

**Completed**

El loop se completó exitosamente. Se creó la infraestructura mínima, independiente y segura
para que AI Assisted News App pueda conectarse a su propia base de datos MongoDB Atlas.

## 2. Estructura creada

```
ai-assisted-news-app/
├── .gitignore                         # [modificado] Se agregó keys/* y !keys/README.md
├── Makefile                           # [nuevo] Targets: db-check-config, db-ping, db-test
├── keys/
│   ├── README.md                      # [nuevo] Documentación de secretos
│   └── mongodb_uri                    # [no versionado] Creado manualmente por el desarrollador
└── backend/news/
    ├── __init__.py                    # [nuevo] Módulo de infraestructura DB
    ├── config.py                      # [nuevo] NewsSettings, defaults, env loading
    ├── secret_loader.py               # [nuevo] Carga segura de secretos desde archivos
    ├── database.py                    # [nuevo] Conexión MongoDB, ping, cierre
    ├── check_config.py                # [nuevo] Verificación de configuración (CLI)
    ├── ping.py                        # [nuevo] Prueba de conectividad (CLI)
    ├── .env.example                   # [nuevo] Variables de entorno no secretas
    ├── README.md                      # [nuevo] Documentación del módulo
    └── tests/
        ├── __init__.py
        ├── conftest.py
        ├── test_secret_loader.py      # 8 tests
        ├── test_config.py             # 4 tests
        ├── test_database.py           # 6 tests
        └── test_check_config.py       # 3 tests
```

## 3. Configuración

| Variable | Default | Descripción |
| --- | --- | --- |
| `NEWS_MONGODB_DATABASE` | `ai_assisted_news` | Nombre de la base de datos |
| `NEWS_MONGODB_URI_FILE` | `../../keys/mongodb_uri` (relativo a `backend/news/`) | Ruta al archivo con la URI |
| `NEWS_MONGODB_REQUIRED` | `true` | Si la conexión es obligatoria |
| `NEWS_MONGODB_TIMEOUT_MS` | `5000` | Timeout de conexión en ms |

La URI se resuelve de forma absoluta desde `backend/news/`. Si la variable no está definida,
se usa la ruta relativa por defecto.

## 4. Secret Management

El mecanismo implementado:

1. Los secretos viven en `keys/` (ignorado por Git vía `.gitignore`).
2. `keys/mongodb_uri` debe ser creado manualmente con la URI de Atlas.
3. `secret_loader.load_secret()` lee el archivo, verifica existencia, tipo regular y contenido no vacío.
4. Nunca imprime, registra ni incluye el valor en excepciones.
5. `check_secret_file()` permite determinar el estado sin revelar el contenido: `configured` / `missing` / `invalid`.
6. `keys/README.md` documenta el formato esperado y las instrucciones.

```
secret values exposed: NO
```

## 5. MongoDB Connection

La conexión se implementa en `database.py`:

- `get_news_client(settings)`: Crea `MongoClient` con `appname="ai-assisted-news"`, timeout configurable, `uuidRepresentation="standard"`.
- `get_news_database(settings)`: Devuelve `client[settings.mongodb_database]`.
- `ping_database(settings)`: Ejecuta `ping` contra la base de datos, retorna estado sanitizado.
- `close_client(client)`: Cierra el cliente de forma segura.

Todas las funciones se probaron mediante mocks unitarios. No se ejecutó conexión Atlas real
porque no existe `keys/mongodb_uri` en el entorno.

## 6. Makefile

| Target | Comando | Descripción |
| --- | --- | --- |
| `db-check-config` | `python3 -c "from news.check_config import run_check; print(run_check())"` | Verifica configuración sin exponer secretos |
| `db-ping` | `python3 -c "from news.ping import run_ping; print(run_ping())"` | Prueba conectividad MongoDB (requiere credencial) |
| `db-test` | `python3 -m pytest backend/news/tests -v` | Ejecuta tests unitarios de infraestructura DB |

## 7. Tests

### Comando ejecutado

```bash
make db-test
```

Equivalente a:

```bash
python3 -m pytest backend/news/tests -v
```

### Resultado

**21 passed** en 0.11s. Ningún test requiere MongoDB Atlas.

| Archivo | Tests | Lo que prueba |
| --- | --- | --- |
| `test_secret_loader.py` | 8 | Carga exitosa, archivo faltante, vacío, whitespace, secreto no expuesto en error, estados de check |
| `test_config.py` | 4 | Defaults, overrides vía env, nombre DB, mongodb_configured sin archivo |
| `test_database.py` | 6 | Creación de cliente con args correctos, selección de DB, ping exitoso, fallo, error sanitizado, cierre |
| `test_check_config.py` | 3 | Output contiene "configured", "missing", nombre DB |

## 8. Security Verification

| Verificación | Resultado |
| --- | --- |
| `keys/mongodb_uri` tracked | NO |
| `keys/` en `.gitignore` | SÍ (regla `keys/*` + excepción `!keys/README.md`) |
| MongoDB URI en archivos versionados | NO (solo placeholders de ejemplo en docs) |
| Secretos en tests | NO |
| `backend/assistant/` modificado | NO (0 líneas) |
| Colecciones creadas | NO |
| Operaciones destructivas | NO |
| `backend/assistant/` diff | 0 líneas |

## 9. Files Changed

### New files (16)

```
Makefile
backend/news/__init__.py
backend/news/.env.example
backend/news/README.md
backend/news/check_config.py
backend/news/config.py
backend/news/database.py
backend/news/ping.py
backend/news/secret_loader.py
backend/news/tests/__init__.py
backend/news/tests/conftest.py
backend/news/tests/test_check_config.py
backend/news/tests/test_config.py
backend/news/tests/test_database.py
backend/news/tests/test_secret_loader.py
keys/README.md
```

### Modified files (1)

```
.gitignore   — agregada sección Secrets con keys/* y !keys/README.md
```

## 10. Decisions

| Decisión | Justificación |
| --- | --- |
| Módulo `backend/news/` en vez de `backend/services/news/` | No es un servicio HTTP. Sigue la misma convención que `backend/assistant/` para módulos autónomos. |
| Ruta relativa por defecto `../../keys/mongodb_uri` | Se resuelve desde `backend/news/` hacia `keys/` en la raíz del proyecto. |
| `keys/*` en `.gitignore` con excepción para `README.md` | Permite conservar la documentación del directorio en el repo sin versionar secretos. |
| No se agregó `.gitkeep` en `keys/` | No es necesario porque `keys/README.md` ya preserva el directorio en Git. |
| `mongodb_uri` como nombre de archivo | Simple, sin extensión, coincide con el nombre de la variable de entorno. |
| `NewsSettings` como dataclass frozen con `@lru_cache` | Sigue el patrón de `assistant/config.py`. |
| `check_secret_file` devuelve string en vez de enum | Evita dependencias adicionales; suficientemente expresivo para sus tres estados. |

## 11. Blockers

Ninguno. El loop no requiere credenciales para completarse.

## 12. Git

| Aspecto | Valor |
| --- | --- |
| Commit | `73ba501` |
| Mensaje | `feat: add news database foundation` |
| Branch | `feat/design-db` |
| Estado post-commit | Working tree sucio por `backend/loops/01-db-foundation.md` y `backend/prompts/01-db-foundation.md` (modificaciones preexistentes no incluidas en el commit) |

## 13. Information for Loop 02

Loop 02 (catálogo `locations`) debe:

1. Crear un modelo Python `Location` en `backend/news/models/location.py`.
2. Crear un repositorio `LocationRepository` que use `get_news_database()`.
3. Crear un seeder con los países listados en `AGENTS.md`.
4. Agregar al Makefile targets para seed si aplica.
5. Agregar tests para el modelo, repositorio y seeder.

La conexión MongoDB está disponible mediante:

```python
from news.config import get_news_settings
from news.database import get_news_database

settings = get_news_settings()
db = get_news_database(settings)
```

La colección `locations` debe crearse en la base de datos configurada (`ai_assisted_news` por defecto),
no en `assistant`. Usar PyMongo directamente, sin ODM.

Los tests deben usar mocks/fakes y no requerir Atlas real.
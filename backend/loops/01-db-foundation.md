# Loop 01 — Database Foundation

## Objetivo

Crear la infraestructura mínima, independiente y segura para que AI Assisted News App pueda conectarse posteriormente a su propia base de datos MongoDB Atlas.

Este loop prepara:

- estructura del módulo de database;
- configuración no secreta;
- mecanismo de lectura de secretos desde `keys/`;
- conexión MongoDB;
- verificación segura de configuración;
- pruebas unitarias;
- Makefile inicial;
- documentación.

Este loop **NO crea todavía las colecciones del diseño**.

---

## Lecturas obligatorias

Antes de modificar código leer:

```text
AGENTS.md
backend/loops/handoffs/00-discovery-result.md
docs/design/database/README.md
docs/design/database/01-colecciones.md
```

`AGENTS.md` contiene las reglas globales y prevalece sobre decisiones técnicas no especificadas en este loop.

---

## Decisiones ya tomadas

No volver a consultar estas decisiones:

### Separación

La DB pertenece exclusivamente a AI Assisted News App.

No:

- reutilizar la DB `assistant`;
- modificar `backend/assistant/`;
- reutilizar NOVU;
- integrar el chatbot financiero existente.

### Tecnología

Usar:

```text
Python
PyMongo
MongoDB Atlas
```

No introducir ODM.

### Database

Nombre parametrizable.

Default recomendado:

```text
ai_assisted_news
```

### Secretos

Los secretos viven exclusivamente en:

```text
keys/
```

`.env` puede contener rutas hacia archivos dentro de `keys/`, pero nunca valores secretos.

### Firebase

`firebaseUid` será utilizado posteriormente por el modelo `users`.

No integrar Firebase Authentication en este loop.

### Chat

Las sesiones tendrán posteriormente TTL de 3600 segundos.

No implementar chat en este loop.

---

# Fase 1 — Determinar ubicación del módulo

Respetar las convenciones encontradas en el repositorio.

Crear infraestructura específica para la DB de noticias sin colocarla dentro de:

```text
backend/assistant/
```

Preferir una estructura independiente bajo `backend/`.

Antes de crearla, verificar las convenciones existentes en:

```text
backend/README.md
backend/services/README.md
```

No crear un servicio HTTP.

El resultado de este loop debe ser infraestructura reutilizable por loops posteriores.

---

# Fase 2 — Estructura de `keys/`

Crear la estructura mínima necesaria para documentar secretos.

`keys/` debe estar ignorado correctamente por Git.

No crear archivos que contengan secretos reales.

Debe existir documentación que indique:

- qué credencial necesita MongoDB;
- qué archivo debe crear manualmente el desarrollador;
- formato esperado;
- que el archivo nunca debe versionarse.

Preferir una convención simple, por ejemplo:

```text
keys/
└── README.md
```

y un archivo esperado localmente como:

```text
keys/mongodb_uri
```

`mongodb_uri` debe estar ignorado.

No crear una URI falsa que pueda confundirse con una credencial válida.

Si se necesita conservar el directorio mediante Git, utilizar `.gitkeep` únicamente cuando sea técnicamente necesario.

---

# Fase 3 — Configuración

Crear configuración específica para la DB de noticias.

La parametrización debe soportar como mínimo:

```text
NEWS_MONGODB_DATABASE
NEWS_MONGODB_URI_FILE
NEWS_MONGODB_REQUIRED
NEWS_MONGODB_TIMEOUT_MS
```

Defaults:

```text
NEWS_MONGODB_DATABASE=ai_assisted_news
NEWS_MONGODB_URI_FILE=<ruta hacia keys/mongodb_uri>
NEWS_MONGODB_REQUIRED=true
NEWS_MONGODB_TIMEOUT_MS=5000
```

La ruta debe resolverse de manera consistente independientemente del working directory cuando sea razonablemente posible.

No guardar `MONGODB_URI` directamente como variable de entorno.

---

# Fase 4 — Secret loader

Implementar una utilidad mínima responsable de cargar secretos desde archivos.

Debe:

1. recibir una ruta;
2. verificar existencia;
3. verificar que sea archivo regular;
4. leer el secreto únicamente dentro del proceso que necesita utilizarlo;
5. eliminar whitespace exterior;
6. rechazar archivo vacío;
7. nunca imprimir el valor;
8. nunca incluir el valor en excepciones;
9. nunca incluirlo en `repr`;
10. producir errores seguros y comprensibles.

No crear un sistema genérico complejo de gestión de secretos.

---

# Fase 5 — Conexión MongoDB

Implementar una abstracción mínima para obtener un cliente/database de MongoDB para AI Assisted News App.

Debe:

- utilizar PyMongo;
- utilizar el URI cargado desde el archivo configurado;
- seleccionar `NEWS_MONGODB_DATABASE`;
- utilizar timeout configurable;
- permanecer completamente separada de `assistant/`;
- permitir cerrar el cliente correctamente.

No:

- crear colecciones;
- crear índices;
- ejecutar seeds;
- borrar datos;
- modificar datos;
- implementar repositories.

---

# Fase 6 — Comprobación de configuración

Crear una comprobación segura que permita determinar:

```text
MongoDB credential file: configured / missing
```

Puede comprobar:

- existencia;
- tipo de archivo;
- vacío/no vacío mediante una función encapsulada.

El agente no debe inspeccionar ni recibir el contenido.

Nunca mostrar:

- URI;
- username;
- password;
- host completo si forma parte del secreto;
- query parameters del URI.

Si falta la credencial, devolver instrucciones para que el humano cree:

```text
keys/mongodb_uri
```

---

# Fase 7 — Prueba de conexión

Crear un comando explícito que permita al humano probar posteriormente la conexión.

La prueba debe utilizar:

```text
ping
```

de MongoDB.

Debe reportar únicamente algo equivalente a:

```text
MongoDB connection: OK
Database: ai_assisted_news
```

o un error sanitizado.

Nunca mostrar la URI.

La prueba de conexión:

- no crea colecciones;
- no inserta datos;
- no elimina datos.

Si las credenciales no están disponibles durante el loop, no considerar esto fallo del loop.

Debe poder verificarse mediante mocks/unit tests.

---

# Fase 8 — Makefile inicial

Crear un `Makefile` en la ubicación coherente con el repositorio.

Como mínimo debe ofrecer comandos equivalentes a:

```text
make db-check-config
make db-ping
make db-test
```

Semántica:

### `db-check-config`

Comprueba configuración y presencia de credenciales sin mostrar secretos.

### `db-ping`

Prueba conectividad con MongoDB mediante `ping`.

No modifica datos.

### `db-test`

Ejecuta únicamente los tests correspondientes a infraestructura DB.

No debe requerir Atlas real.

Los nombres pueden ajustarse únicamente si existe una convención fuerte en el repositorio; documentar cualquier cambio.

---

# Fase 9 — Tests

Crear pruebas unitarias para al menos:

### Secret loader

- archivo existente;
- archivo inexistente;
- archivo vacío;
- whitespace;
- excepción no contiene secreto.

### Config

- defaults;
- overrides;
- resolución de ruta;
- database name.

### MongoDB

Mediante mocks/fakes:

- cliente recibe configuración esperada;
- database correcta es seleccionada;
- timeout aplicado;
- `ping` correcto;
- fallo de `ping` produce error sanitizado;
- cierre del cliente.

Los tests normales NO deben conectarse a Atlas.

---

# Fase 10 — Documentación

Documentar:

- propósito del módulo DB;
- cómo instalar dependencias si aplica;
- dónde crear `keys/mongodb_uri`;
- cómo configurar `.env`;
- cómo ejecutar `make db-check-config`;
- cómo ejecutar `make db-ping`;
- cómo ejecutar `make db-test`;
- separación respecto de `assistant/`;
- que `db-ping` no modifica datos.

Actualizar `.env.example` o crear uno específico para este módulo si la arquitectura lo requiere.

Nunca incluir secretos reales.

---

# Fase 11 — Verificación de seguridad

Antes del commit comprobar:

```bash
git status
git diff
git diff --cached
```

Verificar explícitamente que:

- `keys/mongodb_uri` no esté tracked;
- ninguna URI MongoDB aparezca en archivos versionados;
- ningún secreto aparezca en tests;
- `backend/assistant/` permanezca sin cambios;
- no se hayan creado colecciones;
- no se hayan realizado operaciones destructivas.

---

# Commit

Si todas las verificaciones pasan, crear un único commit:

```text
feat: add news database foundation
```

No hacer push.

---

# Entregable

Crear:

```text
backend/loops/handoffs/01-db-foundation-result.md
```

Debe incluir:

## 1. Resultado

Completed / Blocked / Partial.

## 2. Estructura creada

Árbol de archivos relevante.

## 3. Configuración

Variables y defaults implementados.

No incluir secretos.

## 4. Secret Management

Explicar el mecanismo implementado.

Confirmar explícitamente:

```text
secret values exposed: NO
```

## 5. MongoDB Connection

Explicar implementación y resultado de las pruebas.

Diferenciar:

- unit tests;
- conexión Atlas real, si fue ejecutada manualmente.

## 6. Makefile

Targets disponibles.

## 7. Tests

Comandos y resultados exactos.

## 8. Security Verification

Confirmar:

- secrets tracked: NO;
- MongoDB URI exposed: NO;
- assistant modified: NO;
- destructive DB operations: NO.

## 9. Files Changed

Listado.

## 10. Decisions

Cualquier decisión técnica menor tomada.

## 11. Blockers

Solo bloqueos reales.

## 12. Git

Commit creado y estado final.

## 13. Information for Loop 02

Información necesaria para implementar los modelos.

---

# Definition of Done

El loop termina cuando:

- existe infraestructura DB independiente para noticias;
- existe configuración no secreta;
- secretos se cargan desde archivos;
- `keys/` está protegido contra commits accidentales;
- existe conexión PyMongo reutilizable;
- existe `ping` no destructivo;
- existen tests unitarios;
- tests no requieren Atlas;
- existe Makefile inicial;
- existe documentación;
- `assistant/` no fue modificado;
- ninguna colección fue creada;
- ningún dato fue insertado;
- ningún secreto fue expuesto;
- se creó el handoff;
- verificaciones pasan;
- se creó el commit.

---

# Stop Conditions

Detener y documentar si:

- es necesario modificar `assistant/`;
- una decisión contradice `docs/design/database/`;
- es necesario mostrar un secreto;
- una prueba requiere destruir/modificar datos;
- aparece una dependencia arquitectónica nueva no aprobada;
- la estructura actual del repo hace imposible crear infraestructura independiente sin una decisión humana.

La ausencia de `keys/mongodb_uri` NO bloquea los tests unitarios ni la finalización del loop.

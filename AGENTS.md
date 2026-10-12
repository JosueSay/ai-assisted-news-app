# AGENTS.md — AI Assisted News App

## Propósito

Este repositorio contiene varios componentes y código histórico.

El trabajo de los loops de ingeniería de base de datos corresponde exclusivamente a **AI Assisted News App**.

No asumir que código existente pertenece a la aplicación de noticias.

---

## Fuente de verdad

Para decisiones relacionadas con base de datos, consultar primero:

```text
docs/design/database/
```

Los documentos dentro de esa carpeta representan el diseño aprobado.

El archivo:

```text
docs/design/99-checklist-replicacion.md
```

no es una especificación autoritativa y no debe utilizarse como fuente de verdad.

Los handoffs anteriores se encuentran en:

```text
backend/loops/handoffs/
```

Antes de ejecutar un loop, leer su handoff anterior cuando exista.

---

## Alcance actual

El trabajo actual está limitado a infraestructura y diseño de base de datos para la aplicación de noticias.

Está permitido trabajar en:

- modelos Python;
- MongoDB;
- MongoDB Atlas;
- PyMongo;
- validaciones;
- índices;
- catálogos;
- seeders;
- generadores de datos;
- scripts de inicialización;
- scripts de reseed;
- Makefile;
- tests de DB;
- documentación relacionada con DB.

No implementar salvo que un loop futuro lo autorice explícitamente:

- endpoints;
- routers;
- frontend;
- integración de UI;
- Firebase Authentication;
- lógica completa del chatbot;
- NOVU;
- servicios financieros;
- features ajenas a DB.

Excepción autorizada por decisión humana (2026-10-11): ya existen y pueden mantenerse la API
local de noticias (`backend/news/api.py`), el frontend que la consume y el chat de noticias del
assistant en modo news (`backend/assistant/news_chat/`) con su pantalla. Ver
`backend/loops/handoffs/news-chat-integration-result.md`.

---

## Separación del assistant existente

`backend/assistant/` es el chatbot del equipo. Por decisión humana (2026-10-11) es también el
chatbot de la aplicación de noticias mediante el **modo news** (`MONGODB_CONTEXT_MODE=news`,
código en `backend/assistant/news_chat/`).

En modo news:

- lee y escribe únicamente la base `ai_assisted_news`;
- reutiliza los modelos y la configuración de `backend/news` para cumplir `docs/design/database/`;
- lee la API key desde `keys/openai_api_key`.

No:

- reutilizar su base de datos `assistant` ni sus colecciones para noticias;
- reutilizar NOVU ni sus servicios financieros para noticias;
- romper los modos `projection` y `novu`, que se conservan para el uso original.

La aplicación de noticias debe tener infraestructura MongoDB independiente.

---

## MongoDB

Tecnología estándar para este trabajo:

```text
MongoDB Atlas
PyMongo
Python
```

No introducir un ODM sin una decisión humana explícita.

La base de datos de noticias debe ser independiente de la base `assistant`.

---

## Secretos

Todos los secretos deben almacenarse bajo:

```text
keys/
```

Los agentes tienen prohibido leer, imprimir, copiar, registrar o modificar el contenido de archivos secretos dentro de `keys/`.

Pueden:

- comprobar que `keys/` existe;
- comprobar que un archivo requerido existe;
- comprobar de forma segura si falta un archivo requerido;
- documentar qué archivo debe crear el usuario.

No mostrar valores secretos en logs, tests, handoffs ni commits.

---

## `.env`

`.env` y `.env.example` se utilizan exclusivamente para **parametrización no secreta**.

Pueden contener, por ejemplo:

```text
NEWS_MONGODB_DATABASE=ai_assisted_news
NEWS_MONGODB_KEY_FILE=../../keys/mongodb_uri
CHAT_SESSION_TTL_SECONDS=3600
```

La ruta hacia un archivo secreto puede estar en `.env`.

El valor secreto no puede estar en `.env`.

Nunca colocar directamente:

```text
mongodb+srv://...
password
client_secret
API keys
tokens
```

en `.env`, `.env.example` o código fuente.

---

## Operaciones destructivas

Nunca ejecutar automáticamente:

- drop database;
- drop collection;
- reseed destructivo;
- eliminación masiva;
- limpieza de Atlas.

Una operación destructiva debe:

1. indicar exactamente qué destruirá;
2. requerir confirmación humana explícita;
3. detenerse si no existe confirmación;
4. evitar valores predeterminados peligrosos.

Los tests automatizados no deben destruir datos reales de Atlas.

---

## Seeders

Seedear únicamente datos controlados que formen parte del catálogo o desarrollo.

Inicialmente:

- locations;
- topics;
- noticias de desarrollo/demo cuando el loop correspondiente lo permita.

No seedear:

- users reales;
- userInteractions reales;
- chatSessions reales;
- aiUsage real;
- auditLogs reales.

Los seeders deben ser reproducibles.

---

## Locations

El catálogo inicial debe cubrir:

### América

- Canadá
- México
- Guatemala
- Costa Rica
- Argentina
- Brasil
- Cuba
- Jamaica

### Europa

- España
- Francia

### Asia

- Japón
- China

### África

- Egipto
- Sudáfrica

### Oceanía

- Australia
- Nueva Zelanda

Las ubicaciones deben representar lugares reales.

No utilizar GPS para seleccionar la ubicación del usuario.

La aplicación utiliza ubicación simulada seleccionada manualmente.

---

## Usuarios

`firebaseUid` será el identificador externo proveniente de Firebase Authentication.

Los modelos pueden prepararse para almacenarlo.

No implementar Firebase Authentication durante los loops de DB salvo instrucción explícita posterior.

---

## Chat

El chat de noticias es el assistant en modo news (ver "Separación del assistant existente").
Es independiente de NOVU y de la base `assistant`.

Las sesiones de chat tendrán una vigencia de:

```text
3600 segundos
```

equivalente a una hora.

El chatbot debe cumplir `docs/design/database/04-criterios-de-chat-y-costos.md`: mensajes en
`chatSessions`, cada llamada real a IA registrada en `aiUsage` y solo noticias `published`
citadas.

---

## Presupuesto IA

El presupuesto funcional definido para la aplicación es USD 20.

La colección `aiUsage` debe permitir registrar consumo cuando corresponda.

Los loops de ingeniería ejecutados mediante OpenCode no forman parte del gasto de producción de la aplicación.

Si se lleva telemetría del trabajo de los agentes, debe mantenerse separada de `aiUsage`.

No inventar costos ni tokens cuando la herramienta no proporcione esos datos.

---

## Modelos

Los modelos Python deben reflejar el diseño aprobado en:

```text
docs/design/database/
```

No agregar campos, estados, features o abstracciones "por si acaso".

Si aparece una necesidad no contemplada:

1. documentarla;
2. detener la decisión correspondiente;
3. solicitar decisión humana.

Preferir la solución mínima que satisfaga el diseño.

---

## Testing

Cada loop que implemente comportamiento debe incluir pruebas apropiadas.

Priorizar:

- unit tests sin credenciales;
- tests deterministas;
- tests de validación;
- tests de índices;
- tests de seeders.

Los tests que requieran Atlas deben estar claramente separados de los tests unitarios.

Nunca hacer que el test suite normal dependa obligatoriamente de credenciales reales.

---

## Automatización

La interfaz principal para tareas repetibles será un:

```text
Makefile
```

Los comandos deben ser pequeños, explícitos y seguros.

Cuando una tarea requiera secretos, el comando debe validar primero que la configuración requerida existe sin revelar su contenido.

---

## Git

Cada loop implementable debe producir cambios pequeños y verificables.

Antes de realizar un commit:

1. ejecutar las verificaciones definidas por el loop;
2. comprobar `git diff`;
3. comprobar que ningún secreto esté staged;
4. comprobar que los tests relevantes pasen.

Usar Conventional Commits siguiendo el estilo existente del repositorio.

No hacer push automáticamente.

No modificar historia Git.

---

## Handoffs

Cada loop debe generar:

```text
backend/loops/handoffs/<loop>-result.md
```

El handoff debe incluir:

- objetivo;
- cambios realizados;
- archivos creados/modificados;
- decisiones tomadas;
- decisiones pendientes;
- comandos ejecutados;
- tests ejecutados;
- resultados;
- bloqueos;
- commit creado, si aplica;
- estado final del working tree;
- información necesaria para el siguiente loop.

No incluir secretos.

---

## Regla de parada

Detenerse y solicitar decisión humana cuando:

- una decisión contradiga `docs/design/database/`;
- sea necesario acceder al contenido de `keys/`;
- aparezca una operación destructiva no autorizada;
- sea necesario ampliar el alcance;
- sea necesario introducir una nueva dependencia arquitectónica importante;
- exista riesgo de exponer secretos;
- no pueda verificarse de forma segura el resultado.

No resolver silenciosamente estas situaciones.

## Bootstrap para nuevos desarrolladores

El repositorio debe mantener un comando de Makefile que prepare los archivos locales requeridos por un nuevo desarrollador.

El comando estándar será:

```text
make setup-keys
```

Debe:

- crear `keys/` si no existe;
- crear únicamente los archivos de secretos requeridos que falten;
- crear los archivos vacíos;
- nunca sobrescribir archivos existentes;
- nunca escribir valores secretos;
- indicar qué archivos debe completar manualmente el desarrollador;
- ser idempotente: ejecutarlo varias veces no debe destruir ni reemplazar configuración existente.

Ejemplo:

```text
$ make setup-keys

keys/mongodb_uri       CREATED

Complete the required secret files and run:
make db-check-config
make db-ping
```

Si en el futuro se agrega, elimina o cambia un secreto requerido por el proyecto, el mismo cambio debe actualizar:

- `make setup-keys`;
- `keys/README.md`;
- configuración relacionada;
- documentación correspondiente.

La configuración de secretos debe mantenerse sincronizada.

---

## Trazabilidad del diseño de base de datos

Debe existir un documento versionado que represente visualmente la estructura vigente de MongoDB.

Ubicación estándar:

```text
docs/design/database/07-diagrama.md
```

Preferir Mermaid para que el diagrama permanezca como texto versionable dentro de Git.

El diagrama debe representar como mínimo:

- colecciones;
- referencias entre colecciones;
- documentos embebidos relevantes;
- cardinalidades conceptuales cuando sean útiles.

MongoDB no impone foreign keys; las relaciones mostradas representan referencias lógicas mediante ObjectId u otros identificadores.

El diagrama debe reflejar el diseño implementado y no características futuras.

---

## Sincronización de cambios de DB

Todo cambio estructural de base de datos debe mantener sincronizados:

```text
docs/design/database/
backend/news/
Makefile
tests
seeders
scripts
```

según cuáles sean afectados.

Si cambia:

- una colección;
- un campo;
- una referencia;
- un enum;
- un índice;
- una validación;
- un catálogo;
- una política TTL;
- una estrategia de seed;
- una credencial requerida;

el agente debe revisar si corresponde actualizar:

1. modelos Python;
2. validaciones MongoDB;
3. índices;
4. seeders;
5. tests;
6. Makefile;
7. README;
8. `docs/design/database/`;
9. `docs/design/database/07-diagrama.md`;
10. `keys/README.md`.

No considerar completa una modificación de DB cuando implementación y documentación queden desincronizadas.

---

## Regla de trazabilidad para loops

Antes de cerrar un loop relacionado con DB, verificar explícitamente:

```text
[ ] modelos sincronizados
[ ] documentación sincronizada
[ ] diagrama sincronizado
[ ] tests sincronizados
[ ] Makefile sincronizado si corresponde
[ ] secrets/bootstrap sincronizados si corresponde
```

El handoff debe indicar cuáles elementos fueron revisados y cuáles cambiaron.

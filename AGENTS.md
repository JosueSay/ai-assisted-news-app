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

---

## Separación del assistant existente

`backend/assistant/` corresponde a un asistente existente y NO representa la arquitectura de la aplicación de noticias.

No:

- modificarlo;
- reutilizar su base de datos `assistant`;
- reutilizar sus colecciones;
- reutilizar NOVU;
- adaptar silenciosamente código financiero para noticias.

La aplicación de noticias debe tener infraestructura MongoDB independiente.

Se puede observar código existente únicamente como referencia técnica cuando sea necesario.

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

El chat de noticias es independiente del assistant/NOVU existente.

Las sesiones de chat tendrán una vigencia de:

```text
3600 segundos
```

equivalente a una hora.

La implementación funcional del chatbot no forma parte del alcance actual.

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

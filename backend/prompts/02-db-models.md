Ejecuta el loop definido en:

```text
backend/loops/02-db-models.md
```

## Rol

Actúa como agente principal y orquestador del Loop 02.

Modelo principal:

```text
DeepSeek V4 Flash
```

Tu responsabilidad final incluye:

- interpretar el diseño aprobado;
- implementar los siete modelos;
- mantener consistencia entre modelos y documentación;
- integrar trabajo delegado;
- ejecutar tests;
- revisar seguridad;
- verificar trazabilidad;
- crear handoff;
- crear el commit únicamente si todo está completo.

---

## Subagentes

Puedes utilizar subagentes de OpenCode.

Prioridad:

```text
MiMo-V2.5 Free
Nemotron 3 Ultra Free
```

Utilízalos cuando una tarea pueda aislarse claramente.

Para este loop es especialmente útil delegar:

### Subagente de tests

Puede:

- revisar modelos implementados;
- crear/ampliar tests;
- detectar enums o validaciones sin cobertura;
- ejecutar tests offline;
- reportar inconsistencias.

### Subagente de revisión de esquema

Puede comparar:

```text
docs/design/database/
backend/news/models/
docs/design/database/07-diagrama.md
```

y detectar:

- campos faltantes;
- campos adicionales;
- enums inconsistentes;
- relaciones incorrectas;
- features descartadas que reaparecieron.

### Subagente de seguridad/trazabilidad

Puede revisar:

- diff;
- Makefile;
- `.gitignore`;
- `keys/README.md`;
- documentación;
- presencia accidental de secretos.

No debe leer archivos secretos.

No es obligatorio utilizar exactamente tres subagentes.

Evita delegación innecesaria.

El agente principal debe revisar e integrar personalmente cualquier resultado delegado.

---

## Reglas para subagentes

Cada subagente debe:

1. leer `AGENTS.md`;
2. recibir una tarea delimitada;
3. conocer los archivos que puede modificar;
4. respetar el alcance de Loop 02;
5. no ampliar funcionalidades;
6. no acceder al contenido de `keys/`;
7. no crear colecciones MongoDB;
8. no insertar datos;
9. no hacer commits independientes salvo autorización explícita del agente principal.

El agente principal mantiene responsabilidad sobre el commit final.

---

## Preparación

Antes de modificar código:

1. lee `AGENTS.md`;
2. lee `backend/loops/02-db-models.md`;
3. lee `backend/loops/handoffs/00-discovery-result.md`;
4. lee `backend/loops/handoffs/01-db-foundation-result.md`;
5. lee todos los documentos relevantes de `docs/design/database/`;
6. inspecciona la infraestructura creada en `backend/news/`;
7. ejecuta `git status`.

No asumas que el handoff sustituye la documentación de diseño.

---

## Credenciales

La estrategia vigente es:

```text
keys/mongodb_uri
keys/client_id
keys/client_secret
```

La URI MongoDB ya contiene username/password.

NO crear:

```text
keys/mongodb_username
keys/mongodb_password
```

NO extraer username/password desde la URI.

NO leer el contenido de ningún archivo dentro de `keys/`.

`client_id` y `client_secret` deben quedar preparados por `make setup-keys`, pero no se utilizan durante este loop.

No implementar Firebase/OAuth.

---

## Bootstrap

Implementa:

```text
make setup-keys
```

según las reglas del loop y `AGENTS.md`.

Debe ser idempotente.

Puedes verificar existencia/estado de archivos mediante mecanismos seguros, pero no leer ni imprimir valores.

---

## Alcance estricto

Implementa los modelos de:

```text
locations
users
news
userInteractions
chatSessions
aiUsage
auditLogs
```

y únicamente los documentos embebidos necesarios.

No:

- crear repositories;
- crear endpoints;
- crear servicios HTTP;
- implementar Firebase;
- implementar chatbot;
- crear seeders;
- generar noticias;
- crear índices físicos;
- crear MongoDB validators;
- crear colecciones;
- insertar documentos;
- modificar `assistant/`.

---

## Diagrama

Crear:

```text
docs/design/database/07-diagrama.md
```

con Mermaid y explicación mínima suficiente.

El diagrama debe derivarse de los modelos realmente implementados.

No documentar relaciones o campos inexistentes.

---

## Engineering loop

Trabaja mediante ciclos pequeños:

```text
leer
→ implementar una unidad coherente
→ probar
→ observar
→ corregir
→ comparar con diseño
→ continuar
```

No implementes todos los modelos y esperes hasta el final para ejecutar tests.

Después de cada grupo razonable de modelos, ejecuta sus tests.

---

## Revisión cruzada obligatoria

Antes de considerar terminado el loop, compara explícitamente:

```text
docs/design/database/
        ↕
backend/news/models/
        ↕
docs/design/database/07-diagrama.md
        ↕
backend/news/tests/
```

Los cuatro deben representar el mismo diseño.

Si existe diferencia, corrígela antes de continuar.

---

## Tests

Los tests de Loop 01 deben seguir pasando.

Ejecuta como mínimo:

```text
make db-test
```

y cualquier test específico necesario.

No declares éxito basándote únicamente en tests nuevos.

No utilizar Atlas para los tests de modelos.

---

## Atlas

El desarrollador ya verificó manualmente:

```text
make db-ping
```

con resultado:

```text
MongoDB connection: OK
Database: ai_assisted_news
```

No necesitas repetir esa operación.

No realices escrituras en Atlas.

---

## Verificación de trazabilidad

Antes del commit verifica:

```text
[ ] modelos sincronizados
[ ] documentación sincronizada
[ ] diagrama sincronizado
[ ] tests sincronizados
[ ] Makefile sincronizado
[ ] secrets/bootstrap sincronizados
```

Después revisa:

```text
git status
git diff
git diff --cached
```

Comprueba explícitamente:

```text
secret values exposed: NO
secret files tracked: NO
assistant modified: NO
collections created: NO
documents inserted: NO
destructive operations: NO
```

Revisa también cualquier cambio producido por subagentes.

---

## Commit

Solo si Loop 02 satisface completamente su Definition of Done:

```text
feat: add news database models
```

No hagas push.

No hagas commit si el resultado es `partial` o `blocked`.

---

## Handoff

Crear:

```text
backend/loops/handoffs/02-db-models-result.md
```

siguiendo exactamente la estructura solicitada por el loop.

No incluir secretos.

Debe dejar información suficiente para que Loop 03 implemente MongoDB validators e índices sin reinterpretar los modelos.

---

## Respuesta final

Responder únicamente:

1. estado: `completed`, `partial` o `blocked`;
2. ruta del handoff;
3. modelo principal utilizado;
4. subagentes/modelos utilizados y tarea realizada;
5. número de tests ejecutados y resultado;
6. estado de `make setup-keys`;
7. estado de sincronización modelo/documentación/diagrama;
8. hash y mensaje del commit, si existe;
9. decisiones humanas pendientes.

Ejecuta el loop definido en:

```text
backend/loops/03-db-indexes-validation.md
```

## Orquestación

Actúa como agente principal responsable de completar Loop 03.

Modelo principal recomendado:

```text
openai/gpt-5.6-terra
```

Puedes utilizar subagentes cuando la tarea sea claramente separable.

Modelos preferidos para subagentes:

```text
DeepSeek V4 Flash
MiMo-V2.5 Free
Nemotron 3 Ultra Free
```

Si alguno no está disponible, utiliza otro modelo disponible apropiado.

El agente principal conserva responsabilidad sobre:

- decisiones;
- integración;
- ejecución real contra Atlas;
- seguridad;
- revisión final;
- handoff;
- commit.

---

## Delegación recomendada

Considera delegar en paralelo tareas independientes.

### Subagente — Validators

Objetivo:

- comparar los siete modelos contra validators;
- detectar campos/enums/tipos faltantes;
- clasificar reglas MODEL / DATABASE / BOTH.

No debe modificar modelos funcionales salvo reportar una inconsistencia.

### Subagente — Índices

Objetivo:

- revisar Access Patterns documentados;
- revisar índices propuestos;
- detectar índices redundantes o especulativos;
- verificar unique y TTL.

No debe inventar nuevos Access Patterns.

### Subagente — Tests

Objetivo:

- revisar cobertura de initializer, validators, índices y schema check;
- implementar/ampliar tests offline;
- comprobar regresiones.

### Subagente — Seguridad/trazabilidad

Al final puede revisar:

```text
git diff
Makefile
docs/design/database/
backend/news/
```

y verificar que no existan:

- secretos;
- operaciones destructivas;
- cambios en assistant;
- drift documental.

Ningún subagente puede leer `keys/`.

---

## Preparación obligatoria

Antes de modificar archivos:

1. lee `AGENTS.md`;
2. lee `backend/loops/03-db-indexes-validation.md`;
3. lee `backend/loops/handoffs/02-db-models-result.md`;
4. consulta handoffs anteriores cuando sea necesario;
5. lee `docs/design/database/`;
6. inspecciona `backend/news/models/`;
7. inspecciona infraestructura DB existente;
8. ejecuta `git status`.

No asumas que el resumen del handoff sustituye los modelos reales.

---

## Estado heredado

Loop 02 terminó con:

```text
99 passed
```

y siete modelos implementados.

Atlas fue comprobado manualmente:

```text
MongoDB connection: OK
Database: ai_assisted_news
```

No existen todavía colecciones ni documentos creados por estos loops.

---

## Alcance

Este loop SÍ puede:

```text
crear colecciones
crear/aplicar validators
crear índices
crear TTL
usar collMod de forma segura
inspeccionar schema de Atlas
```

Este loop NO puede:

```text
insertar documentos
seedear datos
crear usuarios
crear noticias demo
eliminar documentos
eliminar colecciones
drop database
implementar repositories
implementar endpoints
implementar Firebase
implementar chatbot
modificar assistant/
```

---

## Secretos

No leas directamente:

```text
keys/mongodb_uri
keys/client_id
keys/client_secret
```

No muestres su contenido.

No extraigas username/password de MongoDB.

Utiliza exclusivamente la infraestructura segura creada por loops anteriores.

Si una herramienta requiere exponer el secreto al contexto del agente, NO la utilices.

---

## Estrategia de ejecución

Trabaja incrementalmente:

```text
leer
→ implementar definitions
→ tests
→ implementar validators
→ tests
→ implementar índices
→ tests
→ initializer
→ tests
→ schema check
→ tests
→ documentación
→ regression completa
→ Atlas
→ idempotencia
→ revisión final
```

No esperes hasta el final para probar.

---

## Regla para validators

No conviertas MongoDB `$jsonSchema` en una segunda implementación completa de Pydantic.

Replica en DB las restricciones apropiadas:

```text
estructura
required
bsonType
enum
minimum/maximum
```

Mantén en aplicación reglas complejas como:

```text
cálculos derivados
validación HTTP(S) avanzada
coherencia cross-field difícil de expresar limpiamente
```

Documenta esa separación.

---

## Regla para índices

Cada índice adicional a:

```text
users.firebaseUid UNIQUE
news.slug UNIQUE
chatSessions.expiresAt TTL
```

debe corresponder a un Access Pattern documentado.

No crear índices "por si acaso".

---

## Pruebas offline

Antes de tocar Atlas debe pasar:

```text
make db-test
```

con cero regresiones.

Los tests no pueden depender de Atlas.

Si fallan, corrige antes de continuar.

---

## Ejecución Atlas

Solo después de tests offline exitosos.

Primero verifica mediante la interfaz segura que la DB objetivo sea:

```text
ai_assisted_news
```

Después ejecuta:

```text
make db-init
make db-schema-check
```

Si ambos funcionan, vuelve a ejecutar:

```text
make db-init
make db-schema-check
```

para verificar idempotencia real.

No insertar datos.

No utilizar comandos MongoDB destructivos.

Si el entorno del agente no permite ejecutar estos comandos sin violar `AGENTS.md`, detente antes de Atlas y solicita que el desarrollador ejecute esos comandos manualmente.

---

## Revisión Atlas

Después de `db-init`, la estructura esperada es:

```text
7 collections
validators: OK
indexes: OK
TTL: OK
documents: 0
```

No asumas que las colecciones están vacías si no puedes comprobarlo de forma segura; reporta únicamente lo verificado.

---

## Regression

Antes de cerrar ejecutar nuevamente:

```text
make db-test
```

Los 99 tests heredados deben seguir pasando además de los nuevos.

---

## Trazabilidad

Verifica explícitamente:

```text
[ ] modelos
[ ] validators
[ ] índices
[ ] documentación
[ ] diagrama
[ ] tests
[ ] Makefile
[ ] secrets/bootstrap
```

Todos deben estar sincronizados.

---

## Seguridad

Antes del commit:

```text
git status
git diff
git diff --cached
```

Verifica:

```text
secret values exposed: NO
secret files tracked: NO
assistant modified: NO

documents inserted: NO
documents deleted: NO
collections dropped: NO
database dropped: NO
```

Revisa también los cambios realizados por subagentes.

---

## Commit

Solo si toda la Definition of Done está satisfecha:

```text
feat: add MongoDB schema validation and indexes
```

No hagas push.

Si el loop queda `partial` o `blocked`, no hagas el commit final.

---

## Handoff

Crear:

```text
backend/loops/handoffs/03-db-indexes-validation-result.md
```

Debe seguir exactamente la estructura definida en el loop.

No incluir credenciales ni información sensible.

Debe dejar Loop 04 preparado para trabajar con catálogos y seeders sin reinterpretar la infraestructura física.

---

## Continuidad ante cambio de modelo

Si el modelo principal alcanza límites de créditos/contexto y otro agente debe continuar:

- conservar el working tree;
- no reiniciar el loop;
- revisar `git status` y `git diff`;
- leer este prompt, `AGENTS.md` y el loop;
- verificar mediante tests el trabajo heredado;
- continuar desde la primera fase realmente pendiente;
- no asumir que una tarea marcada como terminada está correcta sin verificarla.

---

## Respuesta final

Responder únicamente:

1. estado: `completed`, `partial` o `blocked`;
2. ruta del handoff;
3. modelo principal;
4. subagentes/modelos y tareas realizadas;
5. total de tests y resultado;
6. resultado de `db-init`;
7. resultado de `db-schema-check`;
8. resultado de segunda ejecución/idempotencia;
9. estado de sincronización de trazabilidad;
10. confirmación de que no se insertaron/eliminaron documentos;
11. hash y mensaje del commit, si existe;
12. decisiones humanas pendientes.

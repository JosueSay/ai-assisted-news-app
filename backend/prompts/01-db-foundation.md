Ejecuta el loop de ingeniería definido en:

```text
backend/loops/01-db-foundation.md
```

## Rol

Actúa como **agente principal y orquestador** de este loop.

Modelo principal recomendado:

```text
DeepSeek V4 Flash
```

Tu responsabilidad es:

- comprender el objetivo completo;
- dividir trabajo cuando sea útil;
- delegar tareas acotadas a subagentes;
- revisar los resultados de los subagentes;
- integrar los cambios;
- ejecutar verificaciones;
- corregir errores;
- validar la Definition of Done;
- crear el handoff;
- realizar el commit final.

No delegues la responsabilidad final del loop.

## Uso de subagentes

Puedes levantar subagentes de OpenCode cuando permitan trabajar en tareas independientes o reducir contexto del agente principal.

Modelos preferidos para subagentes gratuitos:

```text
MiMo-V2.5 Free
Nemotron 3 Ultra Free
```

Puedes utilizar otros modelos gratuitos disponibles en OpenCode cuando alguno de los anteriores no esté disponible o una tarea concreta lo justifique.

Usa subagentes principalmente para tareas delimitadas como:

- inspeccionar convenciones existentes;
- revisar configuración;
- implementar una utilidad aislada;
- escribir tests;
- revisar seguridad;
- revisar documentación;
- analizar fallos de tests;
- revisar el diff antes del commit.

No levantes subagentes innecesariamente.

Cada subagente debe recibir:

1. objetivo concreto;
2. archivos relevantes;
3. restricciones aplicables;
4. resultado esperado;
5. prohibición de ampliar el alcance.

Los subagentes también deben respetar `AGENTS.md`.

### Restricción de secretos

Ningún agente ni subagente puede leer, mostrar, copiar o registrar el contenido de:

```text
keys/
```

Pueden utilizar las interfaces seguras creadas por el proyecto para determinar únicamente estados como:

```text
configured
missing
invalid
```

sin recibir el valor secreto.

---

## Preparación

Antes de implementar:

1. lee `AGENTS.md`;
2. lee `backend/loops/01-db-foundation.md`;
3. lee `backend/loops/handoffs/00-discovery-result.md`;
4. lee los documentos de diseño requeridos por el loop;
5. verifica `git status`;
6. identifica la estructura actual antes de crear archivos.

`AGENTS.md` contiene las reglas globales del repositorio.

El archivo del loop define el alcance y Definition of Done de esta iteración.

---

## Alcance

Ejecuta únicamente Loop 01.

No adelantes trabajo correspondiente a loops posteriores.

En particular:

- no crear las siete colecciones;
- no implementar todavía sus modelos;
- no crear seeders;
- no generar noticias;
- no implementar endpoints;
- no integrar Firebase;
- no implementar el chatbot;
- no modificar `backend/assistant/`;
- no reutilizar la DB `assistant`;
- no acceder ni mostrar secretos;
- no ejecutar operaciones destructivas.

Puedes crear únicamente la infraestructura, configuración, tests, documentación y automatización autorizadas por Loop 01.

---

## Configuración y secretos

Los secretos deben permanecer bajo:

```text
keys/
```

`.env` y `.env.example` son para parametrización no sensible.

Es válido almacenar allí parámetros como:

```text
NEWS_MONGODB_DATABASE=ai_assisted_news
NEWS_MONGODB_URI_FILE=../keys/mongodb_uri
NEWS_MONGODB_TIMEOUT_MS=5000
```

Nunca almacenar allí el contenido del secreto.

Si no existe una credencial MongoDB configurada, continúa con todo lo verificable mediante tests unitarios.

La ausencia de credenciales no bloquea Loop 01.

---

## Engineering loop

Trabaja iterativamente:

```text
leer
→ plantear cambio pequeño
→ implementar
→ ejecutar tests/verificación
→ observar resultado
→ corregir
→ volver a verificar
```

No realices una implementación grande y declares éxito sin comprobarla.

Si delegas trabajo, integra y revisa personalmente el resultado antes de continuar.

No declares una prueba como exitosa si no fue ejecutada.

---

## Verificación final

Antes de terminar:

1. revisa completamente la Definition of Done de `01-db-foundation.md`;
2. ejecuta los tests requeridos;
3. ejecuta las verificaciones de seguridad;
4. revisa `git diff`;
5. revisa `git status`;
6. verifica que `backend/assistant/` no haya sido modificado;
7. verifica que ningún secreto esté tracked;
8. verifica que ninguna URI MongoDB haya sido expuesta;
9. verifica que no se hayan creado colecciones ni datos;
10. revisa los cambios producidos por cualquier subagente.

Si encuentras problemas, vuelve al ciclo de implementación y corrígelos.

---

## Commit

Solo cuando la Definition of Done esté satisfecha crea:

```text
feat: add news database foundation
```

No hagas push.

No crees el commit si el loop está `partial` o `blocked`.

---

## Handoff

Finalmente crea:

```text
backend/loops/handoffs/01-db-foundation-result.md
```

Debe contener exactamente la información exigida por el loop y servir como entrada verificable para Loop 02.

No incluir secretos.

---

## Respuesta final

Al terminar responde únicamente con:

1. estado: `completed`, `partial` o `blocked`;
2. ruta del handoff;
3. modelos utilizados como agente principal y subagentes;
4. tests ejecutados y resultado;
5. hash y mensaje del commit, si fue creado;
6. decisiones humanas pendientes, si existen.

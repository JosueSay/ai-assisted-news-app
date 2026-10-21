# Loop 10 — Restauración del alcance pendiente del Proyecto 2

Fecha: 2026-10-18. Baseline revisado: `ee9cc00`.

## Objetivo y resultado

Guardar las tareas concretas de los ocho puntos seleccionados por el usuario,
manteniendo fuera los dos frentes excluidos. **Completado como documentación**;
no se implementaron las funcionalidades pendientes.

Al comenzar, `docs/reviews/alcance-pendiente-proyecto-2.md` tenía 161 líneas y
cubría exclusivamente configuración/implementación Firebase. Los otros siete
puntos ya no estaban en el archivo. Se leyó primero el handoff
`firebase-auth-preparation-result.md` y se contrastó con el código actual.

## Archivos y cambios

- `docs/reviews/alcance-pendiente-proyecto-2.md`: restaurados ocho aspectos,
  cada uno con estado actual, tareas pendientes en casillas, alcance, abordaje
  y resultado esperado; secuencia de trabajo y condiciones de cierre.
- `docs/reviews/firebase-auth-configuracion.md`: preservada la guía anterior
  completa; únicamente se cambió su título para identificarla como guía específica.
- `docs/README.md`: enlaces al alcance completo y a la guía Firebase.
- `backend/loops/handoffs/firebase-auth-preparation-result.md`: nota de ubicación
  actual de la guía, conservando el resultado histórico del loop.
- Este handoff.

## Decisiones

- El código actual ya integra Firebase; se documenta como pendiente configuración
  y comprobación real, no como implementación inexistente.
- Se conservan las decisiones de identidad descritas por el loop Firebase:
  UID verificado, Anonymous para invitado, rol admin de MongoDB y cuentas previas separadas.
- Los demás puntos se contrastaron con consumidores vigentes y diseño DB aprobado.
- Se concretó qué hacer sin fijar silenciosamente fórmulas de relevancia, política
  editorial, proveedores de imágenes, almacenamiento o cambios estructurales.
- Se mantienen chat inicial móvil, feed para invitado web y panel existente para
  administrador web; esas rutas siguen pendientes de implementación.
- La guía específica no volverá a sustituir el documento de ocho puntos al completar uno.

## Comandos y verificaciones

- `git status --short`, `git log -1 --oneline`, `wc -l`, `rg` y lectura acotada
  de archivos de documentación/código, excluyendo secretos.
- Plan temporal: `/tmp/news-scope-restoration/task_plan.md`.
- Verificación estructural: ocho secciones numeradas y cinco apartados por sección,
  cada una con tareas explícitas sin marcar completadas.
- Enlaces locales y tablas Markdown comprobados.
- Guía Firebase comparada con copia temporal original: contenido posterior al
  título idéntico.
- `git diff --check`: correcto.
- No se ejecutaron suites: no hay cambios de comportamiento. Los resultados de
  pruebas mencionados por el handoff Firebase siguen siendo históricos.

## Trazabilidad y pendientes

- Modelos, validators, índices, seeders, diagrama, tests, Makefile y requisitos
  de secretos/bootstrap: sin cambios necesarios; solo se documenta alcance.
- Documentación: alcance y guía separados y enlazados, con estado actual revisado.
- No se leyó contenido de `keys/`, no hubo llamadas IA ni operaciones DB.
- No hay bloqueo para entregar este documento. Cada implementación requiere su
  alcance concreto y resolver las decisiones técnicas de las que dependa.
- Commit/push: ninguno; índice sin cambios. Working tree inicialmente limpio;
  al cierre solo se modifican/añaden los archivos documentales listados arriba.

# Loop 12 — Correcciones de diversidad y refresco tras leer

Fecha: 2026-10-20.

## Objetivo

Corregir los dos problemas señalados en la revisión del working tree, por petición
expresa del usuario: diversidad por actualidad y actualización del feed después
de leer. Se leyó el handoff del Loop 11 y el diseño aprobado de personalización.

## Cambios y archivos

- `backend/news/personalization.py`: las posiciones reservadas 4 y 9 toman las
  noticias diversas aún no mostradas por fecha descendente e ID ascendente, con
  fechas ausentes al final. El resto conserva el ranking personalizado.
- `backend/news/tests/test_personalization.py`: dos regresiones sobre actualidad
  frente a afinidad declarada/inferida, empates, fechas ausentes y duplicados.
- `frontend/src/features/news/NewsFeedScreen.tsx`: al salir del detalle vuelve a
  consultar el feed, esperando el envío final de `opened` con el tiempo activo.
  Un `read` confirmado invalida el ranking; si termina después del regreso, lo
  vuelve a consultar. Mientras se lee no sustituye el artículo ni sus mediciones.
- `frontend/tests/newsFeedReading.test.tsx`: cinco pruebas con estado y efectos
  reales de React; sustituye renderizado nativo, Firebase y HTTP. Cubre espera
  del tiempo final, regreso por hash/Atrás, lectura tardía, fallo del envío final
  y enlace inicial a un artículo fuera del feed.
- `frontend/package.json` y `frontend/package-lock.json`: `happy-dom` y
  `@types/react-dom` solo para desarrollo, para ejecutar esas pruebas en Vitest
  sin navegador, cuentas ni red reales. No cambian dependencias de producción.
- `docs/design/database/03-criterios-de-personalizacion.md`: explicita desempates
  de diversidad y el refresco tras finalizar señales de lectura.
- `docs/reviews/alcance-pendiente-proyecto-2.md`: enlaza estas correcciones.
- Este handoff.

## Causas y decisiones

El selector de diversidad recorría el ranking general y podía priorizar noticias
antiguas por interés. Ahora dispone de un orden por actualidad para las reservas,
sin modificar pesos ni las tres primeras posiciones.

El frontend solo recargaba el feed al montar o guardar preferencias. Ahora la
salida del artículo dispara la consulta después de finalizar el envío del tiempo
activo. Las respuestas tardías de lectura también disparan actualización. Los
errores del envío final no bloquean la consulta del ranking ya aprendido.

No hay cambios de esquema, índices, catálogos, credenciales o endpoints. No se
modificaron los cambios anteriores ajenos a estas dos correcciones.

## Comandos, pruebas y resultados

- `git status --short`, lectura de handoff/diseño/skills y revisión acotada de diffs.
- Pruebas de personalización en la imagen existente, con backend montado de solo
  lectura, sin red ni `keys/`: las dos regresiones fallaron primero por el orden
  incorrecto; tras la corrección, **8 passed**.
- `cd frontend && npm test -- tests/newsFeedReading.test.tsx`: las tres primeras
  regresiones fallaron antes del cambio porque no se volvía a consultar `/news`.
- `npm install --save-dev happy-dom --ignore-scripts --no-audit --no-fund`.
- El intento inicial de instalar `@types/react-dom@^19` falló por incompatibilidad
  con los tipos React 19.2 existentes; se instaló `@types/react-dom@~19.2.0` con
  las mismas opciones. No se forzaron dependencias ni se actualizaron tipos React.
- `cd frontend && npm run typecheck`: correcto.
- `cd frontend && npm test`: **26 passed**, cinco archivos.
- La imagen Docker local carecía de `httpx2`, ya declarado por el Loop 11. Se
  instaló temporalmente fuera del repositorio en `/tmp/news-feed-fixes-test-deps`:

  ```sh
  mkdir -p /tmp/news-feed-fixes-test-deps
  docker run --rm --user "$(id -u):$(id -g)" --read-only --tmpfs /tmp \
    -v /tmp/news-feed-fixes-test-deps:/test-deps \
    ai-assisted-news-app-news-api:latest python -m pip install \
    --disable-pip-version-check --no-cache-dir --target /test-deps 'httpx2>=2.0,<3'
  ```

- Suite backend completa, equivalente a la de `make db-test`, aislada sin red,
  secretos ni MongoDB real:

  ```sh
  docker run --rm --network none --read-only --tmpfs /tmp \
    -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/test-deps:/app/backend \
    -v /tmp/news-feed-fixes-test-deps:/test-deps:ro \
    -v "$PWD/backend:/app/backend:ro" \
    -v "$PWD/frontend/src/generated:/app/frontend/src/generated:ro" \
    ai-assisted-news-app-news-api:latest \
    python -m pytest -p no:cacheprovider news/tests -q
  ```

  Resultado final: **233 passed**. La primera ejecución dio 232 aprobadas y una
  omitida porque no estaba montado el contrato generado del frontend; al montarlo
  de solo lectura se verificó también ese contrato, sin omisiones.
- `git diff --check`: correcto. Índice Git sin archivos staged.

## Trazabilidad

- [x] Modelos y validaciones sincronizados: revisados, sin cambios estructurales.
- [x] Documentación sincronizada: criterios y alcance actualizados.
- [x] Diagrama sincronizado: revisado, relaciones y campos sin cambios.
- [x] Tests sincronizados: regresiones backend y componente React añadidas.
- [x] Makefile revisado: comandos existentes suficientes; sin cambios.
- [x] Secrets/bootstrap revisados: no hay secretos nuevos; sin cambios necesarios
  en configuración, `setup-keys` ni `keys/README.md`. No se leyó `keys/`.
- Índices y seeders revisados: estas correcciones no requieren cambios.

## Estado final y siguiente paso

- Objetivo completado; sin decisiones pendientes ni bloqueos para estas correcciones.
- Commit/push: ninguno. Working tree conserva las modificaciones de los Loops
  10/11, más los cambios de este handoff; todo continúa fuera de staging.
- Sin operaciones sobre Atlas, llamadas a IA ni cambios de datos reales.
- Sigue pendiente la validación manual con Firebase real y dispositivos/navegadores
  mencionada en el Loop 11. Las pruebas de componente no verifican geometría real
  ni sustituyen esa revisión visual.

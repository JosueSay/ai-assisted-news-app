# Firebase Hosting — corrección de fuentes del export Expo

Fecha: 2026-10-20.

## Objetivo y causa

Corregir los errores de decodificación de fuentes reportados tras la publicación.
Se consultaron los handoffs de integración Firebase y las skills de diagnóstico,
TDD y revisión ya utilizadas en esta sesión.

Una petición pública a la fuente Newsreader devolvió HTTP 200 y `text/html`, con
cabecera HTML. La fuente existe en el export local y tiene cabecera TTF válida.
La regla `**/node_modules/**` de `hosting.ignore` excluía las fuentes exportadas en
`assets/node_modules/`. Al faltar el recurso publicado, el fallback SPA devolvía
`index.html`, que el navegador intentaba interpretar como fuente.

## Cambios y archivos

- `firebase.json`: retirada de la exclusión de `node_modules` dentro del export;
  se conserva `public=frontend/dist` y la exclusión de archivos ocultos.
- `tests/unit/test_deploy_scripts.py`: regresión para fuentes Newsreader y Roboto.
- `docs/deploy/firebase-paso-a-paso.md`: documentado que estos recursos Expo deben
  publicarse y no son las dependencias del directorio raíz.
- Este handoff.

## Pruebas y resultados

- Petición HTTPS pública sin credenciales: reproducido recurso de fuente servido
  como HTML; no se imprimió el bundle ni configuración del cliente.
- `make deploy-test`: la regresión falló antes de corregir la regla; después,
  **4 passed**.
- Selector real `firebase-tools/lib/listFiles.js`, sin autenticación ni deploy:
  **35 archivos seleccionados, 32 fuentes TTF**, incluidas Newsreader semibold
  y Roboto regular. Todas las fuentes seleccionadas tienen cabecera válida.
- `git diff --check`: correcto.

## Decisiones, pendientes y estado

- Cambio limitado a selección de archivos Hosting; no cambia UI, Auth, API, DB,
  índices, seeders, secretos ni Makefile. No requiere cambios del diagrama DB.
- Sin acceso a archivos secretos de `keys/`, ni operaciones Atlas o llamadas IA.
- Pendiente repetir `make firebase-deploy` y recargar el navegador sin caché para
  verificar la corrección publicada. No se ejecutó un redeploy en este loop.
- Sin decisiones pendientes ni bloqueos de implementación. Commit/push: ninguno.
  El working tree conserva los cambios previos de integración y añade esta
  corrección; no se descartó trabajo del usuario ni se hizo staging.

# Hosting — configuración Firebase ausente por caché de export

Fecha: 2026-10-20.

## Objetivo y diagnóstico

Resolver la pantalla publicada con ambos accesos deshabilitados y el aviso de
configuración pública Firebase pendiente. Se reutilizaron las skills locales de
diagnóstico, TDD y revisión, y se consultó el handoff de integración y la
corrección de fuentes inmediatamente anterior.

Los cuatro parámetros públicos están presentes en `frontend/.env` y el proyecto
coincide con el seleccionado por el usuario. Se comprobó únicamente presencia y
coincidencia, sin imprimir valores. El bundle publicado no incluía el proyecto
ni el dominio esperado. El código inhabilita ambos botones si falta alguno de
esos valores en la configuración compilada.

Se reprodujo con dos exports reales: el export normal reutilizaba transformaciones
sin configuración, incluso cargando correctamente dotenv; el export con `--clear`
incorporó los seis valores públicos actuales (cuatro Firebase y dos URLs API).
No se ejecutó login, API, Atlas ni IA durante esta reproducción.

## Cambios y archivos

- `deploy/firebase/hosting.sh`: export previo a publicar con
  `npm run export:web -- --clear`, conservando preflight y proyecto explícito.
- `tests/unit/test_deploy_scripts.py`: el contrato exige reconstrucción sin caché.
- `docs/deploy/firebase-paso-a-paso.md`: documentados el rebuild y el diagnóstico
  de botones deshabilitados.
- Este handoff.

## Verificación

- Regresión del script falló sin `--clear` y pasó tras el cambio.
- `make deploy-test`: **4 passed**.
- Export previo: `NODE_ENV=production npm run export:web -- --output-dir
  /tmp/news-firebase-auth-before`; correcto, pero proyecto/dominio no incorporados.
- Export corregido: `NODE_ENV=production npm run export:web -- --clear --output-dir
  /tmp/news-firebase-auth-after`; correcto, proyecto/dominio incorporados.
- Comprobación de los seis parámetros públicos contra el bundle reconstruido:
  todos incluidos, sin imprimir valores.
- `git diff --check` y sintaxis Bash: correctos.

## Decisiones, pendientes y estado

Se mantiene el comportamiento del cliente y el contrato de Auth; no cambian UI,
DB, modelos, validadores, índices, diagramas, catálogos ni secretos. El coste de
recompilar los módulos al publicar evita reutilizar configuración antigua.
Los artefactos de reproducción permanecen en `/tmp/`, fuera del árbol versionado.

Implementación y verificación local completas; pendiente que el usuario repita
`make firebase-deploy` y pruebe login e invitado en el sitio publicado. No se
ejecutó deploy remoto, no se accedió a secretos de `keys/` y no se registró gasto IA.
Sin bloqueos ni nuevas decisiones pendientes. Commit/push: ninguno; los cambios
anteriores se conservan en el working tree, sin staging.

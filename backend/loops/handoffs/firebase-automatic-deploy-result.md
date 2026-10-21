# Publicación automática de Cloud Run y Hosting

Fecha: 2026-10-20.

## Objetivo

Completar el pipeline existente para publicar backend y frontend desde `main`,
y entregar los pasos para activarlo en el proyecto ya desplegado manualmente.
Se consultaron los handoffs de integración Firebase y correcciones de fuentes
y caché del export, y se aplicaron planificación, TDD, revisión y seguridad.
El working tree inicial de este cambio estaba limpio.

## Cambios y archivos

- `.github/workflows/deploy.yml`: publicación Cloud Run seguida de Hosting tras
  los jobs de pruebas. Node 24, Firebase CLI 15.34.0, variables públicas de GitHub,
  WIF/ADC y renovación de credenciales antes de Hosting. Solo corre el deploy
  desde `main`; los pull requests ejecutan las pruebas.
- `deploy/gcp/check-ci-config.sh`: preflight sin llamadas cloud. Exige proyecto,
  región, WIF, cuenta, cuatro parámetros Firebase, coincidencia de proyecto y
  precios numéricos de OpenAI. Falla antes de modificar servicios si falta algo.
- `deploy/firebase/ci.sh`: obtiene URLs de los servicios recién desplegados,
  descarta dotenv local y reutiliza el flujo Hosting con validación y `--clear`.
  Si falla una consulta de URL no exporta ni publica.
- `deploy/firebase/hosting.sh`: CLI no interactiva, compatible con WIF/ADC.
- `deploy/gcp/bootstrap.sh`: APIs Firebase y roles Hosting Admin, API Keys Viewer
  y Service Usage Consumer para `gh-deployer` en el proyecto Auth/Hosting.
- `tests/unit/test_deploy_scripts.py`: regresiones preflight, IAM y resolución
  de URLs/publicación; conserva pruebas de fuentes y caché.
- `docs/deploy/pipeline-paso-a-paso.md`: nueva guía específica con parámetros
  públicos del proyecto, activación, variables GitHub y verificación del primer run.
- `docs/deploy/firebase-paso-a-paso.md`, `docs/deploy/README.md`, `docs/README.md`
  y `deploy/TODO_deploy.md`: sincronizados con Hosting automático.
- Este handoff.

## Decisiones

- Se reutiliza la identidad WIF existente. No se añaden secretos requeridos,
  tokens Firebase permanentes ni cuentas de servicio con claves JSON.
- OpenAI es el proveedor predeterminado del pipeline, según la decisión del
  usuario. La región debe configurarse explícitamente para evitar publicar en
  una distinta de la infraestructura existente (`us-east4`).
- La cuenta del pipeline mantiene sus permisos anteriores y recibe permisos
  específicos Hosting; no se le concede Owner ni acceso directo a valores secretos.
- Los datos web Firebase vienen de variables públicas del entorno GitHub
  `production`. Las URLs backend se consultan automáticamente en Cloud Run.
- Se mantiene el primer despliegue manual y la preparación DB fuera del pipeline.
  No hay migraciones, reseeds, carga de secretos ni rollback conjunto automático.
- No hubo push, publicación, cambios IAM remotos ni lectura de secretos desde
  esta sesión; el usuario activará los pasos externos de la guía.

## Verificación y comandos

- Lectura acotada de workflow, bootstrap, scripts y handoffs; se confirmó la
  rama `firebase` y el repo `JosueSay/ai-assisted-news-app` sin imprimir remotes
  que pudieran contener credenciales.
- Documentación oficial Firebase consultada para roles Hosting/API Keys Viewer
  y autenticación CI con ADC; enlaces en la guía.
- `make deploy-test`: **7 passed**, sin cloud, red, credenciales ni MongoDB real.
  Las pruebas IAM y publicación reprodujeron inicialmente los permisos/flujo
  ausentes. Se prueban configuración válida, campos ausentes, proyecto distinto,
  precios inválidos, URLs obtenidas, aborto por error y secuencia de publicación.
- `bash -n` sobre scripts nuevos/modificados: correcto.
- YAML del workflow parseado en contenedor sin red; verificados jobs requeridos,
  preflight previo a mutaciones, orden backend → Hosting, guard de `main`, región
  explícita y permiso OIDC: correcto.
- Ruff sin caché sobre `tests/unit/test_deploy_scripts.py`: correcto.
- Scanner acotado a `deploy/` y workflow: **0 hallazgos**; no se escaneó `keys/`.
- `git diff --check`: correcto; staging vacío.
- Plan de trabajo en `/tmp/news-auto-deploy-plan.md`, fuera del árbol versionable.

## Trazabilidad y estado

- Modelos, validadores, índices, diagrama, catálogos, seeders y TTL: revisados por
  alcance, sin cambios DB necesarios.
- Documentación y tests: actualizados para activación y nuevos comandos CI.
- Makefile: revisado; los targets existentes siguen siendo suficientes.
- Secrets/bootstrap local: sin secretos nuevos; `setup-keys` y `keys/README.md`
  permanecen correctos. Solo cambia el bootstrap IAM cloud.
- Commit/push: ninguno. Working tree contiene los archivos listados, sin staging.
- Implementación local completa. La activación externa y primera ejecución real
  siguen pendientes; no se afirma que IAM/GitHub remoto ya estén configurados.
- Siguiente paso: repetir el bootstrap con proyecto/región existentes, crear
  `production`, completar variables, subir los cambios por PR a `main` y comprobar
  el run completo y la aplicación. La guía incluye todos los valores públicos
  conocidos y pide copiar únicamente API key pública Firebase y App ID web local.

## Seguimiento: transferencia del repositorio

Durante la activación, GitHub confirmó mediante redirección pública que el repo
pasó a `ai-project-u1g/ai-assisted-news-app`. Una consulta de solo lectura a WIF
(`gcloud ... providers describe --format='value(attributeCondition)'`) confirmó
que aún exigía el nombre anterior `JosueSay/ai-assisted-news-app` y `main`.

Se actualizó `deploy/gcp/config.sh` al propietario vigente y el bootstrap ahora
reconcilia providers existentes mediante `update-oidc`, además de crearlos cuando
faltan. Reaplicar el bootstrap concede la vinculación del repo actual y mantiene
la condición de rama `main`. El repo anterior deja de satisfacer la condición.
El remote local todavía usa el nombre anterior y GitHub lo redirige; no se cambió
su URL ni protocolo automáticamente.

La regresión del bootstrap exige actualización del provider existente y la
vinculación de un propietario nuevo: falló antes del cambio y pasó después.
`make deploy-test`: **7 passed**; sintaxis Bash y `git diff --check`: correctos.
La guía pipeline añade el `GITHUB_REPO` explícito y el procedimiento tras una
transferencia. Se consultó la referencia oficial `providers update-oidc`.

No se aplicó la mutación IAM desde el agente. El usuario debe repetir el bootstrap
actualizado con el repo vigente; las variables GitHub conservan el mismo
`WIF_PROVIDER` y `DEPLOYER_SA`. Sin cambios DB, secretos, commit ni push.

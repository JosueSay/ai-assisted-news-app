# APK y enlace web automáticos

Código preparado; falta agregar la credencial externa, integrar los cambios a
main y verificar una ejecución real. El flujo en cada publicación de main es:
pruebas → APK EAS terminado → Cloud Run → export web con URL del APK → Hosting.
También ocurre con Run workflow en main. Cada ejecución solicita un APK y puede
esperar en la cola de tu plan Expo; esto alarga el deploy de backend/web.

## 1. Crear token Expo

1. Abre <https://expo.dev/accounts/donmathiuz/settings/access-tokens>.
2. Crea un token personal con nombre descriptivo, por ejemplo `github-ai-news`.
3. Conserva su valor únicamente en un gestor seguro o en `keys/expo_token` si
   necesitas una copia local. No lo pegues en chat, `.env`, variables públicas o Git.
   `make setup-keys` prepara ese archivo vacío sin sobrescribir archivos existentes.

## 2. Guardarlo en GitHub

1. Abre el repositorio `ai-project-u1g/ai-assisted-news-app`.
2. Ve a Settings → Environments → production.
3. En **Environment secrets**, pulsa **Add environment secret**.
4. Nombre exacto: `EXPO_TOKEN`. Valor: el token Expo creado por ti.
5. Guarda. No lo pongas en **Environment variables**.

El workflow lo entrega únicamente al paso EAS. No hace falta firebase login:ci,
subir la clave OpenAI a GitHub, ni cambiar la firma Android.

## 3. Comprobar requisitos del proyecto

- Proyecto EAS vinculado en `frontend/app.json`, cuenta con permiso para compilar.
- Firma Android existente en EAS, registrada en Firebase mediante SHA-1/SHA-256.
- `frontend/google-services.json` actualizado y disponible en el checkout de CI.
  Es configuración pública de Firebase, no una clave de cuenta de servicio.
- Las seis variables públicas Firebase/APIs en Expo production, ya configuradas.
- El entorno GitHub production conserva sus variables Firebase/GCP y acceso WIF.
- `frontend/eas.json` usa appVersionSource remote y autoIncrement para `apk`:
  EAS inicializa el contador desde el valor local si no existe y gestiona los
  siguientes. Si hay un APK instalado con un contador mayor, usa personalmente
  `npx eas-cli@25.3.0 build:version:set --platform android --profile apk` para
  sincronizar el valor remoto antes de continuar. Conserva el mismo keystore.

## 4. Integrar los cambios

Desde la raíz ejecuta `make deploy-test`; desde frontend ejecuta `npm test` y
`npm run typecheck`. Revisa `git diff --check` y `git status --short`.
Incluye el workflow, scripts Expo, configuración EAS, package/lock, configuración
pública Google, cambios frontend, pruebas y documentación. Excluye `.env`, keys
privadas, APK/export y la fixture temporal `.expo/`.

Crea un commit Conventional Commits, haz push de tu rama y abre una PR hacia
main. Tras pasar pruebas, haz merge. El agente no hace push automáticamente.
Las PR solo ejecutan pruebas; no compilan en Expo ni reciben EXPO_TOKEN.

## 5. Verificar publicación real

En Actions → deploy abre la ejecución del merge:

1. Tests backend/frontend pasan.
2. **Generar APK Android y preparar enlace de descarga** termina correctamente.
3. Cloud Run se publica.
4. Hosting termina con Deploy complete.
5. Abre la web, comprueba “Descargar para Android” y que su destino sea el
   artefacto nuevo `https://expo.dev/artifacts/eas/…apk`.
6. Descárgalo en el teléfono y verifica Google, asistente y teclado.

La automatización solo está comprobada cuando esa ejecución y la descarga real
funcionan. Las pruebas locales simulan EAS y no verifican credenciales, cuotas,
compilación Gradle, disponibilidad pública del artefacto ni permisos de cuentas.

## Comportamiento y fallos

`make android-apk-ci` solo se usa en el runner. Usa EAS CLI 25.3.0, espera el build
y congela credenciales para evitar cambiar la firma automáticamente. Valida
proyecto EAS, perfil apk, distribución interna, plataforma Android, estado final
y URL HTTPS de APK antes de exportarla mediante GITHUB_ENV.

Si falta token, falla EAS o el resultado no es válido, el job se detiene antes
de Cloud Run/Hosting. Si falla Hosting después, el APK puede existir pero la web
conserva su publicación anterior; no hay rollback conjunto. Reejecutar el workflow
solicita otro build. El tiempo máximo del job es 180 minutos; al agotarse, una
compilación EAS ya solicitada podría seguir corriendo y se revisa desde Expo.

No existe actualización silenciosa de apps instaladas: se descarga e instala el
APK nuevo. `make android-apk` manual sigue disponible, pero no cambia Hosting.
Para publicar un build manual en la web, define EXPO_PUBLIC_ANDROID_DOWNLOAD_URL
en frontend/.env y ejecuta `make firebase-deploy`.

Referencias: [CI de EAS](https://docs.expo.dev/build/building-on-ci/),
[tokens Expo](https://docs.expo.dev/accounts/programmatic-access/),
[versiones remotas](https://docs.expo.dev/build-reference/app-versions/).

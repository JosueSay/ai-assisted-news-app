# APK y enlace web automáticos

## Objetivo y estado

El usuario pidió automatizar la actualización del enlace del APK en la web y
guiarlo paso a paso. Implementación local preparada y verificada sin cloud.
Pendientes: token Expo en GitHub production, integración a main y ejecución real.

## Cambios

- `.github/workflows/deploy.yml`: después de pruebas, build APK antes de obtener
  WIF y publicar backends/Hosting. Límite 180 minutos; token Expo solo en ese paso.
- `deploy/expo/build-ci.sh` / `make android-apk-ci`: EAS CLI 25.3.0, perfil apk,
  wait/json/non-interactive/freeze-credentials. Temporal JSON protegido y borrado
  al salir; no imprime token. Requiere Google Services JSON y runner GitHub.
- `frontend/scripts/android-build-result.cjs` y declaración: valida un resultado,
  estado FINISHED, Android, apk, INTERNAL, app.id vinculado y URL directa HTTPS
  expo.dev/artifacts/eas/*.apk sin credenciales/query/fragmento/espacios.
  Exporta EXPO_PUBLIC_ANDROID_DOWNLOAD_URL mediante GITHUB_ENV para Hosting.
- `frontend/src/components/AndroidDownload.web.tsx`: usa URL inyectada y texto
  de descarga directa; fallback al build inicial para publicaciones manuales
  sin esa configuración. Validación opcional añadida al check de Hosting.
- `frontend/eas.json`: versiones remotas con autoIncrement en apk. EAS puede
  inicializar el contador con el versionCode local actual (3); luego lo gestiona.
  No se cambió el contador remoto mediante herramientas en esta tarea.
- `.env.example`, guías deploy/Android/pipeline y nueva guía
  `docs/deploy/android-automatico-paso-a-paso.md` sincronizadas.
- `make setup-keys` crea también expo_token vacío si falta; keys/README explica
  copia local opcional. APIs/DB no requieren ese token. En CI el SDK recibe
  EXPO_TOKEN temporal desde GitHub Secrets, nunca desde .env ni EXPO_PUBLIC_*.
  No se creó, abrió, copió ni modificó ningún archivo de secreto real.

## Verificaciones

- Skills planning-with-files/TDD/code-reviewer y security-compliance aplicadas.
- Prueba selectora escrita antes del helper: falla por módulo inexistente.
  Corregido it.each para no expandir arrays de resultado en argumentos distintos.
- `npm test`: 10 archivos, 66 pruebas OK (12 nuevas de selección/URL del botón).
- `npm run typecheck`: OK.
- `make deploy-test`: 9 tests OK. Nuevos escenarios con npx falso comprueban
  éxito, fallo CLI, resultado inválido y token ausente; no se contactó EAS.
  Bootstrap probado dos veces en directorio efímero, conserva tamaño/mtime del
  archivo sintético preexistente sin leer credenciales reales.
- `bash -n deploy/expo/build-ci.sh`, parse YAML y `git diff --check`: OK.
- Export web limpio con URL pública ficticia: OK; bundle contiene URL inyectada.
  Artefacto local `/tmp/news-auto-apk-web-export`, no publicado.
- Escáner seguro sobre deploy/expo, helper y workflow: 0 hallazgos, sin abrir
  keys/ ni .env. Primera invocación con múltiples objetivos no admitida; repetida
  correctamente con un objetivo por llamada.
- Revisado código instalado de EAS CLI para JSON BuildFragment (app.id), flags
  freeze-credentials y comportamiento de inicialización/incremento remoto.

## Controles revisados

| Riesgo | Control |
| --- | --- |
| Token dentro del cliente/log | Secret solo en paso EAS; no prefijo público; sin echo/set -x |
| URL no perteneciente al APK esperado | Valida proyecto, perfil, plataforma, distribución, estado y URL |
| Publicar tras fallo de build | set -e y paso obligatorio antes de Cloud Run/Hosting |
| Cambiar firma sin intervención | freeze-credentials; usa firma EAS existente |
| Credenciales en una PR | deploy limitado a main/no pull_request, entorno production |

## Pendientes para usuario y límites

1. Crear token Expo y guardarlo como Environment secret EXPO_TOKEN en GitHub
   production. No enviarlo al agente. Copia local solo si se necesita, en keys/.
2. Confirmar Google Services JSON público en checkout y seis variables EAS
   production configuradas; conservar firma y SHA de Firebase.
3. Revisar/commit/push/PR/merge de cambios acumulados a main.
4. Comprobar ejecución real: APK, Cloud Run, Hosting y descarga nueva desde web.
5. Instalar y probar Google/chat/teclado en Android físico.

Cada publicación de main, incluso backend-only o reejecución manual, solicita un
APK y consume la capacidad/cola del plan EAS. El job completo espera; no hay
rollback conjunto. Un timeout de GitHub podría dejar EAS compilando remotamente.
Builds manuales no actualizan Hosting por sí solos. Sin variable pública, un
Hosting manual vuelve al fallback inicial; la guía indica cómo publicar una URL manual.
Una app instalada sigue necesitando descargar/instalar su actualización.

No se ejecutó build remoto, no se verificaron permisos/token/cuota reales, ni
se comprobó disponibilidad HTTP del APK real. No se hizo commit, push o deploy.
Working tree conserva los cambios previos de Google nativo y UI móvil además de
estos cambios. DB: modelos, diseño, diagrama y seeders no afectados; tests,
Makefile y secrets/bootstrap revisados y sincronizados para el nuevo token CI.

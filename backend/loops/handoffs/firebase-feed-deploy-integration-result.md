# Integración del feed y despliegue Firebase — resultado

Fecha: 2026-10-20.

## Objetivo

Comprobar e integrar el feed implementado con Firebase Auth y los scripts de
despliegue, corregir los fallos encontrados y entregar una guía Markdown paso a
paso para configurar el proyecto y publicar la aplicación.

Se leyeron `AGENTS.md`, los handoffs Firebase, Loop 11 y Loop 12, los criterios
aprobados de personalización/chat y el diagrama vigente. Working tree inicial limpio.

## Causas encontradas y cambios

1. Los scripts Cloud Run conservaban la contraseña admin retirada por Firebase,
   y omitían `NEWS_FIREBASE_PROJECT_ID` y los orígenes CORS del portal. Una prueba
   de comandos simulados reprodujo la ausencia de Project ID antes de corregirlos.
   Ahora ambos backends reciben proyecto y CORS; las comas de los orígenes se
   preservan con un delimitador alternativo de gcloud. Solo se montan los secretos
   vigentes. No se borró ningún secreto local ni remoto preexistente.
2. Faltaba la publicación web: se añadieron `firebase.json`, un script Hosting,
   export Expo y validación previa de parámetros públicos. La validación rechaza
   proyecto distinto, valores ausentes y URLs locales/sin HTTPS o con credenciales.
3. Se reprodujo además que Make podía sobrescribir parámetros cloud heredados
   con los valores del `.env` raíz local. Los targets cloud ahora usan el entorno
   y `deploy/gcp/config.sh`; los targets locales conservan su `.env`. Se rechazan
   invocaciones que mezclan targets cloud y locales para evitar ambigüedad.
4. El workflow valida backend, frontend, scripts e integración efímera antes de
   desplegar Cloud Run. La configuración proviene de variables del entorno GitHub
   `production`. El modo predeterminado del workflow es `stub`; Hosting es manual.
5. Se declaró explícitamente el transporte `requests` de `google-auth`, usado
   para obtener certificados Firebase. La imagen API reconstruida importa el
   transporte y la aplicación correctamente.
6. Se amplió la prueba MongoDB real temporal para CORS de Hosting, preferencias,
   feed autenticado, señales de lectura, deduplicación, aprendizaje y refresco.
   El comportamiento del feed existente pasó sus pruebas; no se cambiaron sus
   pesos, reglas de diversidad, modelos, endpoints ni componentes visuales.

## Archivos creados

- `firebase.json`.
- `deploy/firebase/hosting.sh`.
- `frontend/scripts/check-deploy-config.cjs` y su declaración `.d.cts`.
- `frontend/tests/deployConfig.test.ts`.
- `tests/unit/test_deploy_scripts.py`.
- `docs/deploy/firebase-paso-a-paso.md`.
- Este handoff.

## Archivos modificados

- `deploy/gcp/{config,bootstrap,load-secrets,deploy}.sh`.
- `Makefile`, `.github/workflows/deploy.yml`, `.gitignore`, `.dockerignore`.
- `backend/news/requirements.txt`, `frontend/package.json`.
- `tests/integration/test_news_shared_contract.py`.
- `docs/deploy/README.md`, `deploy/TODO_deploy.md`, `docs/README.md`.
- `docs/reviews/firebase-auth-configuracion.md`, `frontend/README.md`.
- `keys/README.md`: exclusivamente documentación versionada no secreta.

## Decisiones

- Se mantiene la infraestructura existente: Firebase Auth/Hosting, Cloud Run y
  MongoDB Atlas independiente del assistant histórico. No se añadieron plataformas
  de infraestructura, ODM, colecciones ni dependencias arquitectónicas nuevas.
- Por defecto, Auth y Hosting usan el proyecto Cloud Run; se permite indicar
  `NEWS_FIREBASE_PROJECT_ID` explícito. El frontend debe usar ese mismo ID de Auth.
- CORS permite por defecto los dos dominios Hosting del proyecto Firebase;
  dominios propios requieren configuración explícita de ambos backends.
- No se publica automáticamente desde esta sesión. El usuario solicitó reparar
  la integración y una guía para configurar su proyecto y desplegar.
- No se leyó, imprimió, copió ni modificó ningún archivo secreto de `keys/`.
  Solo se consultó y actualizó su README versionado. No hubo llamadas reales a
  Firebase Auth, Atlas u OpenAI ni registros en `aiUsage` de producción.

## Comandos y resultados

- `git status --short`, `git log -7 --oneline`, búsquedas y lecturas acotadas.
- `make deploy-test`: **3 passed**. Cubre Firebase/CORS/secretos montados, orden
  preflight → export → Hosting, abortar antes de publicar y aislamiento de `.env`.
  Las regresiones de Project ID ausente y contaminación local fallaron primero.
- `cd frontend && npm test`: **35 passed**, seis archivos.
- `cd frontend && npm run typecheck`: correcto.
- `NODE_ENV=production EXPO_NO_DOTENV=1 EXPO_NO_TELEMETRY=1 npm run export:web`:
  correcto, genera `frontend/dist` ignorado por Git.
- `make firebase-check-config` con valores públicos de fixture y
  `EXPO_NO_DOTENV=1`: correcto, sin consultas cloud ni lectura de secretos.
- Build de pruebas:
  `docker build -f backend/assistant/Dockerfile --target test -t ai-news-firebase-tests:local backend`.
- Suite backend en contenedor aislado, sin red ni `keys/`, con `backend/` y
  contrato frontend montados de solo lectura:

  ```bash
  docker run --rm --network none --read-only --tmpfs /tmp \
    -e OPENAI_API_KEY_FILE=/tmp/missing-key -e API_GPT= \
    -v "$PWD/backend:/app:ro" \
    -v "$PWD/frontend/src/generated:/frontend/src/generated:ro" \
    ai-news-firebase-tests:local \
    python -m pytest -p no:cacheprovider news/tests assistant/tests -q
  ```

  **400 passed, 1 skipped**. Solo se omite el smoke test que requiere servicios
  levantados vía Compose. El primer intento con una imagen local antigua falló
  en colección por dependencias ausentes; se reconstruyó la imagen apropiada.
- `make news-integration-test`: **1 passed**, MongoDB 8 temporal en red interna,
  sin volumen persistente ni secretos. Confirma CORS, bootstrap reproducible,
  preferencias, feed, aprendizaje `0.1`, dos eventos pese a reintentos, chat,
  aislamiento de identidad, admin, validadores, índices y TTL. No usa Atlas.
- Build API: `docker build -f backend/news/Dockerfile -t ai-news-firebase-api:local .`:
  correcto. Imports de transporte Firebase y `news.api` en esa imagen: correctos.
- Ruff sin caché sobre los dos archivos Python de pruebas afectados: correcto.
- `bash -n` sobre los scripts cloud/Hosting y `node --check` del validador: correctos.
- `docker compose config -q`: correcto.
- Parseo de YAML del workflow y JSON Hosting: correcto.
- `python3 .skills/security-compliance/scripts/test_secret_scan.py`: **8 passed**.
- Scanner sobre rutas acotadas de deploy, workflow, validador, pruebas y guía:
  sin secretos encontrados. Único hallazgo esperado: `mongodb-uri` en
  `tests/integration/test_news_shared_contract.py:22`, fixture temporal preexistente,
  sin credenciales. No se escaneó `keys/`. El scanner acepta un destino por
  ejecución; se corrigió una invocación inicial con varios argumentos.
- `git diff --check`: correcto. `git diff --cached --name-only`: vacío.

## Revisión de seguridad

Se aplicaron las skills locales de planificación, diagnóstico, TDD, revisión y
seguridad. La planificación permanece en `/tmp/news-firebase-task-plan.md`.

| Caso | Control y evidencia |
| --- | --- |
| Proyecto Firebase equivocado | Preflight compara proyecto cliente/Hosting; test de rechazo |
| Publicar con APIs locales | Preflight HTTPS/localhost y regresión del `.env` de Make |
| Lectura desde un origen ajeno | CORS explícito en ambos servicios; preflight positivo/negativo con MongoDB temporal |
| Identidad/rol manipulados | Tokens verificados y rol MongoDB; suite API y contrato de integración |
| Exposición de secretos | Solo rutas en scripts, scanner acotado, exclusión de artefactos Firebase/credenciales efímeras del repo y build |

## Trazabilidad DB

- [x] Modelos sincronizados: revisados mediante suites y contrato real, sin cambios.
- [x] Documentación sincronizada: guía operativa, READMEs y TODO actualizados.
- [x] Diagrama sincronizado: `07-diagrama.md` revisado; no cambian campos o relaciones.
- [x] Tests sincronizados: frontend, scripts e integración ampliados.
- [x] Makefile sincronizado: targets Hosting/check/tests y separación local/cloud.
- [x] Secrets/bootstrap sincronizados: permanecen `mongodb_uri` y `openai_api_key`;
  `setup-keys` ya contempla ambos. Bootstrap cloud y README alineados, sin archivo
  admin obsoleto. No hay nuevos secretos requeridos.
- Índices, validadores, seeders y políticas TTL: sin cambios; verificados en DB efímera.

## Pendientes, bloqueos y estado final

- Sin bloqueos para los cambios locales entregados. La configuración externa y
  prueba publicada quedan a cargo del usuario siguiendo la guía.
- Esta sesión no tiene CLIs `gcloud`/`firebase` instaladas ni un proyecto Firebase
  configurado para validar login/deploy real. Las pruebas cloud usan CLIs simuladas;
  no prueban IAM, facturación, red Atlas productiva ni OAuth de cuentas reales.
- Deben configurarse proyecto, proveedores, dominios, facturación, acceso Atlas,
  secretos y parámetros públicos antes del despliegue real. Google Sign-In nativo
  requiere un build propio, separado del portal web.
- Commit/push: ninguno. Working tree contiene únicamente los cambios descritos,
  sin staging. No se modificó historia ni se tocaron datos persistentes reales.
- Siguiente paso: seguir `docs/deploy/firebase-paso-a-paso.md`, empezar con
  `CHATBOT_PROVIDER=stub`, verificar el portal y luego habilitar IA real con precios.

## Seguimiento: guía con OpenAI desde el inicio

Por petición posterior del usuario, se actualizaron la guía paso a paso,
`docs/deploy/README.md` y `deploy/TODO_deploy.md` para desplegar directamente con
`CHATBOT_PROVIDER=openai`. Se requieren ambos secretos, modelo y precios desde
la configuración inicial. La recomendación anterior de empezar con `stub` queda
reemplazada por esta decisión.

La guía exige configurar explícitamente proveedor y precios en GitHub
`production`, porque el fallback actual del workflow sigue siendo `stub`.
Incluye comprobar resumen/explicación, `strategy=llm`, `aiUsed=true` y `aiUsage`.
No se cambiaron defaults de ejecución, código, esquemas ni secretos; esta
actualización es documental. Verificación: revisión de referencias a `stub` y
`git diff --check`; no corresponde repetir suites de código. No hubo commit,
push ni despliegue y el working tree conserva los cambios de la integración.

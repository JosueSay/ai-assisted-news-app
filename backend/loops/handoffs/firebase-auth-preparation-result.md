# Firebase Authentication, punto 1 — resultado del loop

## Objetivo

Implementar Firebase Authentication de extremo a extremo para la aplicación de noticias,
la API y el chat en modo news, manteniendo el alcance limitado al punto 1 del Proyecto 2.

## Cambios realizados

- Frontend: Firebase Auth/App JS modules; Google popup en web, OAuth Google en build nativo que entrega
  credencial a Firebase, Firebase Anonymous Auth para invitados, restauración/cierre de
  sesión y perfil resuelto por el backend. El cliente ya no persiste un perfil local como
  prueba de login.
- Backend `news`: verificación de Firebase ID tokens con `google-auth` y certificados
  públicos (audience, issuer, firma, expiración, `auth_time` y Project ID), upsert seguro
  de usuarios por `firebaseUid`, endpoint `GET /auth/me` y protección de `POST /admin/news`
  mediante `users.role` en MongoDB.
- Chat modo news: exige Firebase Bearer token, ignora/elimina la identidad declarada en el
  body y resuelve propietario de `chatSessions` desde el UID verificado. Los modos
  históricos `projection` y `novu` no cambian.
- Retirados el login/token local `/admin/login` y sus módulos/configuración de noticias.
  No se borran archivos secretos locales preexistentes ni datos de MongoDB.
- `.env`, frontend `.env.example`, Makefile, Compose, `keys/README.md`, READMEs,
  arquitectura y el documento `docs/reviews/alcance-pendiente-proyecto-2.md` sincronizados.
  No se agregó una clave de servicio: la verificación de firmas no requiere una.

## Decisiones tomadas

- Google para cuentas registradas; Firebase Anonymous Auth para mantener el modo invitado.
- `users.role` en MongoDB es la fuente de permisos admin. Un usuario nuevo siempre se crea
  como `user`; un operador debe promocionar manualmente un UID Firebase verificado.
- No se fusionan ni eliminan perfiles provisionales (`google:...`, `guest:...`,
  `local-admin:...`) ni sus datos. La relación nueva se crea por UID Firebase.
- Se conserva el esquema DB existente. `users.firebaseUid` y su índice único no cambian.
- Las rutas de lectura pública siguen públicas; `/auth/me`, el chat news y publicación
  requieren token según el contrato documentado.

## Configuración externa pendiente

El usuario debe configurar el proyecto Firebase (Project ID), habilitar Google y
Anonymous, registrar Android/iOS/web, autorizar dominios, añadir SHA-1/SHA-256 Android
y completar las variables públicas de `frontend/.env` más `NEWS_FIREBASE_PROJECT_ID`
en el `.env` raíz. No compartir client secrets, service-account JSON, tokens ni secretos.
Hasta recibir esa configuración no se pudo hacer un login real contra Firebase ni un
build EAS firmado.

Para dar rol admin: iniciar sesión una vez, comprobar el UID con la cuenta Firebase y
asignar `users.role=admin` mediante una sesión autorizada de MongoDB; el handoff no
ejecutó esa operación ni tocó una DB real.

## Comandos y verificaciones

- `python -m pytest news/tests assistant/tests -q` en venv externo: **345 passed, 1 skipped**.
- `npm run typecheck`: pasó.
- `npm test`: **15 tests passed**.
- `npx expo export --platform android`: export de Metro Android pasó (2700 módulos).
- `npx expo export --platform web`: export web pasó (2250 módulos).
- `make news-integration-test`: **1 passed** sobre MongoDB temporal efímera; verifica API,
  chat, resolución Firebase simulada, admin, esquema, índices y TTL; no usó Atlas ni DB real.
- `docker compose config -q`: pasó.
- Ruff sobre los archivos backend afectados directamente: pasó. El chequeo amplio de los
  directorios existentes señaló reglas preexistentes fuera de los archivos de este cambio;
  no se aplicaron autofixes masivos.
- Security scanner: `backend/assistant/app.py`, `frontend/src/services` y el documento de
  alcance sin hallazgos. En `backend/news` informó 9 coincidencias `mongodb-uri` en rutas
  de configuración/ejemplos/tests existentes; no se copiaron valores. Pruebas del scanner:
  8 passed.
- `git diff --check`: pasó. Enlaces Markdown locales y newline final: pasaron.
- `npm audit --omit=dev` todavía reporta 25 advisories en el árbol frontend existente
  (7 moderate, 17 high, 1 critical; principalmente Expo/Metro/RN y shell-quote). La
  instalación del SDK modular `@firebase/app`/`@firebase/auth` evitó añadir el paquete
  agregado `firebase` y sus módulos Firestore no usados; no ejecuté `npm audit fix` ni
  actualizaciones mayores de Expo/React Native por exceder este loop.

## Trazabilidad de DB

- [x] Modelos revisados; sin cambios estructurales.
- [x] Documentación sincronizada (DB, auth, bootstrap y configuración).
- [x] Diagrama revisado; sin cambio porque colecciones/campos/referencias no cambian.
- [x] Tests de backend y frontend actualizados.
- [x] Makefile/Compose y `NEWS_FIREBASE_PROJECT_ID` sincronizados.
- [x] `setup-keys` y `keys/README.md` sincronizados; no se agrega secreto Firebase.

## Bloqueos / pendientes

- Configuración de Firebase/Google Cloud por parte del usuario y comprobación real de
  Google/Anonymous en web y builds iOS/Android.
- El registro Firebase existente no convierte automáticamente las cuentas antiguas;
  cualquier asociación de datos requerirá decisión humana.

## Commit y working tree

- No se creó commit.
- `git status --short` al cierre: cambios en configuración, backend news/assistant,
  documentación, frontend y tests; se eliminaron los módulos obsoletos de auth local.
  Los archivos nuevos/no trackeados son `backend/news/firebase_auth.py`,
  `backend/news/user_accounts.py`, tres tests nuevos, `frontend/src/services/firebaseClient.ts`,
  este handoff y `docs/reviews/`. `docs/reviews/` ya estaba sin seguimiento antes del loop.
- No se tocaron archivos secretos ni se leyó su contenido; no se modificó ninguna base real.

## Ubicación de la guía (actualización documental 2026-10-18)

La guía de configuración y verificación de Firebase se conserva en
[firebase-auth-configuracion.md](../../../docs/reviews/firebase-auth-configuracion.md).
El archivo [alcance-pendiente-proyecto-2.md](../../../docs/reviews/alcance-pendiente-proyecto-2.md)
vuelve a reunir los ocho puntos seleccionados y sus tareas concretas. Esta separación
no modifica la implementación ni las decisiones/resultados históricos de este handoff.

# Firebase Authentication — configuración y verificación pendiente

Fecha: 2026-10-18.

Este documento cubre únicamente el punto 1: Firebase Authentication. Los puntos
2–8 quedan fuera de este loop.

Para configurar y desplegar el sistema actual completo, sigue la
[guía Firebase paso a paso](../deploy/firebase-paso-a-paso.md), que incluye
Hosting, Cloud Run, Atlas, CORS y comprobación del feed personalizado.

## Estado de implementación

El código de Firebase Auth está integrado en el frontend, la API de noticias y el
chat en modo news. Falta que completes la configuración de Firebase/Google Cloud
de la sección 3 y verifiques el inicio de sesión real en tus builds. No se cambió
el esquema MongoDB ni se migraron o borraron cuentas existentes.

Para DB prevalece el diseño aprobado de
[`docs/design/database/`](../design/database/README.md): MongoDB/PyMongo, base
`ai_assisted_news` y `users.firebaseUid` como UID externo único.

## 1. Qué quedó implementado

- `frontend/src/services/googleAuth.ts` usa Firebase Authentication. En web inicia
  sesión con Google mediante popup; en Android/iOS intercambia la credencial Google
  por una sesión Firebase. El invitado usa Firebase Anonymous Authentication.
- `frontend/src/services/firebaseClient.ts` inicializa Firebase y mantiene la sesión
  con persistencia web o AsyncStorage en móvil. Los ID tokens se renuevan con Firebase.
- Después del login, el frontend consulta `GET /auth/me`; el backend valida el token y
  crea/recupera `users` por el UID verificado. Un perfil local guardado no autentica.
- `backend/news/firebase_auth.py` valida Bearer ID tokens: firma, audience, issuer,
  expiración y Project ID. Usa certificados públicos; no requiere una clave JSON de
  service account ni privilegios IAM para verificar la firma.
- `POST /admin/news` exige un token válido y `users.role=admin`, consultado en MongoDB.
  La API antigua `/admin/login` y el token local se retiraron. En el chat news el
  request tampoco puede declarar un `user`, UID o rol.
- El modo news del assistant usa el mismo verificador y `users.firebaseUid`; los modos
  históricos `projection` y `novu` se mantienen sin cambios.
- Los usuarios provisionales (`google:...`, `guest:...`, `local-admin:...`) quedan
  intactos y separados. No se unen por email, nombre o coincidencia de ID.

## 2. Accesos y autorización

| Operación | Acceso |
| --- | --- |
| Feed, detalle público y catálogo de ubicaciones | Público |
| `GET /auth/me` | Firebase ID token; resuelve/crea usuario regular |
| Chat en modo news | Firebase ID token; sesión aislada por usuario MongoDB |
| `POST /admin/news` | Firebase ID token y `users.role=admin` en MongoDB |

El cliente no puede asignarse un UID o rol. Un usuario nuevo siempre se crea con rol
`user`. Para designar un admin, primero inicia sesión con la cuenta y deja que
`/auth/me` cree su usuario; luego una persona autorizada debe actualizar el rol en la
base correcta. Ejemplo para MongoDB Compass/Shell, sustituyendo el UID verificado:

```javascript
db.users.updateOne(
  { firebaseUid: "<UID de Firebase>" },
  { $set: { role: "admin", updatedAt: new Date() } }
)
```

No ejecutes esa operación sobre una base productiva sin verificar el proyecto/base y
la cuenta destino. No hay endpoint público para conceder privilegios.

## 3. Qué debes configurar en Firebase / Google Cloud

### Firebase Console

1. Crea o selecciona el proyecto Firebase y confirma su **Project ID**.
2. En **Authentication → Sign-in method**, habilita **Google** y **Anonymous**.
   Configura el email de soporte y la audiencia OAuth adecuada (interna solo para
   una organización; externa si habrá usuarios fuera de Workspace).
3. Registra tres apps Firebase:
   - Android: `com.aina.news`.
   - iOS: `com.aina.news`.
   - Web: para el portal web.
4. En Authentication → Settings, autoriza el dominio del portal. `localhost` se usa
   en desarrollo; agrega el dominio real cuando exista.
5. En la app Android añade las huellas SHA-1 y SHA-256 de las firmas que uses para
   builds de desarrollo y distribución (incluidas las firmas EAS que correspondan).
   En EAS puedes consultarlas desde `npx eas-cli@latest credentials --platform android`;
   registra las huellas de las keystores que realmente usarás, no compartas sus claves.

### Configuración local del repositorio

Pon el **mismo Project ID** en `.env` de la raíz:

```dotenv
NEWS_FIREBASE_PROJECT_ID=tu-project-id
```

En `frontend/.env`, copia la configuración pública de la app Web que muestra Firebase
Console, además de los client IDs OAuth nativos:

```dotenv
EXPO_PUBLIC_FIREBASE_API_KEY=...
EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=tu-project-id.firebaseapp.com
EXPO_PUBLIC_FIREBASE_PROJECT_ID=tu-project-id
EXPO_PUBLIC_FIREBASE_APP_ID=...
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=...
EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID=...
```

Los valores `EXPO_PUBLIC_*` son configuración pública de cliente. **No** pongas allí
client secrets, service-account JSON, contraseñas, ID tokens ni claves privadas.
Firebase ID tokens se verifican con certificados públicos; no tienes que crear ni
descargar una service-account key ni conceder un rol IAM para esta verificación.

### Información que necesito después

Compárteme solo información no secreta para comprobar el wiring:

- Project ID de Firebase.
- Que habilitaste Google y Anonymous.
- Si los usuarios podrán ser externos a Workspace y el dominio del portal, si ya existe.
- Confirmación de que configuraste los valores públicos de Firebase y OAuth en los `.env`
  locales (no hace falta pegar aquí sus valores).
- Huellas SHA-1/SHA-256 que quedaron registradas, si quieres que verifiquemos un build.

No compartas secretos, tokens de login ni el contenido de `keys/`.

## 4. Decisiones fijadas en el código

- Google es el proveedor de cuentas registradas; el modo invitado acordado usa Firebase
  Anonymous Auth.
- `users.role` en MongoDB es la fuente de autorización admin. El backend nunca toma el
  rol de claims o campos controlables por el cliente.
- Los perfiles provisionales y sus sesiones no se asocian automáticamente a Firebase.
- El esquema DB no cambió. El UID Firebase es el identificador externo y se mantiene el
  índice único aprobado de `users.firebaseUid`.
- La API de lectura sigue siendo pública; `/auth/me`, publicación y chat news requieren
  token según la tabla de acceso.

## 5. Seguridad y comprobación

| Riesgo | Control implementado |
| --- | --- |
| Suplantar UID/rol desde cliente | Chat rechaza campos extra; backend usa claims verificados y rol MongoDB. |
| Token inválido, vencido o de otro proyecto | Valida firma, `aud`, `iss`, expiración y `NEWS_FIREBASE_PROJECT_ID`; responde 401. |
| Cuenta común publica | `/admin/news` consulta `users.role` en servidor y responde 403 si no es admin. |
| Fusión incorrecta de perfiles antiguos | No hay migración ni asociación automática. |
| Filtrar clave de cuenta de servicio | La verificación no usa service-account keys; no se añadió ningún secreto. |

Las pruebas automatizadas usan verificadores simulados y no requieren credenciales
reales. La autenticación real en web/iOS/Android queda pendiente hasta que completes
tu proyecto y hagas un build nativo propio; Expo Go no sirve para comprobar Google
Sign-In nativo.

## 6. Cómo probar después de configurar Firebase

1. Ejecuta `make env-local` solo si quieres generar/reemplazar el `.env` raíz; luego
   configura `NEWS_FIREBASE_PROJECT_ID` en ese archivo. Completa `frontend/.env` con
   los valores públicos indicados arriba.
2. Ejecuta `make db-bootstrap` y luego `docker compose up -d --build news-api chatbot frontend`.
3. Inicia sesión con Google y como invitado; ambos deben llegar al feed/chat.
4. Para probar administración, localiza el UID de Firebase de la cuenta que ya inició
   sesión y asigna `users.role=admin` mediante una sesión segura de MongoDB. Vuelve a
   iniciar sesión y comprueba publicación. No cambies la colección o base por accidente.
5. Comprueba que una cuenta normal obtiene 403 al publicar y que editar el body para
   incluir `user`, `firebaseUid` o `role` en el chat se rechaza.

La configuración en consola por sí sola no basta: el frontend, la API y el chat deben
estar usando el mismo Project ID.

# Frontend

App Expo + React Native + TypeScript con Firebase Auth y feed personalizado desde
`news-api` y MongoDB. La web funciona en navegadores de escritorio y teléfono.
Google Sign-In nativo requiere un build propio; Expo Go solo permite comprobar
los recorridos compatibles con su cliente, como el invitado Firebase.

Para publicar el portal, sigue la [guía Firebase paso a paso](../docs/deploy/firebase-paso-a-paso.md).
`make firebase-check-config` valida los parámetros y `make firebase-deploy` genera
el export web y lo publica en Hosting.

## Ejecutar

```bash
cd frontend
npm install
npm start
```

Esto abre el Metro Bundler con un código QR en la terminal:

- **Android**: instalá [Expo Go](https://play.google.com/store/apps/details?id=host.exp.exponent)
  y escaneá el QR desde la app.
- **iPhone**: instalá [Expo Go](https://apps.apple.com/app/expo-go/id982107779)
  y escaneá el QR con la Cámara del sistema (te ofrece abrirlo en Expo Go).
- Ambos dispositivos deben estar en la misma red Wi-Fi que la computadora. Si
  no conectan, corré `npm start -- --tunnel`.

También podés previsualizar en el navegador con `npm run web`.

## Ejecutar con Docker Compose

Desde la raiz del proyecto:

```bash
docker compose up --build frontend
```

Compose construye el contenedor del frontend, instala dependencias con `npm ci`
y publica Metro en `http://localhost:8081`. El host de Expo es configurable:

```bash
EXPO_HOST=tunnel docker compose up --build frontend
```

En modo `lan`, si el QR muestra una IP tipo `172.x.x.x`, Expo esta anunciando la
red interna de Docker. Puedes forzar la IP local real de tu computadora:

```bash
REACT_NATIVE_PACKAGER_HOSTNAME=192.168.1.50 docker compose up --build frontend
```

Si configuras Google Sign-In real, crea `frontend/.env` desde `.env.example`;
Compose lo carga automaticamente cuando existe.

## Feed conectado a MongoDB local

Desde la raíz del proyecto:

```bash
make db-bootstrap
make db-verify
docker compose up -d --build news-api chatbot frontend
```

Servicios esperados:

```text
news-mongo   http://localhost:27018
news-api     http://localhost:8020
frontend     http://localhost:8081
```

El frontend consume `EXPO_PUBLIC_NEWS_API_BASE_URL`, que en el `.env` raíz queda como:

```dotenv
EXPO_PUBLIC_NEWS_API_BASE_URL=http://localhost:8020
```

Si la API no responde, la app muestra un estado de error. No existe un dataset
local de respaldo en el frontend.

## Qué vas a ver

Después de iniciar sesión, la app móvil abre el asistente. En la web de escritorio
abre el feed; en la web móvil, sin una ruta explícita, abre el asistente. Los
enlaces directos a noticias y las pestañas Inicio/Guardados siguen disponibles.
La navegación inferior reserva su espacio y se oculta al abrir el teclado nativo;
el historial móvil se despliega sin desplazar el campo de escritura.

Al abrir la app aparece la pantalla de autenticación:

- **"Continuar como invitado"** — crea una sesión Firebase Anonymous; requiere
  habilitar el proveedor Anonymous en el proyecto.
- **"Iniciar sesión con Google"** — obtiene una sesión Firebase Authentication.
  Las cuentas admin usan este mismo botón y reciben permisos solo si
  `users.role` tiene `admin` en el servidor.
- No hay acceso admin por contraseña local ni token de frontend.

## Configurar Firebase Authentication

1. En Firebase Console, habilita los proveedores **Google** y **Anonymous**.
2. Registra las apps Android e iOS con el mismo ID de [`app.json`](app.json):
   `com.aina.news`. Registra además una app web para el acceso web.
3. En la app Android agrega las huellas SHA-1 y SHA-256 de las firmas que usarás
   para development y distribución. Habilita los dominios autorizados del portal.
4. Copia la configuración pública de Firebase Web a `frontend/.env`:

   ```dotenv
   EXPO_PUBLIC_FIREBASE_API_KEY=...
   EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=...firebaseapp.com
   EXPO_PUBLIC_FIREBASE_PROJECT_ID=...
   EXPO_PUBLIC_FIREBASE_APP_ID=...
   ```

5. Android usa `react-native-nitro-google-signin` con Credential Manager. Guarda
   el `google-services.json` actualizado de Firebase en `frontend/`, con el cliente
   Android de la firma del APK y un cliente OAuth Web de tipo 3. El plugin en
   `app.json` incorpora el archivo y `webClientId: "autoDetect"` obtiene ese cliente
   Web. No necesita `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID`. El ID token de Google
   se intercambia por una sesión Firebase; los backends siguen recibiendo tokens Firebase.

   Para el flujo iOS existente (todavía pendiente de prueba), configura:

   ```dotenv
   EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID=...
   ```

   Los valores de Firebase Web y los client IDs son configuración pública de
   cliente; **no** agregues client secrets, service-account JSON ni tokens.
6. En el `.env` de la raíz configura el mismo `NEWS_FIREBASE_PROJECT_ID`. La API y
   el chat validan firma, issuer, audience, proyecto y expiración del ID token.
   La verificación usa certificados públicos y no requiere una clave de servicio.
7. En la base `ai_assisted_news`, una cuenta autorizada puede pasar a admin solo
   después de que la persona haya iniciado sesión y exista `users.firebaseUid`:

   ```javascript
   db.users.updateOne(
     { firebaseUid: "<UID de Firebase>" },
     { $set: { role: "admin", updatedAt: new Date() } }
   )
   ```

   Hazlo desde una sesión administrativa segura de MongoDB; nunca aceptes el rol
   desde el request del frontend.

8. Para un APK Android instalable, sigue la
   [guía de Android paso a paso](../docs/deploy/android-apk-paso-a-paso.md).
   Incluye cuenta Expo, variables del build y firma. Google nativo necesita
   configuración OAuth y validación en dispositivo; habilitar Google para la
   web no completa esa configuración. El perfil `apk` no usa Expo Go ni Metro.

La sesión Firebase restaura el acceso; el backend crea/recupera el usuario por UID.
Los usuarios provisionales `google:...`, `guest:...` y `local-admin:...` no se
fusionan automáticamente ni se borran.

## Comandos

```bash
npm run typecheck   # tsc --noEmit
npm test            # vitest run
```

## Estructura

```text
frontend/
├── App entry: index.ts -> src/App.tsx (enrutado simple por useState)
├── src/
│   ├── App.tsx           # composición general y estado de sesión
│   ├── theme.ts           # colores y espaciado compartidos
│   ├── types.ts
│   ├── components/        # UI reutilizable (AppButton, ArticleCard)
│   ├── features/
│   │   ├── auth/           # LoginScreen
│   │   └── news/           # NewsFeedScreen
│   └── services/
│       ├── googleAuth.ts   # Firebase Auth: Google web/native y guest anonymous
│       ├── firebaseClient.ts # configuración y persistencia Firebase
│       └── newsService.ts  # feed desde API local/MongoDB
└── tests/
    └── newsService.test.ts
```


## Contrato de datos

`src/generated/newsContract.ts` se genera desde `backend/news/topics.py` y sus
enums: no se edita a mano. Desde la raíz ejecutar `make news-contract` y
`make news-contract-check`. La app conserva todos los topics de cada noticia,
sus fuentes y estado de verificación, y la declaración de imagen asistida por IA.
El detalle de una cita se consulta por slug cuando no está cargado en el feed.
La pestaña Asistente usa `EXPO_PUBLIC_ASSISTANT_API_BASE_URL` (8010); en un
móvil físico ambas URLs de API deben apuntar a la IP LAN de la computadora.

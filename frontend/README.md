# Frontend

App móvil (Expo + React Native + TypeScript) con login de Google y un feed de
noticias de demostración. Corre igual en iPhone y Android sin necesitar Mac
ni cuenta de Apple para probarla, usando la app **Expo Go**.

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

## Qué vas a ver

Al abrir la app aparece la pantalla de login con dos botones:

- **"Continuar como invitado"** — entra directo, sin configuración previa.
  Es la forma más rápida de mostrar la experiencia completa (feed de
  noticias, header con usuario, logout) en ambos teléfonos ahora mismo.
- **"Iniciar sesión con Google"** — queda deshabilitado hasta configurar
  credenciales reales (ver abajo). Sin configurar, el hint en pantalla lo
  explica.

## Google Sign-In real

El código ya implementa el flujo completo (Authorization Code + PKCE contra
Google, sin exponer client secret) en
[`src/services/googleAuth.ts`](src/services/googleAuth.ts). Para activarlo:

1. En [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   creá dos **OAuth client ID**: uno tipo **Android** (con el package
   `com.aina.news` de [`app.json`](app.json) y el SHA-1 de tu build) y uno
   tipo **iOS** (con el bundle id `com.aina.news`).
2. Copiá `.env.example` a `.env` y completá `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID`
   y `EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID`.
3. Generá un **dev client propio** con EAS (build en la nube, no requiere
   Mac):
   ```bash
   npx eas-cli@latest build --profile development --platform android
   ```
   Instalá el APK resultante en el Android en lugar de Expo Go.

**Por qué no alcanza con Expo Go:** los client ID de tipo Android/iOS de
Google validan el paquete/bundle id y la firma de la app real, no el
contenedor genérico de Expo Go — por eso el botón de Google solo completa el
login dentro de tu propio dev client.

**Sobre iPhone sin Mac:** Expo Go te deja mostrar toda la interfaz (login de
invitado, feed, navegación) en un iPhone real sin Mac ni cuenta de Apple de
pago. Para instalar un dev client propio (necesario para Google real) en un
iPhone físico, Apple exige firma de código: o una Mac con Xcode, o una cuenta
de Apple Developer de pago ($99/año) para distribución ad-hoc/TestFlight. Sin
eso, el login de invitado es la vía para demostrar la experiencia en iOS.

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
│       ├── googleAuth.ts   # OAuth con Google + sesión de invitado
│       └── newsService.ts  # feed de noticias (demo hoy, reemplazable)
└── tests/
    └── newsService.test.ts
```

# Google nativo Android

## Objetivo y autorización

Reemplazar el acceso Google por navegador de Android tras el reporte de
`400: invalid_request`. El código previo usaba AuthSession con retorno `ainews://`;
el código 400 por sí solo no demuestra la causa específica del rechazo.
El usuario autorizó explícitamente integrar Nitro: «si hazlo».

## Cambios

- `frontend/package.json` y lock: Nitro Google Sign-In 2.3.0 y Nitro Modules 0.37.1.
- `frontend/src/services/androidGoogleSignIn.android.ts`: carga perezosa del SDK,
  `configure({ webClientId: "autoDetect" })`, validación de Play Services,
  selector explícito de cuentas y Google ID token hacia Firebase
  `GoogleAuthProvider.credential` / `signInWithCredential`. Cancelar no crea sesión.
- `frontend/src/services/androidGoogleSignIn.ts`: implementación alternativa para
  web/iOS, sin importar el SDK nativo. Limpieza nativa al cerrar sesión solo si
  se cargó el módulo; un fallo de limpieza no impide cerrar Firebase.
- `frontend/src/services/googleAuth.ts`: Android usa el adaptador nativo;
  web conserva signInWithPopup e iOS conserva su AuthSession anterior.
  El perfil y rol siguen obteniéndose del backend con Firebase ID token.
- `frontend/app.json`: plugin Nitro, googleServicesFile Android y versionCode 2.
  Conservados owner/projectId EAS, paquete y demás cambios previos del usuario.
- `frontend/google-services.json`: archivo público creado por el usuario, ya
  presente antes de esta tarea, usado sin modificarlo. Incluye cliente OAuth Web
  y Android; no es una clave de cuenta de servicio. Debe viajar al build EAS.
- `frontend/.env.example`, README y guía Android: instrucciones del flujo nativo.
  EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID ya no se utiliza; no hace falta otra
  variable EAS. Se mantienen las seis variables Firebase/APIs existentes.
- Tests nuevos androidGoogleSignIn y googleAuth: SDK/Firebase, cancelación,
  errores, perfil verificado, logout, invitado y conservación de web/iOS.

## Comandos y resultados

- Revisadas skills planning-with-files (plan en /tmp), TDD y code-reviewer.
- `npm install react-native-nitro-google-signin@2.3.0 react-native-nitro-modules --ignore-scripts`:
  dos dependencias añadidas. npm reportó vulnerabilidades del árbol; no se aplicó
  un audit fix ni se evaluó un cambio general de dependencias fuera del alcance.
- Prueba del adaptador antes de implementarlo: falla por módulo inexistente.
- `npm test`: 9 archivos, 51 pruebas OK (15 nuevas de auth).
- `npm run typecheck`: OK.
- `npx expo export --platform web --platform android --clear --output-dir /tmp/news-google-native-export`:
  OK, export web y bundle Hermes Android. Nitro está en Android, ausente en web.
- Prebuild aislado bajo `/tmp/news-google-native-prebuild-*`, sin instalar:
  `EXPO_NO_DOTENV=1 expo prebuild --platform android --no-install`: OK. Copiados
  solo archivos de configuración/paquetes públicos y enlace a node_modules.
  Verificado Google Services JSON copiado, classpath y plugin Gradle aplicado.
  Aviso no bloqueante existente: expo-system-ui ausente para userInterfaceStyle.
- `expo-modules-autolinking react-native-config --platform android --json`:
  ambos módulos tienen configuración Android.
- Inspección inicial de autolinking sin --json produjo salida de objeto JS no
  parseable; corregida con --json. Una comprobación de lock usó ruta relativa
  equivocada y se repitió desde frontend con resultado correcto.
- `git diff --check`: OK; revisados cambios sin contenido secreto.

## Límites y siguiente paso

No se compiló Gradle/APK, no se ejecutó build EAS remoto ni se probó el teléfono.
Las pruebas de SDK son simuladas; el prebuild/export no sustituyen esa validación.
Ejecutar `make android-apk` desde la raíz con la misma firma existente. Instalar
el APK nuevo, cerrar sesión invitada y probar selector Google, cancelación,
sesión persistente, perfil/feed/chat y logout. Si funciona, actualizar el enlace
web al nuevo build; el enlace actual sigue apuntando al primer APK compartido.

iOS no está configurado para Nitro ni validado físicamente. El plugin añade
mods iOS pero el proyecto solo aporta Google Services Android en este alcance.
Para iOS se necesitará un trabajo específico de configuración y prueba.

Sin cambios DB, secretos, bootstrap o backend. No se leyó ni modificó keys/ ni
se cambió el .env local. Sin commit, push, deploy o cambios de historia Git.
Working tree conserva además preparación APK, descarga web y vinculación EAS
de turnos anteriores; esta tarea modifica app.json, package/lock, googleAuth,
.env.example, README, guía y añade adaptadores, tests y este handoff.

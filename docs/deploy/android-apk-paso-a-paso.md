# Android: primer APK instalable

Estado: el usuario vinculó Expo, configuró el entorno y generó el primer APK.
Compartió el build `33425211-31ac-4a45-bda4-e33dcbcbe6fc`. La pantalla de entrada
web incluye un enlace a esa página de instalación de Expo; requiere publicar
estos cambios en Hosting. No se verificó externamente una URL directa al APK
ni todas las funciones en un teléfono. Esto no modifica Cloud Run.

## 1. Crear cuenta e iniciar sesión

Crea tu cuenta en <https://expo.dev/signup>. Desde la raíz del repositorio:

```bash
cd frontend
npx eas-cli@latest login
npx eas-cli@latest whoami
```

Introduce tus credenciales únicamente en el CLI o en Expo, nunca en el chat.
Usamos `npx` para evitar problemas del PATH con instalaciones globales.

## 2. Vincular el proyecto

Dentro de `frontend`:

```bash
npx eas-cli@latest init
```

Crea el proyecto en tu cuenta cuando lo solicite. El CLI vinculará un ID real en
la configuración Expo. Conserva `android.package=com.aina.news` de `app.json` y
el perfil `apk` de `eas.json`. No inventes un `projectId`.

## 3. Configurar los valores públicos del build

En el proyecto de Expo abre **Environment variables** y crea estas variables
para el entorno **production**, con visibilidad **Plain text**. Copia los valores
que ya utilizas en `frontend/.env` para el despliegue real:

| Nombre | Valor que debes usar |
| --- | --- |
| `EXPO_PUBLIC_FIREBASE_API_KEY` | Configuración pública de Firebase Web |
| `EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN` | Dominio Firebase Auth del proyecto |
| `EXPO_PUBLIC_FIREBASE_PROJECT_ID` | Proyecto Firebase existente |
| `EXPO_PUBLIC_FIREBASE_APP_ID` | ID de la app Firebase Web que usa el cliente actual |
| `EXPO_PUBLIC_NEWS_API_BASE_URL` | URL HTTPS de `news-api` en Cloud Run |
| `EXPO_PUBLIC_ASSISTANT_API_BASE_URL` | URL HTTPS de `news-chatbot` en Cloud Run |

El entorno `production` de GitHub y el de Expo son configuraciones independientes.
El `.env` local ignorado por Git no estará disponible en el compilador remoto.
Todo `EXPO_PUBLIC_*` queda visible en la aplicación. No subas `keys/`, la clave
OpenAI, URI MongoDB, tokens ni claves privadas: siguen en el backend.

## 4. Compilar y conservar la firma

Regresa a la raíz del repositorio y ejecuta:

```bash
cd ..
make android-apk
```

Si pregunta por credenciales Android, permite que EAS genere y administre un
keystore nuevo si no tienes una firma previa para esta aplicación. Si ya existe
una firma de distribución, reutilízala. Conserva la misma firma para futuras
actualizaciones. No descargues ni agregues credenciales al repositorio.

El perfil genera un **APK**, instalable directamente. No requiere Expo Go ni un
servidor Metro. Espera la finalización del build y abre el enlace que entregue EAS.
La validación local de TypeScript/export no sustituye esta compilación nativa.

## 5. Instalar y comprobar el primer build

Abre el enlace del APK desde Android, descárgalo y permite la instalación desde
ese navegador cuando Android lo solicite. Comprueba:

- Abre sin Metro ni la computadora encendida.
- “Continuar como invitado” inicia sesión con Firebase Anonymous.
- Feed, detalle y chat funcionan con los backends desplegados.
- Cerrar y volver a abrir conserva la sesión.

Si una variable pública estaba equivocada, corrígela en EAS y genera otro APK.
Los cambios del cliente necesitan un build nuevo en este flujo; Hosting publica
solo la web. Para actualizar una instalación, conserva paquete y firma.
EAS gestiona el versionCode remoto y lo incrementa automáticamente; el
versionCode 3 de app.json sirve como valor inicial si aún no existe uno remoto.
`expo.version` es el nombre de versión visible y se cambia manualmente cuando corresponda.

## 6. Completar Google nativo antes de distribuir a todos

La configuración web de Google no garantiza el acceso desde Android. Registra en
Firebase la app Android con paquete `com.aina.news`, agrega las huellas SHA-1 y
SHA-256 del certificado del build (consultables en las credenciales de EAS) y
descarga de nuevo `google-services.json`. Colócalo en
`frontend/google-services.json`. Debe incluir el cliente Android para esa firma y
un cliente OAuth Web (`client_type: 3`). Es configuración pública del cliente,
no una clave privada de cuenta de servicio. Asegura que esté disponible al subir
el proyecto a EAS; el archivo actual no está excluido por Git.

Android ahora usa `react-native-nitro-google-signin` y `react-native-nitro-modules`.
El plugin de Expo incorpora Google Services en Gradle y el SDK detecta el cliente
Web de ese archivo. No requiere agregar otra variable a EAS. La antigua
`EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID` puede permanecer, pero ya no se utiliza.
No usa el navegador ni el retorno `ainews://` para Google en Android.

Genera otro APK con `make android-apk`, conservando la firma existente. El código
parte de `versionCode: 3` y EAS gestiona los siguientes números remotamente. Instala
el APK encima del anterior y cierra la sesión invitada para probar Google.
Comprueba selección y cancelación de cuenta, perfil/feed, cierre de sesión y
persistencia al reiniciar. El rol admin sigue viniendo del backend por UID Firebase.
La app móvil abre el asistente después del acceso. Comprueba que puedes escribir
con respuestas largas y con el teclado abierto, y que Inicio y Guardados siguen
accesibles al cerrar el teclado. El historial se abre encima del contenido sin
desplazar el campo de entrada; los filtros se ocultan temporalmente al escribir.
Después de probarlo, sustituye el enlace de descarga web por el del build nuevo.

El módulo se carga solo al pulsar Google en Android. Expo Go no incorpora ese
módulo y no sirve para probar ese acceso: usa el APK firmado. iOS conserva su
flujo anterior; esta integración y sus pruebas se limitan a Android.

## 7. Poner la descarga en la página

La pantalla de entrada web incluye “Descargar para Android”, que abre la ficha
del build compartido por el usuario. Desde ahí se descarga/instala el APK.
Se puede usar también desde una computadora para abrir la instalación en el
teléfono. No aparece dentro de la app nativa y funciona sin iniciar sesión.

El pipeline espera el APK, valida su URL y exporta la web con
`EXPO_PUBLIC_ANDROID_DOWNLOAD_URL`; el botón descarga directamente ese artefacto.
Actívalo siguiendo la [guía Android automática](android-automatico-paso-a-paso.md).
Un build manual en EAS no actualiza el botón por sí solo. Para Hosting manual,
define la URL pública del APK en esa variable de frontend/.env antes de ejecutar
`make firebase-deploy`. Sin variable se conserva el enlace inicial de Expo.
iOS sigue pendiente.

## Referencias oficiales

- [Primer build y cuenta Expo](https://docs.expo.dev/build/setup/)
- [Perfil APK](https://docs.expo.dev/build-reference/apk/)
- [Variables remotas EAS](https://docs.expo.dev/eas/environment-variables/)
- [Credenciales administradas](https://docs.expo.dev/app-signing/managed-credentials/)
- [Google en Expo](https://docs.expo.dev/guides/google-authentication/)
- [Plugin Nitro para Expo](https://react-native-nitro-google-sign-in.github.io/docs/setup/expo/)
- [Restricciones OAuth de aplicaciones nativas](https://developers.google.com/identity/protocols/oauth2/native-app)

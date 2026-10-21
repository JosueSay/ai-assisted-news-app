# Preparación del APK Android

## Objetivo y estado

Preparar Android antes de iOS y de agregar la descarga a la web, por instrucción
humana. Preparación local terminada; APK firmado y distribución pendientes.
El usuario indicó que todavía no tiene cuenta Expo.

## Cambios y decisiones

- `frontend/eas.json`: perfil `apk`, distribución interna, entorno production,
  APK de release con versión local. No se inventó un ID de proyecto EAS.
- `Makefile`: `make android-apk` llama EAS desde frontend y evita cargar el
  `.env` raíz de Compose, igual que las tareas cloud existentes.
- `docs/deploy/android-apk-paso-a-paso.md`: cuenta, vinculación, seis variables
  públicas remotas, firma administrada, instalación, prueba y límites de Google.
- `frontend/README.md`: sustituida instrucción de un perfil development inexistente.
- `docs/deploy/README.md`: enlaces y comando Android.
- No se añadieron dependencias, credenciales locales ni cambios de base de datos.
  Se usaron las skills planning-with-files y code-reviewer; TDD se revisó y no
  se añadió un test que solo duplicase configuración estática.

## Verificaciones

- `npm run typecheck`: OK.
- `npx expo export --platform android --clear --output-dir /tmp/news-android-release-check`:
  OK, bundle Hermes Android y 32 assets. No demuestra que Gradle compile ni que
  Firebase/Google funcionen en un dispositivo.
- `make -n android-apk`: comando correcto, sin solicitar build remoto.
- Parse JSON del perfil: OK.
- `make deploy-test`: 7 pruebas OK.
- `git diff --check`: OK; revisión del diff y archivos nuevos sin secretos.

## Pendientes para continuar

1. Usuario crea cuenta Expo e inicia sesión personalmente con EAS CLI.
2. Vincula el proyecto con `eas init` y configura variables production en EAS.
3. Ejecuta `make android-apk`; permite firma administrada si no existe una previa.
4. Instala y prueba acceso invitado, sesión persistente, feed y chat reales.
5. Google nativo usa AuthSession/esquema propio, sujeto a restricciones OAuth
   Android. Registrar paquete/huellas/Client ID y verificar en teléfono; si falla,
   evaluar integración nativa con decisión humana antes de agregar dependencia.
6. Con artefacto real probado, publicar una URL de versión y agregar descarga web.
   iOS y automatización móvil quedan pendientes.

No se leyó ni modificó contenido secreto de `keys/`; no se compiló remotamente,
publicó, creó commit ni hizo push. Working tree con los archivos de
configuración/documentación indicados y este handoff (tres modificados y tres
nuevos en total). DB: modelos, diseño, diagrama, tests DB y secretos/bootstrap
no requieren cambios.

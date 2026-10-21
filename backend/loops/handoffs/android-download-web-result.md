# Descarga Android desde la web

## Objetivo

Agregar acceso al primer build Android compartido por el usuario:
`33425211-31ac-4a45-bda4-e33dcbcbe6fc`, cuenta Expo donmathiuz.

## Cambios y decisiones

- `frontend/src/components/AndroidDownload.web.tsx`: enlace HTML accesible,
  con estilos existentes, destino exacto proporcionado y texto que explica que
  abre la página de instalación Expo. No requiere iniciar sesión en AI News.
- `frontend/src/components/AndroidDownload.tsx`: no muestra descarga dentro de
  la app instalada; Metro selecciona la implementación web para Hosting.
- `frontend/src/features/auth/LoginScreen.tsx`: enlace bajo el acceso; ScrollView
  permite llegar a los controles si la tarjeta excede la altura disponible.
- `frontend/tests/androidDownload.test.tsx`: enlace público con navegación
  por teclado, explicación de destino y ausencia en la implementación nativa.
- `docs/deploy/android-apk-paso-a-paso.md`: estado actualizado y publicación.

Se conserva el enlace al build, no una URL de APK inventada. La ficha no pudo
consultarse con web ni extraerse desde HTML; consulta pública de API devolvió
403. No se utilizaron credenciales ni se accedió a secretos para resolverla.
El usuario informó que completó instalación; no se verificaron independientemente
feed/chat/Google en un teléfono ni acceso externo a la descarga de Expo.

## Verificación y límites

- Skill UI: ui-ux-pro-max, búsqueda enfocada en accesibilidad de enlaces;
  estilos semánticos existentes, foco nativo del enlace, alto mínimo 48 px.
- Skills locales TDD y code-reviewer aplicadas: prueba antes del componente,
  revisión de cambios y límites de navegación.
- `npm test`: 7 archivos, 36 pruebas OK.
- `npm run typecheck`: OK.
- `npx expo export --platform web --clear --output-dir /tmp/news-android-download-web`:
  OK; bundle incluye el build compartido.
- `git diff --check`: OK.
- No se realizó inspección visual en navegador ni pruebas físicas Android.

## Pendientes y estado Git

Publicar Hosting con `make firebase-deploy` o mediante el pipeline después de
integrar los cambios a main. No se creó commit ni se hizo push ni deploy.
Conservar los cambios previos del usuario en app.json (vinculación EAS) y los
archivos de preparación APK. Working tree con esos cambios previos más los
componentes, prueba, LoginScreen, guía y este handoff; sin cambios en secretos.
No cambian DB, modelos, validaciones, diagrama, seeders o bootstrap de secretos.
iOS, descarga directa de artefacto y pipeline de APK quedan pendientes.

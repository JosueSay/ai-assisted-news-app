# Asistente principal y composición móvil

## Objetivo

Corregir el chat móvil donde la navegación inferior tapa el campo de escritura,
y abrir el asistente como pantalla principal después del acceso.

## Causa y cambios

La barra inferior tenía position absolute, pero el contenedor del chat ocupaba
todo el alto disponible sin descontarla. El feed sí agregaba espacio inferior,
por lo que el defecto era especialmente visible al abrir una conversación larga.
El encabezado del chat tampoco limitaba el ancho del título junto al historial.

- `frontend/src/features/news/NewsFeedScreen.tsx`: navegación en flujo normal,
  contenido con minHeight 0, sin padding duplicado del feed. Eventos Keyboard
  nativos ocultan temporalmente la navegación y pasan su estado al chat.
  Android/iOS nativos abren chat; web móvil sin hash abre chat, escritorio sigue
  en home. Rutas explícitas y hashchange se conservan. Marca móvil vuelve al chat.
- `frontend/src/features/chat/ChatScreen.tsx`: título adaptable, historial móvil
  superpuesto con altura limitada en lugar de desplazar todo el chat. Oculta
  filtros/contexto al abrir teclado móvil o en ventanas muy bajas (<450 px).
  El estado y contenido de la conversación se conservan; composer fuera del
  scroll de mensajes. Chips con alto mínimo 44 y placeholder móvil más corto.
- `frontend/app.json`: softwareKeyboardLayoutMode resize y versionCode 3 para
  actualizar una posible instalación previa de la versión 2 de Google nativo.
- `frontend/tests/newsFeedReading.test.tsx`: tres casos de entrada móvil,
  apertura/cierre del teclado, navegación y conservación de enlaces/escritorio.
- README frontend y guía Android actualizados.

## Verificación

- Skills systematic-debugging, test-driven-development y ui-ux-pro-max aplicadas;
  revisión manual de diff siguiendo code-reviewer. Plan de trabajo en /tmp.
- Test antes del cambio: dos casos fallan porque Android/web móvil abren feed.
- `npm test`: 9 archivos, 54 pruebas OK, incluidas lecturas y Google nativo previos.
- `npm run typecheck`: OK.
- Export limpio web/Android y export final tras ajustes responsive: OK.
  Resultado final `/tmp/news-mobile-chat-final-export`.
- Prebuild Android aislado bajo `/tmp/news-mobile-chat-prebuild-*`: OK,
  AndroidManifest usa adjustResize. Aviso existente expo-system-ui no bloqueante.
- Chromium/Playwright con componentes reales vía react-native-web, fuentes
  reales y servicios/Firebase simulados (sin conexión backend ni llamadas IA):
  390x844, 320x568, 844x390, 1280x800. En todos: input dentro de viewport, sin
  superposición ni overflow horizontal; escribir, enviar, recibir respuesta
  local y limpiar draft funcionan. Abrir historial móvil permite seguir escribiendo.
- Capturas inspeccionadas en /tmp: news-mobile-chat-320x568.png,
  news-mobile-chat-844x390.png; otras resoluciones también capturadas.
- Fixture temporal ignorada en `frontend/.expo/mobile-chat-preview/`; script
  `/tmp/news-mobile-chat-browser.cjs`. No se agrega dependencia de pruebas.
  SafeAreaProvider se sustituye solo en esa fixture web por vistas sin insets.
  Se corrigieron alias de SVG/web y variables process de la fixture para Vite;
  no se modificó código de producción para habilitar el preview.
- `git diff --check`: OK. Servidor temporal cerrado al terminar la comprobación.

## Límites y siguiente paso

No se ejecutó APK ni teclado físico Android/iOS; eventos de teclado se prueban
simulados, y navegador confirma distribución/entrada de texto, no el IME nativo.
No se verificó Dynamic Type máximo en un dispositivo. Compilar con
`make android-apk`, conservar firma e instalar sobre la versión anterior; probar
Google, chat y teclado reales antes de actualizar el enlace de descarga.
Web requiere publicar Hosting para recibir estos cambios.

Sin cambios DB, secretos ni servicios backend. Modelos/diseño/diagrama/seeders/
bootstrap no afectados. No se leyó keys/, no hubo commit, push ni deploy.
Working tree conserva cambios anteriores de EAS/Google/descarga y añade estos
ajustes de chat, navegación, pruebas, documentación y handoff.

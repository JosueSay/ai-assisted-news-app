# Desplegar AI News con Firebase, Cloud Run y MongoDB Atlas

Actualizado: 2026-10-20. Ejecuta los comandos desde la raíz del repositorio, salvo
cuando se indique otra carpeta. Sustituye los ejemplos por los datos de tu proyecto.

## 1. Qué vas a desplegar

| Componente | Destino | Función |
| --- | --- | --- |
| Frontend Expo web | Firebase Hosting | Login, feed, detalle, preferencias y chat |
| Identidad | Firebase Authentication | Google y usuarios invitados |
| API `news-api` | Google Cloud Run | Perfil, feed personalizado, lecturas y administración |
| Assistant en modo news | Google Cloud Run | Chat de noticias autenticado |
| Base `ai_assisted_news` | MongoDB Atlas | Noticias, perfiles, intereses y sesiones |

El script `deploy/gcp/deploy.sh` publica los dos servicios Python. El comando
`make firebase-deploy` publica el frontend. Hosting sirve archivos estáticos;
las peticiones del navegador van a las URLs HTTPS de Cloud Run. Se conserva la
arquitectura MongoDB/PyMongo existente, sin configurar Firestore ni Realtime Database.

El chatbot se despliega con `CHATBOT_PROVIDER=openai` desde el primer deploy.
Necesitas una clave OpenAI válida y los precios del modelo configurados antes
de publicar los backends.

## 2. Elegir el proyecto y habilitar facturación

1. Abre [Firebase Console](https://console.firebase.google.com/).
2. Selecciona tu proyecto. Si ya tienes un proyecto Google Cloud, agrega Firebase
   a ese mismo proyecto desde la consola.
3. En **Configuración del proyecto → General**, identifica el **ID del proyecto**.
   Usa ese ID, no el nombre visible ni el número de proyecto.
4. Para esta guía, usa el mismo proyecto para Auth, Hosting y Cloud Run.
5. Vincula una cuenta de facturación. Cloud Run requiere facturación; el proyecto
   Firebase pasa al plan Blaze. Configura alertas de presupuesto en Google Cloud.
   Consulta los [planes de Firebase](https://firebase.google.com/docs/projects/billing/firebase-pricing-plans).

El presupuesto funcional de USD 20 corresponde al consumo de IA registrado por
la aplicación. Cloud Run, Artifact Registry, Secret Manager, Cloud NAT y la IP
reservada se facturan aparte. Las [alertas de Cloud Billing](https://docs.cloud.google.com/billing/docs/how-to/budgets)
por sí solas no fijan un límite de gasto.

## 3. Registrar la aplicación web

1. En **Configuración del proyecto → General → Tus apps**, pulsa el icono **Web `</>`**.
2. Registra una app, por ejemplo `AI News Web`.
3. Guarda la configuración web: `apiKey`, `authDomain`, `projectId` y `appId`.
4. No necesitas pegar el ejemplo JavaScript de Firebase: el repositorio ya inicializa el SDK.
5. En **Hosting**, completa la activación inicial si la consola lo pide.

La configuración del SDK web es pública y termina en el navegador. Los secretos
de servidor, las claves privadas y los tokens de sesión no deben ir en `EXPO_PUBLIC_*`.
Consulta [configuración web de Firebase](https://firebase.google.com/docs/web/setup).

## 4. Habilitar el inicio de sesión

1. En **Authentication**, pulsa **Comenzar** si aún no está habilitado.
2. En **Método de acceso / Sign-in method**, habilita **Google**, selecciona el
   correo de soporte y guarda.
3. Habilita también **Anónimo / Anonymous**, usado por «Continuar como invitado».
4. En **Configuración → Dominios autorizados**, comprueba o añade:
   - `TU_PROJECT_ID.web.app`;
   - `TU_PROJECT_ID.firebaseapp.com`;
   - `localhost` para desarrollo web;
   - tu dominio personalizado, si lo usas.
5. Escribe solo el hostname, sin `https://`, puerto ni rutas. Los proyectos nuevos
   pueden requerir que agregues `localhost` manualmente.

El login web usa popup. Si Google muestra una restricción de audiencia o de modo
de prueba, revisa **Google Auth Platform → Audience** en el mismo proyecto Google
Cloud y habilita el acceso de las cuentas que probarán la app. Referencias:
[Google Sign-In web](https://firebase.google.com/docs/auth/web/google-signin),
[usuarios anónimos](https://firebase.google.com/docs/auth/web/anonymous-auth) y
[dominios de desarrollo](https://firebase.google.com/docs/auth/faq-and-troubleshooting).

## 5. Instalar las herramientas locales

Necesitas Docker, Make, Python 3, Node.js 24 y npm. Instala
[Google Cloud CLI](https://cloud.google.com/sdk/docs/install) y la
[Firebase CLI](https://firebase.google.com/docs/cli).

```bash
npm install -g firebase-tools
gcloud auth login
firebase login
firebase projects:list
cd frontend
npm ci
cd ..
```

Verifica que tu proyecto aparezca en la lista. No necesitas descargar una clave
JSON de cuenta de servicio para verificar Firebase ID tokens en esta aplicación.

Ya existe `firebase.json`, con `frontend/dist` y el fallback SPA a `index.html`.
No necesitas ejecutar `firebase init` ni reemplazar esa configuración. El script
pasa `--project` explícitamente. Si tu proyecto tiene varios sitios Hosting,
verifica cuál es el sitio predeterminado: la configuración actual publica en ese sitio.
Conserva las fuentes de `frontend/dist/assets/node_modules/`: son recursos del
export Expo. No añadas `**/node_modules/**` a `hosting.ignore`, porque impediría
publicarlas y el navegador recibiría HTML al solicitarlas.
Consulta el [inicio de Hosting](https://firebase.google.com/docs/hosting/quickstart).

## 6. Configurar los servicios de Cloud Run

En la misma terminal:

```bash
export PROJECT_ID="tu-project-id"
export NEWS_FIREBASE_PROJECT_ID="$PROJECT_ID"
export REGION="us-central1"
export CHATBOT_PROVIDER="openai"
```

Elige la región adecuada para tu clúster Atlas. Estos son parámetros públicos.
Los nombres y valores predeterminados restantes están en `deploy/gcp/config.sh`.
Los targets `gcp-*` y `firebase-*` no cargan el `.env` raíz de desarrollo: usan
el entorno y ese archivo de configuración. Así no heredan accidentalmente las
URLs locales ni el proyecto Firebase de Compose. Ejecuta las tareas locales y
cloud en invocaciones Make separadas. Hosting carga los `.env` del frontend.

En `deploy/gcp/config.sh`, configura `OPENAI_MODEL` y estos dos parámetros no
secretos con los precios vigentes de ese modelo, expresados en USD por millón
de tokens:

- `NEWS_CHAT_INPUT_USD_PER_MILLION`: precio de entrada.
- `NEWS_CHAT_OUTPUT_USD_PER_MILLION`: precio de salida.

También puedes exportar esos parámetros en esta terminal. No dejes los precios
vacíos ni inventes valores: el despliegue con OpenAI los requiere para registrar
el consumo en `aiUsage` y aplicar el presupuesto funcional de USD 20. Configurarlos
solo en el `.env` raíz no los transmite a los comandos cloud.

Por defecto, ambos backends aceptan los orígenes
`https://TU_PROJECT_ID.web.app` y `https://TU_PROJECT_ID.firebaseapp.com`.
Para un dominio propio o para probar la web local contra Cloud Run, configura
ambas listas antes del deploy:

```bash
export NEWS_API_ALLOWED_ORIGINS="https://${PROJECT_ID}.web.app,https://${PROJECT_ID}.firebaseapp.com,https://noticias.ejemplo.com,http://localhost:8081"
export CHATBOT_ALLOWED_ORIGINS="$NEWS_API_ALLOWED_ORIGINS"
```

Usa orígenes exactos con esquema y puerto cuando corresponda, sin ruta ni barra
final. CORS en los backends y dominios autorizados en Firebase son configuraciones
distintas; ambas deben permitir el portal. El script preserva las comas al enviar
las variables a Cloud Run, según la [sintaxis de variables de entorno](https://cloud.google.com/run/docs/configuring/services/environment-variables).

## 7. Preparar infraestructura y Atlas

```bash
make gcp-bootstrap
```

El bootstrap crea APIs, Artifact Registry, cuentas de servicio, contenedores de
secretos, VPC, NAT con IP fija y federación GitHub. Necesitas permisos para crear
estos recursos. No despliega la app ni carga datos en MongoDB.

1. Guarda la IP y los identificadores WIF que imprime.
2. En Atlas, **Network Access**, autoriza esa IP como `<IP>/32`.
3. En Atlas, prepara un usuario DB con acceso a la base `ai_assisted_news`.
4. Prepara los archivos locales requeridos:

   ```bash
   make setup-keys
   ```

5. Completa manualmente `keys/mongodb_uri` con tu conexión Atlas y
   `keys/openai_api_key` con tu clave OpenAI. Ambos archivos son obligatorios
   para este despliegue. Nunca pegues esos valores en `.env`,
   código, chats ni commits. El bootstrap no sobrescribe archivos existentes.
6. Ejecuta personalmente la carga a Secret Manager:

   ```bash
   make gcp-secrets CHATBOT_PROVIDER=openai
   ```

   Este comando carga MongoDB y OpenAI como versiones de secretos en el proyecto
   seleccionado. La clave OpenAI debe existir y tener contenido. Ya no se requiere
   `keys/news_admin_password`.

## 8. Inicializar el esquema y el contenido

El deploy no inicializa ni rellena Atlas. Si esa base ya tiene el esquema y los
catálogos, verifica su estado. Para una base nueva, configura estos parámetros
no secretos en el `.env` raíz:

```dotenv
NEWS_DB_MODE=atlas
NEWS_MONGODB_DATABASE=ai_assisted_news
NEWS_MONGODB_URI_FILE=keys/mongodb_uri
NEWS_FIREBASE_PROJECT_ID=tu-project-id
```

Autoriza también temporalmente tu IP local en Atlas para ejecutar los comandos
desde tu equipo. Luego ejecuta:

```bash
docker compose --profile tools build news-tools
make db-check-config
make db-ping
make db-init
make db-seed-catalogs
make db-schema-check
make db-seed-check
```

`db-init` aplica validadores e índices; los catálogos son reproducibles. Revisa la
base seleccionada antes de ejecutarlos. Si quieres contenido de demostración y
esta base lo permite, ejecuta `make db-seed-news` y `make db-news-check`.
Los seeders no generan usuarios ni consumo IA reales. No ejecutes un reseed para
resolver un error de conexión o configuración.

## 9. Desplegar los dos backends

Con los secretos cargados y el modelo y sus precios configurados en el paso 6,
ejecuta el primer despliegue con OpenAI:

```bash
ALLOW_PUBLIC=1 make gcp-deploy CHATBOT_PROVIDER=openai
```

`ALLOW_PUBLIC=1` permite que el navegador llegue a las URLs HTTPS de Cloud Run.
La autorización de aplicación sigue vigente: perfil, interacciones y chat
requieren tokens Firebase; publicar exige además `users.role=admin` en MongoDB.
El feed público y el detalle conservan acceso público.

El script construye y sube las imágenes, despliega y al final imprime:

```dotenv
EXPO_PUBLIC_NEWS_API_BASE_URL=https://TU_API.run.app
EXPO_PUBLIC_ASSISTANT_API_BASE_URL=https://TU_CHATBOT.run.app
```

Abre `/health` en ambas URLs y comprueba conexión MongoDB. Si ya hay IAM público,
los siguientes deploys pueden ejecutarse sin `ALLOW_PUBLIC=1`.

Para volver a desplegar, conserva la configuración del paso 6:

```bash
make gcp-deploy CHATBOT_PROVIDER=openai
```

Si cambias la clave, ejecuta personalmente `make gcp-secrets CHATBOT_PROVIDER=openai`
antes de volver a desplegar. Las llamadas reales a OpenAI generan consumo;
las consultas que el chat resuelve directamente con MongoDB pueden seguir sin usar IA.
No se atribuyen tokens ni costos de las pruebas de agentes a `aiUsage`.

## 10. Configurar y publicar el frontend

Si `frontend/.env` no existe, créalo a partir de `frontend/.env.example`. Si ya
existe, edítalo sin sobrescribir su configuración. Completa:

```dotenv
EXPO_PUBLIC_FIREBASE_API_KEY=CONFIGURACION_PUBLICA_WEB
EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=tu-project-id.firebaseapp.com
EXPO_PUBLIC_FIREBASE_PROJECT_ID=tu-project-id
EXPO_PUBLIC_FIREBASE_APP_ID=APP_ID_WEB
EXPO_PUBLIC_NEWS_API_BASE_URL=https://TU_API.run.app
EXPO_PUBLIC_ASSISTANT_API_BASE_URL=https://TU_CHATBOT.run.app
```

Usa los valores de tu app web del paso 3 y las URLs del paso 9. Para web no
necesitas los client IDs OAuth nativos. Si utilizas `.env.production`, mantenlo
coherente: Expo lo carga para este export y las variables del shell tienen prioridad.

```bash
make firebase-check-config
make firebase-deploy
```

La validación rechaza parámetros ausentes, Project IDs distintos y APIs locales
o sin HTTPS. El deploy vuelve a validar, limpia la caché de Metro con `--clear`,
exporta Expo a `frontend/dist` y ejecuta
`firebase deploy --only hosting` para el proyecto indicado. Firebase publica la
URL del sitio. El export sigue el [flujo web de Expo](https://docs.expo.dev/deploy/web/).

Si cambias una variable `EXPO_PUBLIC_*`, vuelve a desplegar Hosting: esos valores
se incorporan al bundle durante la compilación. Cambiar solo Cloud Run no actualiza el navegador.

## 11. Comprobar la integración publicada

1. Abre `https://TU_PROJECT_ID.web.app` y entra con Google.
2. Elige país y temas, guarda y comprueba que el feed muestre sus motivos de selección.
3. Abre una noticia, léela y vuelve al feed. Debe consultar de nuevo el ranking
   después de enviar el tiempo activo; la ubicación se selecciona manualmente.
4. Abre el chat y pregunta por noticias. Las citas deben abrir el detalle publicado.
   Después pide un resumen o una explicación de una noticia. Comprueba que la
   respuesta elaborada use `strategy=llm`, `aiUsed=true` y tenga su registro en
   `aiUsage`. Una consulta resuelta directamente con MongoDB puede tener otra
   estrategia aunque el proveedor configurado sea OpenAI.
5. Recarga el portal: la sesión y preferencias de esa cuenta deben restaurarse.
6. Cierra sesión y entra como invitado: debe tener una identidad distinta.
7. Para comprobar un admin, sigue la promoción manual de un UID verificado en la
   [guía de Auth](../reviews/firebase-auth-configuracion.md#2-accesos-y-autorización).
   Una cuenta regular no debe poder publicar.

Las pruebas locales disponibles, sin cuentas Firebase ni Atlas reales, son:

```bash
make deploy-test
make news-integration-test
cd frontend
npm run typecheck
npm test
```

## 12. Activar el pipeline de GitHub, si lo deseas

En **Settings → Environments → production → Environment variables**, crea:

| Variable | Valor |
| --- | --- |
| `GCP_PROJECT_ID` | ID del proyecto Cloud Run |
| `WIF_PROVIDER` | Ruta completa que imprime `gcp-bootstrap` |
| `DEPLOYER_SA` | Correo de la cuenta del pipeline que imprime el bootstrap |
| `NEWS_FIREBASE_PROJECT_ID` | Opcional si coincide con `GCP_PROJECT_ID` |
| `GCP_REGION` | Opcional; predeterminado `us-central1` |
| `CHATBOT_PROVIDER` | Obligatorio: `openai`; si lo omites, el workflow actual usa `stub` |
| `NEWS_CHAT_INPUT_USD_PER_MILLION` / `NEWS_CHAT_OUTPUT_USD_PER_MILLION` | Obligatorios: precios del modelo configurado, en USD por millón de tokens |
| `NEWS_API_ALLOWED_ORIGINS` / `CHATBOT_ALLOWED_ORIGINS` | Si agregas un dominio propio |

El workflow valida backend, frontend y scripts antes de desplegar Cloud Run en
`main`. Hosting se publica con `make firebase-deploy`; todavía no hay publicación
automática del portal en ese workflow. No subas `keys/` ni claves JSON a GitHub.
Configura las tres variables de OpenAI antes de habilitar ese despliegue para
que un merge no cambie el chatbot a `stub`. Mantén `OPENAI_MODEL` en
`deploy/gcp/config.sh` alineado con los precios del entorno `production`.

## 13. Errores frecuentes

| Síntoma | Qué revisar |
| --- | --- |
| `auth/unauthorized-domain` | Dominio del navegador autorizado en Firebase Auth |
| `auth/operation-not-allowed` | Proveedores Google y Anonymous habilitados |
| Login Firebase funciona pero falla el perfil | Mismo Project ID en frontend, API y chat; usuario y catálogos MongoDB disponibles |
| Error CORS en `/profile`, `/news` o `/chat` | Origen exacto en la lista del servicio correspondiente y nuevo deploy del backend |
| Cloud Run responde 403 antes de llegar a la API | Primer deploy con `ALLOW_PUBLIC=1` y permisos IAM suficientes |
| API 401 | Sesión/token Firebase válido y proyecto correcto |
| API 503 o `/health` degradado | Versión del secreto MongoDB, IP NAT autorizada en Atlas y conexión DB |
| Feed vacío | Noticias `published` en la base correcta; la app no inventa noticias de respaldo |
| El portal intenta usar `localhost` | Corregir variables públicas, ejecutar validación y volver a publicar Hosting |
| Login con ambos botones deshabilitados y aviso de configuración Firebase | Revisar los cuatro parámetros públicos y repetir `make firebase-deploy`, que reconstruye con `--clear` para incorporar los valores actuales |
| Chat sin respuesta elaborada de IA | Verificar `CHATBOT_PROVIDER=openai` en Cloud Run y GitHub, secreto OpenAI cargado, precios del modelo y presupuesto disponible; probar con resumen o explicación |

## 14. Si también quieres instalarla en Android/iOS

Hosting entrega la web, que puedes abrir desde el navegador del teléfono. Para
Google Sign-In nativo necesitas un build propio; Expo Go no valida ese recorrido.
Registra las apps con `com.aina.news`, configura firmas y client IDs nativos y sigue
la [guía del frontend](../../frontend/README.md#configurar-firebase-authentication).
Eso es un paso separado del despliegue web de esta guía.

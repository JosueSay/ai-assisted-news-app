# Despliegue de AI News

Actualizado: 2026-10-20. El frontend web se publica en Firebase Hosting; Firebase
Authentication identifica a lectores e invitados. `news-api` y el assistant en
modo news corren en Cloud Run y comparten únicamente MongoDB Atlas
`ai_assisted_news`.

La [guía Firebase paso a paso](firebase-paso-a-paso.md) explica desde la creación
del proyecto hasta la comprobación del feed, la lectura, el chat y el pipeline.
Para automatizar publicaciones después del primer deploy, sigue la
[guía del pipeline paso a paso](pipeline-paso-a-paso.md).

## Comandos

| Comando | Uso |
| --- | --- |
| `make gcp-bootstrap` | Preparar APIs, Artifact Registry, IAM, Secret Manager, VPC/NAT y WIF |
| `make gcp-secrets CHATBOT_PROVIDER=openai` | Cargar manualmente los secretos MongoDB y OpenAI desde `keys/` |
| `ALLOW_PUBLIC=1 make gcp-deploy CHATBOT_PROVIDER=openai` | Primer deploy de los dos backends, con OpenAI, acceso HTTP público y Auth de aplicación |
| `make firebase-check-config` | Validar proyecto Firebase y parámetros públicos del frontend |
| `make firebase-deploy` | Exportar la web y publicar únicamente Hosting |
| `make deploy-test` | Comprobar comandos cloud/Hosting, preflight CI e IAM simulados, sin red ni secretos |
| `make news-integration-test` | Probar API, perfil, lecturas y chat sobre MongoDB efímera |

Configura `PROJECT_ID` y opcionalmente `NEWS_FIREBASE_PROJECT_ID` y `REGION` antes
de ejecutar los comandos cloud. Se pueden definir en el entorno o en
`deploy/gcp/config.sh`. CORS permite por defecto los dos dominios Hosting del
proyecto Firebase; los dominios propios deben agregarse a ambos backends.
Los comandos cloud no cargan el `.env` raíz de desarrollo. Hosting usa la
configuración pública del frontend; las tareas locales conservan el `.env` raíz.
Configura el modelo y sus precios de entrada/salida en el entorno o en
`deploy/gcp/config.sh` antes de desplegar. En GitHub `production`, define
`CHATBOT_PROVIDER=openai` y ambos precios explícitamente; el workflow usa `openai`
por defecto y requiere una región explícita. La guía detalla estos pasos.

## Archivos y límites

- `deploy/gcp/config.sh`: parámetros públicos, incluidos Firebase, CORS y precios IA.
- `deploy/gcp/bootstrap.sh`: infraestructura; no inicializa MongoDB ni carga secretos.
- `deploy/gcp/load-secrets.sh`: carga MongoDB y, cuando corresponde, OpenAI. El
  operador lo ejecuta personalmente; no se requiere contraseña admin local.
- `deploy/gcp/deploy.sh`: build, push y deploy de los dos servicios Python.
- `deploy/firebase/hosting.sh` y `firebase.json`: export y publicación del portal.
- `deploy/firebase/ci.sh`: resuelve URLs Cloud Run y publica Hosting con las
  variables públicas del runner y credenciales ADC/WIF.
- `deploy/gcp/check-ci-config.sh`: valida variables antes de cambios cloud.
- `.github/workflows/deploy.yml`: tests backend/frontend y publicación de Cloud
  Run seguida de Hosting desde `main`, con variables GitHub `production`.

Los secretos cloud se montan como archivos y cada servicio tiene su propia cuenta.
La salida usa NAT con IP fija para la lista de acceso Atlas. El rol admin proviene
exclusivamente de `users.role`, vinculado al UID Firebase verificado. Perfil,
interacciones y chat requieren Firebase ID tokens; feed y detalle públicos siguen
disponibles. El límite de instancias no reemplaza los controles de presupuesto IA.

El despliegue web no genera un build Android/iOS. Abre el portal publicado en el
navegador del teléfono; Google Sign-In nativo requiere un build propio y configuración
OAuth adicional. Consulta la [guía del frontend](../../frontend/README.md).

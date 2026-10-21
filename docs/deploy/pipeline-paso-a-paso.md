# Activar despliegue automático de backend y frontend

Esta guía completa el despliegue manual ya realizado. El workflow publica los dos
servicios Cloud Run y luego Firebase Hosting cuando llegan cambios a `main` y
pasan las pruebas. No actualiza secretos ni esquemas MongoDB automáticamente.

## 1. Actualizar los permisos de la cuenta del pipeline

Desde la raíz del repositorio:

```bash
export PROJECT_ID="adfasdfasfd-1899a"
export NEWS_FIREBASE_PROJECT_ID="$PROJECT_ID"
export REGION="us-east4"
export GITHUB_REPO="ai-project-u1g/ai-assisted-news-app"
make gcp-bootstrap
```

El bootstrap comprueba los recursos existentes y añade a `gh-deployer` los
permisos para publicar Hosting: `roles/firebasehosting.admin`,
`roles/serviceusage.apiKeysViewer` y `roles/serviceusage.serviceUsageConsumer`.
También habilita las APIs de Firebase necesarias. Conserva la infraestructura
existente, su IP NAT y los secretos que ya cargaste; no es necesario volver a
cargar valores secretos para activar el pipeline.

El repositorio fue transferido de `JosueSay` a `ai-project-u1g`. El bootstrap
actualiza también un provider WIF existente y concede a la cuenta del pipeline
la vinculación del repositorio actual. Su condición permite únicamente ese
repositorio y `refs/heads/main`: el nombre anterior deja de satisfacerla.
Tras otra transferencia, actualiza `GITHUB_REPO` y repite el bootstrap antes
del siguiente despliegue. No cambian `WIF_PROVIDER` ni `DEPLOYER_SA` en GitHub.

La autorización Hosting sigue los
[roles documentados por Firebase](https://firebase.google.com/docs/projects/iam/roles-predefined-product#firebase_hosting_roles).
La CLI usa las [credenciales ADC del job](https://firebase.google.com/docs/cli#cli-ci-systems),
obtenidas mediante WIF. No se necesita `firebase login:ci` ni una clave JSON permanente.

## 2. Crear el entorno GitHub

1. Abre el repositorio en GitHub.
2. Ve a **Settings → Environments → New environment**.
3. Crea el entorno con el nombre exacto **`production`**.
4. En sus reglas de despliegue permite la rama **`main`**.
5. Si configuras revisores obligatorios, el pipeline esperará su aprobación antes
   de desplegar. Para una ejecución enteramente automática, no añadas esa revisión.

## 3. Añadir las variables de producción

En **Environment variables → Add environment variable**, crea cada fila de esta
tabla. Son parámetros públicos; los archivos `.env` locales no se suben al runner.

| Nombre | Valor para este despliegue |
| --- | --- |
| `GCP_PROJECT_ID` | `adfasdfasfd-1899a` |
| `GCP_REGION` | `us-east4` |
| `WIF_PROVIDER` | `projects/248394644314/locations/global/workloadIdentityPools/github/providers/ai-news-repo` |
| `DEPLOYER_SA` | `gh-deployer@adfasdfasfd-1899a.iam.gserviceaccount.com` |
| `CHATBOT_PROVIDER` | `openai` |
| `OPENAI_MODEL` | `gpt-5-mini`, el modelo del despliegue actual |
| `NEWS_CHAT_INPUT_USD_PER_MILLION` | `0.25`, precio configurado para el modelo actual |
| `NEWS_CHAT_OUTPUT_USD_PER_MILLION` | `2.00`, precio configurado para el modelo actual |
| `EXPO_PUBLIC_FIREBASE_API_KEY` | Copia el valor público del SDK web de `frontend/.env` |
| `EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN` | `adfasdfasfd-1899a.firebaseapp.com` |
| `EXPO_PUBLIC_FIREBASE_PROJECT_ID` | `adfasdfasfd-1899a` |
| `EXPO_PUBLIC_FIREBASE_APP_ID` | Copia el App ID web de `frontend/.env` |

`EXPO_PUBLIC_FIREBASE_API_KEY` es la configuración pública del cliente Firebase;
la clave privada OpenAI es un secreto distinto y permanece en Secret Manager.
No copies `keys/openai_api_key`, `keys/mongodb_uri` ni tokens a estas variables.
Si cambias modelo o tarifas, actualiza conjuntamente el nombre y los dos precios.

Opcionales:

- `NEWS_FIREBASE_PROJECT_ID`: solo si Auth/Hosting usan otro proyecto Google Cloud.
  Debe coincidir con `EXPO_PUBLIC_FIREBASE_PROJECT_ID`.
- `NEWS_API_ALLOWED_ORIGINS` y `CHATBOT_ALLOWED_ORIGINS`: para dominios adicionales.
  Los dos dominios Hosting del proyecto ya se permiten por defecto.

Las dos URLs API del frontend se consultan automáticamente en Cloud Run después
de desplegar el backend. No necesitas copiarlas a GitHub.

## 4. Subir los cambios y abrir una PR hacia main

Los cambios locales del workflow y scripts deben estar en GitHub. Revisa primero:

```bash
make deploy-test
git diff --check
git status --short
```

Prepara y confirma únicamente los archivos del cambio de despliegue, incluidos
los nuevos scripts, pruebas y documentación. Verifica la selección antes de
confirmarla; no añadas secretos, `.env` locales ni artefactos generados.
Usa un commit Conventional Commits, por ejemplo:

```text
feat(deploy): automate frontend and backend releases
```

Haz push de tu rama de trabajo y abre una PR con destino `main`. Estas acciones
las ejecutas tú; el agente no hace push automáticamente. Cuando pasen las pruebas,
haz merge a `main`. WIF ya está limitado al repositorio configurado en
`deploy/gcp/config.sh` y a esa rama; una ejecución desde otra rama no publica.

## 5. Verificar el primer despliegue automático

En **GitHub → Actions → deploy**, abre la ejecución del push a `main`.

1. `test` debe aprobar backend, contrato de scripts e integración MongoDB efímera.
2. `frontend` debe aprobar TypeScript, tests y export web de comprobación.
3. `deploy` debe aprobar la configuración de `production` y autenticar por WIF.
4. **Publicar API y chatbot en Cloud Run** debe terminar correctamente.
5. **Publicar frontend en Firebase Hosting** debe terminar con `Deploy complete!`.
6. Abre `https://adfasdfasfd-1899a.web.app` y prueba login, feed y chat.

La automatización queda verificada cuando pasa una ejecución real completa y el
sitio funciona. Los tests locales de scripts usan CLIs simuladas; no verifican
por sí solos la configuración IAM o las variables externas.

## 6. Uso habitual después de activarlo

```text
cambio → commit → push → PR → pruebas → merge a main → backend → Hosting
```

Si falla una prueba, no se publica. Si falla el deploy backend, no se publica
Hosting. Los dos servicios y Hosting son despliegues secuenciales: un fallo
intermedio puede dejar alguno actualizado; no existe rollback conjunto automático.

Para repetir una publicación sin cambios, usa **Actions → deploy → Run workflow**
seleccionando `main`. Los comandos Make manuales siguen disponibles.

Los cambios de secretos se cargan mediante `make gcp-secrets CHATBOT_PROVIDER=openai`
antes de volver a desplegar. Los cambios de esquema DB siguen su procedimiento
revisado e independiente; el pipeline no hace reseeds ni migraciones.

## Errores al activar

| Mensaje o síntoma | Acción |
| --- | --- |
| Falta una variable de producción | Crear la variable indicada en el entorno `production` |
| WIF deniega acceso | Verificar repo, rama `main`, provider y cuenta de despliegue |
| Hosting devuelve 403 | Repetir el bootstrap actualizado y comprobar permisos de la cuenta `gh-deployer` |
| No encuentra los servicios Cloud Run | Confirmar `GCP_PROJECT_ID`, `GCP_REGION=us-east4` y nombres de servicio |
| Se queda esperando aprobación | Revisar las reglas de protección del entorno `production` |
| Publica backend pero falla Hosting | Corregir el paso fallido y repetir el workflow completo; revisar el sitio después |

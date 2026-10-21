# keys

Este directorio contiene archivos con secretos (URIs, API keys, tokens) necesarios para
ejecutar el proyecto en entorno local.

## Reglas

- **Nunca versionar** estos archivos. `.gitignore` ignora todo el directorio excepto este README.
- Cada archivo contiene **únicamente el valor del secreto**, sin metadatos, comentarios ni
  líneas adicionales.
- El proyecto no lee secretos de variables de entorno directamente: los lee desde estos archivos.

## Archivos requeridos

| Archivo | Propósito | ¿Debe crearlo el desarrollador? |
| --- | --- | --- |
| `mongodb_uri` | URI de conexión a MongoDB Atlas para la aplicación de noticias. | Sí |
| `openai_api_key` | API key de OpenAI del chatbot de noticias (`backend/assistant` en modo news). Solo se usa con `CHATBOT_PROVIDER=openai`. | Sí (puede quedar vacío con `CHATBOT_PROVIDER=stub`) |

## Preparación automática

```bash
make setup-keys
```

Crea los archivos faltantes vacíos. No sobrescribe archivos existentes.

Para Cloud Run se usa la misma lista: el operador ejecuta `make gcp-secrets`
para cargar estos archivos en Secret Manager. Con `CHATBOT_PROVIDER=stub` OpenAI
es opcional. El despliegue actual con Firebase Auth no requiere contraseña admin
local ni otro archivo secreto. Consulta la
[guía de despliegue](../docs/deploy/firebase-paso-a-paso.md).

## Formato esperado

### `mongodb_uri`

Contiene únicamente la URI de MongoDB Atlas. Sin comillas, sin saltos de línea extra:

```
mongodb+srv://usuario:contraseña@cluster.xxxxx.mongodb.net/
```

### `openai_api_key`

Contiene únicamente la API key de OpenAI del chatbot (`POST /chat` en el puerto 8010). Con
`CHATBOT_PROVIDER=stub` (valor por defecto en Compose) no se usa y puede quedar vacío: el chat
responde solo con datos de MongoDB y sin costo.

Con `CHATBOT_PROVIDER=openai` también deben definirse en `.env`
`NEWS_CHAT_INPUT_USD_PER_MILLION` y `NEWS_CHAT_OUTPUT_USD_PER_MILLION` (precios del modelo), que
no son secretos. Cada llamada queda registrada en la colección `aiUsage` y el chat deja de usar IA
al alcanzar el presupuesto de `NEWS_AI_BUDGET_USD` (20 USD por defecto).

## Firebase Authentication

La autenticación usa Firebase ID tokens; no requiere archivos de cuenta de servicio ni
secretos OAuth en `keys/`. El `Project ID` del backend va en `.env` como
`NEWS_FIREBASE_PROJECT_ID`; la configuración pública de cliente y los OAuth Client IDs
van en `frontend/.env`. No guardes contraseñas, tokens ni claves privadas en esos archivos.

Reemplaza a pasar la key por la variable `API_GPT`: no debe ir en `.env`. El assistant solo usa
`API_GPT` si está definida explícitamente en el entorno (compatibilidad con su uso anterior).

## Cómo crear `mongodb_uri`

1. Copiar la URI desde MongoDB Atlas (Database → Connect → Drivers).
2. Reemplazar `<password>` con la contraseña real.
3. Crear el archivo:

   ```bash
   echo 'mongodb+srv://...' > keys/mongodb_uri
   ```

4. Verificar que Git no lo trackea:

   ```bash
   git status keys/
   ```

## Seguridad

- No compartir el contenido de estos archivos.
- No incluirlos en logs, issues, tickets ni commits.
- Si por error se versiona un secreto, rotar la credencial inmediatamente.

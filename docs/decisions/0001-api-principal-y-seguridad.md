# ADR 0001: API principal y controles de seguridad

- Fecha: 2026-10-03
- Estado: propuesta

## Contexto

La app móvil usa noticias de demostración y guarda la sesión solo en el teléfono. El asistente
necesita un `user_id` confiable y una proyección `assistant_contexts` que nadie escribe. Hay un
clúster MongoDB Atlas de desarrollo (`news-app-dev`).

## Decisión

1. Un solo servicio `backend/services/api` con FastAPI y Python 3.13, igual que el asistente. Usa
   `pymongo` asíncrono (`AsyncMongoClient`), sin ODM.
2. Identidad con Google. La API verifica el `id_token` con la librería `google-auth` y emite sus
   propios tokens. El teléfono no consulta el perfil de Google directamente.
3. Access token JWT firmado con HS256, vida de 15 minutos, `iss` y `aud` fijos, `sub` = id del
   usuario. Refresh token opaco de 256 bits, vida de 30 días, guardado como hash SHA-256, con
   rotación en cada uso y revocación de la familia si se reutiliza.
4. La ingesta de noticias es un servicio aparte (`backend/services/ingest`): RSS primero y scraper
   HTML solo como respaldo. Comparte con la API el formato de `articles`. El tráfico de usuarios
   nunca provoca peticiones a fuentes externas. Detalle en `docs/architecture/ingesta.md`.
5. MongoDB Atlas en desarrollo. El Docker Compose sigue usando Mongo local para pruebas.

## Controles (OWASP API Security Top 10, 2023)

| Riesgo | Control |
|---|---|
| API1 autorización por objeto | Toda consulta de datos de usuario filtra por `user_id` del JWT. Nunca se acepta `user_id` del cliente. |
| API2 autenticación | Verificación de `id_token` en servidor. JWT corto. Refresh con rotación y detección de reuso. Rate limit en `/auth/*`. |
| API3 autorización por propiedad | Modelos de respuesta Pydantic explícitos. Entradas con `extra="forbid"`. Nunca se devuelve un documento Mongo completo. |
| API4 consumo de recursos | `limit` máximo 50, cuerpo máximo 16 KB, timeouts a Mongo y al asistente, rate limit por IP y por usuario. |
| API5 autorización por función | Sin rutas de administración en v1. Si se agregan, rol verificado en servidor. |
| API6 flujos sensibles | Rate limit específico para `/v1/chat` por costo del modelo. |
| API7 SSRF | La ingesta solo usa URLs de una lista fija. El cliente nunca envía URLs que el servidor visite. |
| API8 configuración | CORS cerrado (la app nativa no lo necesita). Docs `/docs` desactivadas en producción. Cabeceras de seguridad. Errores sin trazas. Contenedor sin root. |
| API9 inventario | Versión en la ruta (`/v1`). Contrato en `docs/api/README.md`. |
| API10 consumo de APIs externas | El contenido de las fuentes se trata como no confiable: se limpia HTML y se limita tamaño. |

Controles adicionales:

- Secretos solo en variables de entorno o gestor de secretos. `.env` ignorado por git. Nada secreto en
  variables `EXPO_PUBLIC_*`.
- Un usuario de MongoDB por servicio en el clúster compartido: la API con `readWrite` sobre
  `news_app`, el scraper con escritura solo en `articles` e `ingestion_runs`, el asistente solo
  lectura. Cada integrante del equipo usa su propio usuario.
- Lista de IPs en Atlas. No usar `0.0.0.0/0`.
- Logs estructurados con `request_id`, sin tokens, contraseñas ni cuerpos completos.
- En el teléfono, tokens en `expo-secure-store`, no en AsyncStorage.
- Dependencias fijadas y revisadas con `pip-audit` en CI.

## Alternativas consideradas

- Firebase Auth o Auth0: menos código, pero agrega un proveedor más y otro SDK en la app.
- Sesiones con cookie: no encaja bien con una app nativa.
- Usar directamente el token de Google en cada petición: obliga a validar contra Google siempre y
  no permite revocar sesiones propias.

## Consecuencias

- La API es la única puerta de entrada. El asistente deja de publicarse fuera de la red interna.
- Hay que agregar `expo-secure-store` al frontend y cambiar `googleAuth.ts` para enviar el
  `id_token`.
- Para validar `aud` se necesitan los client ID de Google de Android e iOS en la configuración de
  la API.

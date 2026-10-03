# Contratos de API

Estado: borrador v1 (2026-10-03). API principal en `backend/services/api`. Base: `/v1`.

## Convenciones

- JSON UTF-8. Fechas en ISO 8601 con zona horaria.
- Autenticación: `Authorization: Bearer <access_token>` salvo en rutas marcadas como públicas.
- Paginación por cursor: `?limit=20&cursor=<opaco>`. `limit` máximo 50. La respuesta incluye
  `next_cursor` o `null`.
- Los errores usan `application/problem+json` (RFC 9457) y nunca incluyen trazas ni detalles internos.

```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Token expirado.",
  "request_id": "b3f1c2..."
}
```

## Rutas

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | pública | Estado de la API y de MongoDB. Sin datos sensibles. |
| POST | `/v1/auth/google` | pública | Recibe `id_token` de Google y devuelve tokens propios y el usuario. |
| POST | `/v1/auth/refresh` | pública | Rota el refresh token. |
| POST | `/v1/auth/logout` | Bearer | Revoca el refresh token enviado. |
| GET | `/v1/me` | Bearer | Perfil del usuario autenticado. |
| PUT | `/v1/me/preferences` | Bearer | Reemplaza `topics` (lista cerrada de temas). |
| GET | `/v1/news` | pública | Feed paginado. Filtro opcional `topic`. |
| GET | `/v1/news/{id}` | pública | Detalle de un artículo. |
| GET | `/v1/me/saved` | Bearer | Artículos guardados, paginado. |
| PUT | `/v1/me/saved/{article_id}` | Bearer | Guarda un artículo. Idempotente. |
| DELETE | `/v1/me/saved/{article_id}` | Bearer | Quita un guardado. Idempotente. |
| POST | `/v1/chat` | Bearer | Reenvía al asistente con el `user_id` del token. Pendiente de acordar con el asistente. |

## Esquemas principales

`POST /v1/auth/google`

```json
// entrada
{ "id_token": "eyJhbGciOiJSUzI1NiIs..." }

// salida 200
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "Xk9...",
  "user": { "id": "66fe...", "name": "Ana", "email": "ana@gmail.com", "photo_url": null, "topics": [] }
}
```

`GET /v1/news?topic=economia&limit=20`

```json
{
  "items": [
    {
      "id": "66ff...",
      "title": "Guatemala impulsa programas de ahorro digital",
      "summary": "Nuevas iniciativas...",
      "source": "Prensa Libre",
      "url": "https://...",
      "topic": "economia",
      "published_at": "2026-09-20T09:00:00-06:00"
    }
  ],
  "next_cursor": "eyJwIjoi..."
}
```

El frontend hoy usa `publishedAt` en camelCase. La API responde en snake_case y el
`newsService.ts` hace la conversión.

## Códigos de estado

| Código | Uso |
|---|---|
| 400 | Cuerpo o parámetros inválidos. |
| 401 | Falta token, token inválido o expirado. |
| 403 | Usuario deshabilitado. |
| 404 | Recurso inexistente o ajeno. Un recurso de otro usuario responde 404, no 403. |
| 409 | Conflicto de estado. |
| 413 | Cuerpo mayor al límite (16 KB). |
| 429 | Límite de peticiones. Incluye `Retry-After`. |
| 503 | MongoDB o el asistente no disponibles. |

# Arquitectura

Estado: propuesta v1 (2026-10-03). Cubre la API principal. El asistente (`backend/assistant`) lo
mantiene otro integrante; aquí solo aparece como dependencia.

## Componentes y límites de confianza

La app móvil solo habla con la API principal. La API es el único componente que conoce la identidad
del usuario, escribe en MongoDB y llama al asistente por la red interna.

```mermaid
flowchart LR
    subgraph Cliente["Dispositivo (no confiable)"]
        APP["App Expo<br/>tokens en SecureStore"]
    end

    subgraph Externos["Servicios externos"]
        GOOGLE["Google OAuth<br/>JWKS"]
        FUENTES["Fuentes de noticias<br/>RSS / API"]
    end

    subgraph Backend["Red interna del backend"]
        API["API principal<br/>FastAPI :8000"]
        INGEST["Ingesta / scraper<br/>servicio aparte"]
        ASSIST["Asistente<br/>FastAPI :8010"]
    end

    subgraph Datos["MongoDB Atlas"]
        DB[("news_app")]
    end

    APP -- "HTTPS + Bearer JWT" --> API
    APP -- "PKCE" --> GOOGLE
    API -- "verifica id_token" --> GOOGLE
    API -- "TLS, usuario readWrite" --> DB
    API -- "user_id del JWT" --> ASSIST
    ASSIST -- "solo lectura" --> DB
    INGEST -- "HTTPS" --> FUENTES
    INGEST -- "upsert artículos" --> DB
```

| Límite | Regla |
|---|---|
| App a API | Todo dato del cliente se valida. El `user_id` nunca viaja en el cuerpo: sale del JWT. |
| API a Google | La firma, `aud`, `iss`, `exp` y `email_verified` del `id_token` se validan en el servidor. |
| API a asistente | Red privada. El puerto 8010 no se publica fuera de Docker. |
| API a MongoDB | Usuario de base de datos con `readWrite` solo sobre `news_app`. TLS obligatorio. IP en lista de acceso. |
| Ingesta a fuentes | Solo URLs de una lista fija de fuentes. Tiempo máximo y tamaño máximo por respuesta. Detalle en [ingesta.md](ingesta.md). |

## Inicio de sesión y renovación

La app ya obtiene el código de Google con PKCE. El cambio es enviar el `id_token` a la API en vez de
usar el `access_token` de Google para leer el perfil desde el teléfono.

```mermaid
sequenceDiagram
    autonumber
    participant App
    participant Google
    participant API
    participant DB as MongoDB

    App->>Google: Authorization Code + PKCE
    Google-->>App: id_token
    App->>API: POST /v1/auth/google {id_token}
    API->>Google: JWKS (en caché)
    API->>API: valida firma, aud, iss, exp, email_verified
    API->>DB: upsert users por google_sub
    API->>DB: guarda hash del refresh token
    API-->>App: access_token 15 min + refresh_token 30 días

    Note over App,API: Peticiones normales con Authorization: Bearer

    App->>API: POST /v1/auth/refresh {refresh_token}
    API->>DB: busca hash, revoca el usado, guarda el nuevo
    alt token ya usado antes
        API->>DB: revoca toda la familia
        API-->>App: 401
    else válido
        API-->>App: nuevo par de tokens
    end
```

El modo invitado no crea cuenta. Puede leer `GET /v1/news` sin token y no accede a preferencias,
guardados ni chat.

## Modelo de datos

Base `news_app`. Los campos marcados como índice se crean al iniciar la API.

```mermaid
erDiagram
    users ||--o{ refresh_tokens : tiene
    users ||--o{ saved_articles : guarda
    articles ||--o{ saved_articles : aparece_en
    users ||--o| assistant_contexts : proyecta

    users {
        ObjectId _id
        string google_sub UK
        string email
        string name
        string photo_url
        string[] topics
        string status
        date created_at
        date last_login_at
    }
    refresh_tokens {
        ObjectId _id
        ObjectId user_id
        string token_hash UK
        string family_id
        date expires_at "TTL"
        date revoked_at
        date created_at
    }
    articles {
        ObjectId _id
        string url_hash UK
        string url
        string title
        string summary
        string source
        string topic
        string image_url
        date published_at
        date ingested_at
    }
    saved_articles {
        ObjectId _id
        ObjectId user_id
        ObjectId article_id
        date created_at
    }
    assistant_contexts {
        ObjectId _id
        string user_id UK
        int schema_version
        object context
        date updated_at
    }
```

| Colección | Índices |
|---|---|
| `users` | `{google_sub: 1}` único |
| `refresh_tokens` | `{token_hash: 1}` único, `{family_id: 1}`, `{expires_at: 1}` TTL |
| `articles` | `{url_hash: 1}` único, `{published_at: -1, _id: -1}`, `{topic: 1, published_at: -1}` |
| `saved_articles` | `{user_id: 1, article_id: 1}` único, `{user_id: 1, created_at: -1}` |
| `assistant_contexts` | `{user_id: 1}` único. Lo escribe la API, lo lee el asistente. |

`assistant_contexts` sigue el esquema de `backend/assistant/docs/database.md`. Su contenido
(nombre, temas, últimos guardados) se acuerda con quien mantiene el asistente.

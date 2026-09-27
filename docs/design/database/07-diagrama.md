# Diagrama de Base de Datos — AI Assisted News App

> **Nota:** MongoDB no impone foreign keys. Las relaciones mostradas son referencias lógicas
> mediante `ObjectId`.

## Diagrama de colecciones y relaciones

```mermaid
erDiagram
    locations ||--o{ users : "simulatedLocationId"
    locations ||--o{ news : "geographicScope.locationIds[]"
    locations ||--o{ userInteractions : "context.simulatedLocationId"
    locations ||--o{ chatSessions : "simulatedLocationId"

    users ||--o{ news : "authorId"
    users ||--o{ news : "verification.reviewedBy (opcional)"
    users ||--o{ userInteractions : "userId"
    users ||--o{ chatSessions : "userId"
    users ||--o{ aiUsage : "userId"
    users ||--o{ auditLogs : "actorId"

    news ||--o{ userInteractions : "newsId"
    news ||--o{ aiUsage : "newsId"
    news ||--o{ auditLogs : "entityId"
    news ||--o{ chatSessions : "messages[].responseMetadata.citedNewsIds[]"

    chatSessions ||--o{ aiUsage : "chatSessionId"

    locations {
        ObjectId _id PK
        string name
        string city "nullable"
        string region "nullable"
        string country
        string countryCode
        enum level "city | region | country | international"
        bool active
        date createdAt
    }

    users {
        ObjectId _id PK
        string firebaseUid UK
        string email
        string displayName
        string photoUrl
        enum role "user | admin"
        ObjectId simulatedLocationId FK
        embedded onboarding
        array inferredInterests
        date createdAt
        date updatedAt
        date lastLoginAt
    }

    news {
        ObjectId _id PK
        string slug UK
        string title
        string summary
        string content
        ObjectId authorId FK
        enum status "draft | published"
        array topics
        array keywords
        embedded geographicScope
        embedded verification
        array sources
        embedded image
        embedded aiAssistance
        int wordCount
        int estimatedReadingMinutes
        date publishedAt "nullable"
        date createdAt
        date updatedAt
    }

    userInteractions {
        ObjectId _id PK
        ObjectId userId FK
        ObjectId newsId FK
        enum type "opened | read"
        int dwellTimeSeconds "nullable"
        embedded context
        date createdAt
    }

    chatSessions {
        ObjectId _id PK
        ObjectId userId FK
        ObjectId simulatedLocationId FK
        array messages "embebido"
        date createdAt
        date expiresAt "TTL futuro"
    }

    aiUsage {
        ObjectId _id PK
        enum feature "chat | summary | image_generation | classification"
        string provider
        string model
        ObjectId userId "nullable" FK
        ObjectId newsId "nullable" FK
        ObjectId chatSessionId "nullable" FK
        int inputTokens "nullable"
        int outputTokens "nullable"
        float estimatedCostUsd
        date createdAt
    }

    auditLogs {
        ObjectId _id PK
        ObjectId actorId FK
        enum action "news.created | news.updated | news.published | image.generated"
        string entityType "siempre 'news'"
        ObjectId entityId FK
        object details
        date createdAt
    }
```

## Documentos embebidos

| Colección | Documento embebido | Campos principales |
| --- | --- | --- |
| `users` | `onboarding` | `completed`, `completedAt`, `selectedTopics[]` |
| `users` | `inferredInterests[]` | `topic`, `score` (0-1), `updatedAt` |
| `news` | `geographicScope` | `level`, `locationIds[]` |
| `news` | `verification` | `status`, `reviewedBy`, `reviewedAt`, `notes` |
| `news` | `sources[]` | `name`, `url`, `sourceType`, `publishedAt`, `accessedAt`, `supports` |
| `news` | `image` | `url`, `alt`, `type`, `credit`, `rights`, `aiDisclosure` |
| `news` | `aiAssistance` | `summaryGenerated`, `topicsGenerated`, `imageGenerated`, `humanReviewed` |
| `userInteractions` | `context` | `simulatedLocationId`, `feedPosition` |
| `chatSessions` | `messages[]` | `role`, `content`, `responseMetadata` (embebido), `createdAt` |
| `chatSessions.messages` | `responseMetadata` | `strategy`, `intent`, `citedNewsIds[]`, `confidence`, `uncertainty`, `aiUsed` |

## Catálogos

- **`locations`**: Único catálogo precargado. Contiene ubicaciones geográficas reales
  (países, regiones, ciudades). Se selecciona durante el onboarding. No cambia por uso.

## Datos generados por uso

- `userInteractions` — cada lectura o apertura del usuario.
- `chatSessions` — cada conversación; expira tras 3600 segundos (TTL).
- `aiUsage` — cada llamada a un proveedor de IA.
- `auditLogs` — cada acción administrativa sobre noticias.

## Campos únicos

- `users.firebaseUid` — identificador externo desde Firebase Authentication.
- `news.slug` — identificador legible de la noticia.

## TTL futuro

`chatSessions` tendrá un índice TTL sobre `expiresAt`. La creación del índice corresponde
a un loop posterior. El modelo ya incluye el campo `expiresAt` con valor por defecto de
3600 segundos desde la creación.

# Colecciones

Parte de la [documentación de base de datos](README.md).

Esquema de cada colección. Las colecciones se presentan en orden de dependencia: primero el
catálogo que las demás referencian, después las entidades principales y por último los registros
derivados.

## Resumen

| Colección | Naturaleza | Referencia a | Referenciada por |
| --- | --- | --- | --- |
| `locations` | Catálogo precargado | — | `users`, `news`, `userInteractions`, `chatSessions` |
| `users` | Persistente | `locations` | `news`, `userInteractions`, `chatSessions`, `aiUsage`, `auditLogs` |
| `news` | Persistente | `users`, `locations` | `userInteractions`, `chatSessions`, `aiUsage`, `auditLogs` |
| `userInteractions` | Persistente | `users`, `news`, `locations` | — |
| `chatSessions` | Temporal con expiración | `users`, `locations`, `news` | `aiUsage` |
| `aiUsage` | Persistente | `users`, `news`, `chatSessions` | — |
| `auditLogs` | Persistente | `users`, `news` | — |

## locations

Catálogo global precargado. Define las ubicaciones que un usuario puede seleccionar durante el
onboarding y el alcance geográfico que puede declarar una noticia.

```javascript
// ============================================================
// locations
// Catálogo global precargado.
// Se selecciona durante onboarding.
// ============================================================
{
  _id: ObjectId,

  name: String,                 // "Guatemala City"
  city: String | null,
  region: String | null,
  country: String,
  countryCode: String,

  level:
    "city" |
    "region" |
    "country" |
    "international",

  active: Boolean,
  createdAt: Date
}
```

Notas:

- `level` usa la misma enumeración que `news.geographicScope.level`, de modo que ubicación y
  alcance geográfico son comparables.
- `active` distingue las ubicaciones seleccionables de las que permanecen en el catálogo por
  compatibilidad con datos existentes.

## users

Cuenta de la persona usuaria, sus preferencias declaradas y los intereses derivados de su
comportamiento.

```javascript
// ============================================================
// users
// ============================================================
{
  _id: ObjectId,

  firebaseUid: String,          // unique
  email: String,
  displayName: String,
  photoUrl: String,

  role: "user" | "admin",

  // Ubicación simulada seleccionada durante onboarding
  simulatedLocationId: ObjectId,

  onboarding: {
    completed: Boolean,
    completedAt: Date | null,

    // Elegidos explícitamente durante onboarding
    selectedTopics: [String]
  },

  // Calculados a partir de userInteractions
  inferredInterests: [
    {
      topic: String,
      score: Number,            // 0 - 1
      updatedAt: Date
    }
  ],

  createdAt: Date,
  updatedAt: Date,
  lastLoginAt: Date
}
```

Notas:

- `firebaseUid` es único y actúa como identificador externo de la cuenta.
- `simulatedLocationId` referencia a `locations`. Es la ubicación vigente del usuario, no un
  histórico.
- `onboarding.selectedTopics` contiene preferencias declaradas por la persona;
  `inferredInterests` contiene preferencias derivadas de `userInteractions`. Son dos orígenes
  distintos y no se mezclan en el mismo campo.
- `inferredInterests[].score` vive en el rango de 0 a 1.

## news

Noticia publicable, con su procedencia, su estado de verificación y su alcance geográfico.

```javascript
// ============================================================
// news
// ============================================================
{
  _id: ObjectId,

  slug: String,                 // unique

  title: String,
  summary: String,
  content: String,

  authorId: ObjectId,

  // No existe proceso de revisión separado
  status:
    "draft" |
    "published",

  topics: [String],
  keywords: [String],

  // ------------------------------------------
  // Alcance geográfico
  // ------------------------------------------
  geographicScope: {
    level:
      "city" |
      "region" |
      "country" |
      "international",

    locationIds: [ObjectId]
  },

  // ------------------------------------------
  // Verificación
  // ------------------------------------------
  verification: {
    status:
      "confirmed" |
      "developing" |
      "insufficient_sources" |
      "conflicting_sources",

    reviewedBy: ObjectId | null,
    reviewedAt: Date | null,
    notes: String | null
  },

  // ------------------------------------------
  // Fuentes / procedencia
  // ------------------------------------------
  sources: [
    {
      name: String,
      url: String,

      sourceType:
        "official" |
        "media" |
        "primary_source" |
        "witness" |
        "other",

      publishedAt: Date | null,
      accessedAt: Date,

      supports: String | null
    }
  ],

  // ------------------------------------------
  // Imagen
  // ------------------------------------------
  image: {
    url: String | null,
    alt: String | null,

    type:
      "photograph" |
      "illustration" |
      "ai_generated" |
      "ai_modified" |
      "none",

    credit: String | null,
    rights: String | null,

    aiDisclosure: String | null
  },

  // ------------------------------------------
  // Uso de IA
  // ------------------------------------------
  aiAssistance: {
    summaryGenerated: Boolean,
    topicsGenerated: Boolean,
    imageGenerated: Boolean,
    humanReviewed: Boolean
  },

  // ------------------------------------------
  // Lectura
  // ------------------------------------------
  wordCount: Number,
  estimatedReadingMinutes: Number,

  publishedAt: Date | null,
  createdAt: Date,
  updatedAt: Date
}
```

Notas:

- `slug` es único y sirve como identificador legible de la noticia.
- `authorId` y `verification.reviewedBy` referencian a `users`.
- `geographicScope.locationIds` referencia a `locations`.
- No existe ningún campo que permita al autor elevar la posición de su noticia en el feed. El
  detalle está en [decisiones descartadas](06-decisiones-descartadas.md).
- `wordCount` y `estimatedReadingMinutes` se documentan en
  [tiempo de lectura](05-tiempo-de-lectura.md).

## userInteractions

Registro de lectura. Contiene únicamente las interacciones que alimentan los intereses inferidos
y el orden del feed.

```javascript
// ============================================================
// userInteractions
// Solo interacciones que realmente utilizaremos
// para aprender intereses y ordenar el feed.
// ============================================================
{
  _id: ObjectId,

  userId: ObjectId,
  newsId: ObjectId,

  type:
    "opened" |
    "read",

  dwellTimeSeconds: Number | null,

  context: {
    simulatedLocationId: ObjectId,
    feedPosition: Number | null
  },

  createdAt: Date
}
```

Notas:

- `context.simulatedLocationId` conserva la ubicación vigente en el momento de la interacción.
  Permite interpretar el registro aunque el usuario cambie de ubicación después.
- `context.feedPosition` conserva la posición en la que se mostró la noticia. Admite `null`
  cuando la interacción no se originó en el feed.
- `dwellTimeSeconds` admite `null` cuando no se dispone de la medición.

## chatSessions

Conversación del usuario con el asistente. Es temporal: cada sesión tiene fecha de expiración.

```javascript
// ============================================================
// chatSessions
// Temporal — TTL
// ============================================================
{
  _id: ObjectId,

  userId: ObjectId,
  simulatedLocationId: ObjectId,

  messages: [
    {
      role: "user" | "assistant",
      content: String,

      // Solo aplica a respuestas assistant
      responseMetadata: {
        strategy:
          "database_query" |
          "template" |
          "llm",

        intent:
          "recent_news" |
          "regional_news" |
          "topic_news" |
          "news_detail" |
          "summarize" |
          "explain" |
          "unsupported",

        citedNewsIds: [ObjectId],

        confidence:
          "high" |
          "medium" |
          "low",

        uncertainty: String | null,
        aiUsed: Boolean
      },

      createdAt: Date
    }
  ],

  createdAt: Date,
  expiresAt: Date
}
```

Notas:

- `expiresAt` marca el momento a partir del cual la sesión deja de conservarse.
- `responseMetadata` solo tiene contenido en mensajes con `role: "assistant"`.
- `citedNewsIds` referencia a `news` y es el vínculo entre una respuesta y las noticias que la
  respaldan.
- `messages` es un arreglo embebido: crece dentro del documento de la sesión y desaparece con ella.

## aiUsage

Registro de consumo de llamadas de IA y su costo estimado.

```javascript
// ============================================================
// aiUsage
// Control del presupuesto de $20
// ============================================================
{
  _id: ObjectId,

  feature:
    "chat" |
    "summary" |
    "image_generation" |
    "classification",

  provider: String,
  model: String,

  userId: ObjectId | null,
  newsId: ObjectId | null,
  chatSessionId: ObjectId | null,

  inputTokens: Number | null,
  outputTokens: Number | null,

  estimatedCostUsd: Number,

  createdAt: Date
}
```

Notas:

- Los tres campos de referencia admiten `null` porque no toda llamada está asociada a un usuario,
  a una noticia y a una sesión al mismo tiempo.
- `estimatedCostUsd` es el campo sobre el que se acumula el gasto del proyecto.

## auditLogs

Registro de las acciones administrativas sobre noticias.

```javascript
// ============================================================
// auditLogs
// Reducido a las acciones administrativas que tendremos
// ============================================================
{
  _id: ObjectId,

  actorId: ObjectId,

  action:
    "news.created" |
    "news.updated" |
    "news.published" |
    "image.generated",

  entityType: "news",
  entityId: ObjectId,

  details: Object,

  createdAt: Date
}
```

Notas:

- `entityType` admite un único valor porque la auditoría cubre solo noticias.
- `actorId` referencia a `users` y es quien ejecuta la acción.
- `details` es un objeto libre: su forma depende de la acción registrada.

## Relaciones

| Campo | Colección origen | Apunta a | Cardinalidad |
| --- | --- | --- | --- |
| `simulatedLocationId` | `users` | `locations` | N:1 |
| `authorId` | `news` | `users` | N:1 |
| `verification.reviewedBy` | `news` | `users` | N:1, opcional |
| `geographicScope.locationIds` | `news` | `locations` | N:M |
| `userId` | `userInteractions` | `users` | N:1 |
| `newsId` | `userInteractions` | `news` | N:1 |
| `context.simulatedLocationId` | `userInteractions` | `locations` | N:1 |
| `userId` | `chatSessions` | `users` | N:1 |
| `simulatedLocationId` | `chatSessions` | `locations` | N:1 |
| `citedNewsIds` | `chatSessions.messages` | `news` | N:M |
| `userId`, `newsId`, `chatSessionId` | `aiUsage` | `users`, `news`, `chatSessions` | N:1, opcionales |
| `actorId` | `auditLogs` | `users` | N:1 |
| `entityId` | `auditLogs` | `news` | N:1 |

## Campos únicos

| Colección | Campo | Motivo |
| --- | --- | --- |
| `users` | `firebaseUid` | Identificador externo de la cuenta |
| `news` | `slug` | Identificador legible de la noticia |

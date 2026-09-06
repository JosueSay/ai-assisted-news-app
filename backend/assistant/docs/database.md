# Lectura de base de datos y esquema MongoDB

## Estado del chatbot original

El código original en `G-T-NOVU-Prototipo/chatbot` no leía una base de datos. Enviaba a OpenAI sólo:

1. el prompt del sistema;
2. el texto de `message`;
3. opcionalmente `previous_response_id`.

La lectura de MongoDB mencionada en el README del prototipo pertenecía a
`backend/app/services/copilot.py`, no al chatbot aislado. Esta copia mueve esa capacidad detrás de un
repositorio para que no quede mezclada con FastAPI ni OpenAI.

## Flujo implementado

```text
POST /chat
  -> valida message y user_id
  -> ContextRepository.get_context(user_id)
       -> EmptyContextRepository, o
       -> MongoContextRepository (projection | novu)
  -> carga prompts/system.md
  -> ChatProvider.generate(prompt, contexto, mensaje)
  -> devuelve message, response_id y model
```

Mongo sólo se consulta cuando la solicitud incluye `user_id` y `MONGODB_URI` está configurada. Las
consultas usan proyecciones de campos y límites explícitos; no se manda el documento de usuario
completo al modelo.

## Opción recomendada: `projection`

La aplicación principal mantiene una colección denormalizada con exactamente los datos que el
asistente tiene permiso de conocer. El repositorio ejecuta una sola consulta:

```javascript
db.assistant_contexts.findOne(
  { user_id: authenticatedUserId },
  { _id: 0, user_id: 0, schema_version: 0, updated_at: 0 }
)
```

Después extrae únicamente el objeto `context`. El esquema base que debe entregarse es:

```json
{
  "_id": "ObjectId",
  "user_id": "string | ObjectId",
  "schema_version": 1,
  "context": {
    "person": {
      "first_name": "Diego",
      "locale": "es-GT",
      "timezone": "America/Guatemala"
    },
    "preferences": {
      "topics": ["tecnología", "economía"],
      "language": "es"
    },
    "saved_items": []
  },
  "updated_at": "Date"
}
```

`context` es deliberadamente extensible. Para una aplicación de noticias puede contener, por
ejemplo, preferencias temáticas, fuentes permitidas, artículos guardados y un historial reciente
acotado. Para NOVU puede contener `savings_profile`, `goals` y movimientos recientes. Al cambiar sus
campos también hay que actualizar el prompt para explicar unidades, significado y restricciones.

El validador ejecutable y los índices están en [`../docker/mongo-init.js`](../docker/mongo-init.js):

- índice único `{user_id: 1}`;
- índice `{updated_at: -1}`;
- `schema_version` entero;
- `updated_at` como BSON Date;
- `context` como documento.

Esta opción reduce exposición de datos, costo de tokens y acoplamiento con el esquema operativo. La
aplicación dueña de los datos debe actualizar la proyección cuando cambien las entidades fuente.

## Opción heredada: `novu`

Con `MONGODB_CONTEXT_MODE=novu`, el repositorio usa el mismo modelo del backend integrado original.
Convierte `user_id` a `ObjectId` y lee en paralelo:

| Colección | Filtro | Campos/límite |
|---|---|---|
| `users` | `_id = user_id` | nombre, locale, zona horaria y estado |
| `savings_profiles` | `user_id = user_id` | perfil de ahorro sin `_id` |
| `goals` | `owner_id = user_id`, no borradas | últimas 20 |
| `contributions` | del usuario, `posted` o `reversed` | últimas 50 |
| `withdrawal_requests` | solicitadas por el usuario, `approved` o `executed` | últimas 50 |
| `activities` | `user_id = user_id` | últimas 30 |

Los montos siguen el esquema NOVU: enteros en centavos (`amount_minor`) y moneda ISO (`GTQ`), nunca
`float`. Los índices mínimos para estas consultas son:

```javascript
db.savings_profiles.createIndex({ user_id: 1 }, { unique: true });
db.goals.createIndex({ owner_id: 1, updated_at: -1 });
db.contributions.createIndex({ user_id: 1, occurred_at: -1 });
db.withdrawal_requests.createIndex({ requester_id: 1, created_at: -1 });
db.activities.createIndex({ user_id: 1, occurred_at: -1 });
```

## Qué modificar para usar la Mongo existente

1. Definir `MONGODB_URI` y `MONGODB_DATABASE` en el gestor de secretos del despliegue.
2. Elegir `projection` si se puede construir `assistant_contexts`; es la opción recomendada.
3. Si se usa otra colección o tipo de identificador, cambiar
   `MONGODB_CONTEXT_COLLECTION` y `MONGODB_USER_ID_TYPE`.
4. Si el esquema existente es distinto, modificar sólo
   `repositories/mongo.py::_get_projection_context` o agregar otro repositorio; no tocar el proveedor
   de OpenAI.
5. Ajustar `prompts/system.md` para describir el dominio, las unidades y qué hacer cuando falten
   datos.
6. Obtener `user_id` de autenticación confiable. El cuerpo actual sirve para integración y demo, no
   constituye autorización.
7. Crear un usuario Mongo de sólo lectura limitado a las colecciones necesarias y habilitar TLS en
   producción.

## Datos que no deben enviarse al modelo

- contraseñas o hashes;
- tokens de sesión, API keys o secretos;
- números completos de tarjeta o cuenta;
- documentos KYC, DPI, direcciones o teléfonos si no son indispensables;
- documentos Mongo completos por comodidad;
- historiales sin límite.

El bloque se serializa como JSON y se etiqueta explícitamente como datos, no instrucciones. Esa
medida ayuda contra prompt injection almacenada en la DB, pero no reemplaza listas de campos,
autorización, validación ni límites.

## Conversación y persistencia

Esta copia conserva `previous_response_id` y `store=true` para mantener compatibilidad con el
chatbot original. Si se necesita que OpenAI no almacene el estado del proveedor:

1. crear `assistant_conversations` y `assistant_messages`;
2. guardar cada turno como documento separado (evitar arreglos de mensajes sin límite);
3. leer los últimos N mensajes por conversación y usuario autenticado;
4. enviarlos como `input`;
5. cambiar el proveedor a `store=false` y dejar de usar `previous_response_id`.

Esquema mínimo sugerido:

```json
{
  "assistant_conversations": {
    "_id": "ObjectId",
    "user_id": "string | ObjectId",
    "status": "active | archived",
    "last_message_at": "Date",
    "created_at": "Date"
  },
  "assistant_messages": {
    "_id": "ObjectId",
    "conversation_id": "ObjectId",
    "sender": "user | assistant",
    "content": "string",
    "model": "string | null",
    "prompt_version": "string",
    "created_at": "Date"
  }
}
```

Índices: `{user_id: 1, last_message_at: -1}` y
`{conversation_id: 1, created_at: -1, _id: -1}`.

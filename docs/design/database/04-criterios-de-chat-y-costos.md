# Criterios de chat y costos

Parte de la [documentación de base de datos](README.md).

Reglas sobre las sesiones de chat, los metadatos que acompañan cada respuesta, el registro de
consumo de IA y la auditoría administrativa.

## Sesiones temporales

Reglas:

- `chatSessions` es una colección temporal: `expiresAt` marca el momento a partir del cual la
  sesión deja de conservarse.
- Las conversaciones no se preservan entre sesiones.
- El período de vigencia es un parámetro del diseño y se fija en la tabla de
  [parámetros](README.md#parámetros-del-diseño).
- Los mensajes viven embebidos en el documento de la sesión, de modo que expiran junto con ella.

## Estrategia de la respuesta

`responseMetadata.strategy` declara con qué recurso se construyó la respuesta.

| Valor | Significado | Consumo de IA |
| --- | --- | --- |
| `database_query` | La respuesta se resolvió con datos de la base. | Ninguno |
| `template` | La respuesta se resolvió con una respuesta predefinida. | Ninguno |
| `llm` | La respuesta se construyó con un modelo de lenguaje. | Registrado en `aiUsage` |

Reglas:

- `aiUsed` es coherente con `strategy`: solo vale verdadero cuando `strategy` es `llm`.
- Toda respuesta con `strategy = "llm"` tiene su registro correspondiente en `aiUsage`.
- Las respuestas con `strategy` `database_query` o `template` no generan registro en `aiUsage`
  porque su costo de API es cero.

## Intención de la consulta

`responseMetadata.intent` clasifica qué pidió el usuario.

| Valor | Significado |
| --- | --- |
| `recent_news` | Noticias recientes. |
| `regional_news` | Noticias de una región. |
| `topic_news` | Noticias de un tema. |
| `news_detail` | Detalle de una noticia concreta. |
| `summarize` | Resumen de contenido. |
| `explain` | Explicación de contenido. |
| `unsupported` | Petición fuera del alcance de la aplicación. |

Reglas:

- `recent_news`, `regional_news`, `topic_news` y `news_detail` se corresponden con información que
  existe en la base de datos.
- `summarize` y `explain` se corresponden con elaboración de contenido.
- `unsupported` identifica peticiones ajenas al dominio de noticias. Estas peticiones no generan
  registro en `aiUsage`.

## Noticias citadas

Reglas:

- `citedNewsIds` contiene las noticias en las que se apoya la respuesta y es el vínculo que
  permite rastrear su procedencia.
- Las fuentes no se copian dentro del mensaje: se alcanzan a través de la noticia citada y su
  arreglo `sources`.
- Solo pueden citarse noticias con `status = "published"`.

## Nivel de confianza

`responseMetadata.confidence` califica la respuesta con `high`, `medium` o `low`.

Reglas:

- El nivel se sustenta en el estado de verificación y en la cantidad y calidad de las fuentes de
  las noticias citadas.
- No expresa la seguridad declarada por el modelo de lenguaje.
- `uncertainty` describe en texto qué queda sin resolver, y admite `null` cuando no aplica.
- Cuando una noticia citada tiene un `verification.status` distinto de `confirmed`, esa condición
  debe quedar reflejada en la respuesta.

## Consumo y presupuesto de IA

Reglas:

- Cada llamada real a un proveedor de IA genera un registro en `aiUsage`.
- El gasto acumulado del proyecto se obtiene sumando `estimatedCostUsd`.
- El presupuesto total del proyecto es de 20 USD; ese límite es el que se contrasta contra el
  acumulado.
- `feature` distingue el origen del consumo entre `chat`, `summary`, `image_generation` y
  `classification`, lo que permite atribuir el gasto por funcionalidad.
- `inputTokens` y `outputTokens` admiten `null` cuando el proveedor no los reporta;
  `estimatedCostUsd` siempre está presente.
- Las referencias `userId`, `newsId` y `chatSessionId` permiten atribuir el consumo a una persona,
  una noticia o una conversación cuando corresponde.

## Auditoría

`auditLogs.action` registra las acciones administrativas sobre noticias.

| Valor | Acción registrada |
| --- | --- |
| `news.created` | Creación de una noticia. |
| `news.updated` | Modificación de una noticia. |
| `news.published` | Publicación de una noticia. |
| `image.generated` | Generación de una imagen. |

Reglas:

- Toda acción queda asociada a quien la ejecuta mediante `actorId`.
- `entityType` vale siempre `news`: la auditoría cubre únicamente esa entidad.
- `details` es un objeto libre cuyo contenido depende de la acción registrada.
- La auditoría es un registro histórico: sus documentos no se modifican después de creados.

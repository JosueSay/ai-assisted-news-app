# Base de datos

Parte de la [documentación de diseño](../README.md).

Bloque de documentos que define el contenido de la base de datos y las reglas que rigen sus datos.

## Documentos

| Documento | Contenido |
| --- | --- |
| [01 Colecciones](01-colecciones.md) | Esquema completo, campo por campo, y relaciones entre colecciones |
| [02 Criterios de contenido](02-criterios-de-contenido.md) | Estados de publicación, verificación, fuentes, imágenes y uso declarado de IA |
| [03 Criterios de personalización](03-criterios-de-personalizacion.md) | Interacciones registradas, intereses, ubicación y composición del feed |
| [04 Criterios de chat y costos](04-criterios-de-chat-y-costos.md) | Sesiones temporales, nivel de confianza, consumo de IA y auditoría |
| [05 Tiempo de lectura](05-tiempo-de-lectura.md) | Campos de duración estimada y datos derivables |
| [06 Decisiones descartadas](06-decisiones-descartadas.md) | Campos y colecciones que se quitaron, con su motivo |
| [07 Diagrama](07-diagrama.md) | Colecciones, documentos embebidos y referencias lógicas |

## Cómo leer los criterios

Cada criterio se expresa como una condición sobre campos concretos. La documentación fija el
significado del dato, no el mecanismo que lo produce.

- Correcto: una noticia incierta es aquella cuyo `verification.status` vale `developing`,
  `insufficient_sources` o `conflicting_sources`.
- Fuera de alcance: el procedimiento por el cual se determina cuál de esos tres valores
  corresponde.

## Parámetros del diseño

Valores que los criterios dejan abiertos. Se fijan aquí y se citan desde el documento que los usa.

| Parámetro | Valor | Dónde se usa | Efecto de cambiarlo |
| --- | --- | --- | --- |
| Velocidad de lectura de referencia | 200 palabras por minuto | [Tiempo de lectura](05-tiempo-de-lectura.md) | Obliga a recalcular `estimatedReadingMinutes` en toda la colección |
| Umbral de lectura para `read` | 90 % del contenido | [Criterios de personalización](03-criterios-de-personalizacion.md) | Cambia el significado de las interacciones ya registradas |
| Vigencia de una sesión de chat | 3600 segundos | [Criterios de chat y costos](04-criterios-de-chat-y-costos.md) | Determina `chatSessions.expiresAt` |
| Presupuesto total de IA | 20 USD | [Criterios de chat y costos](04-criterios-de-chat-y-costos.md) | Es el límite contra el que se contrasta la suma de `estimatedCostUsd` |

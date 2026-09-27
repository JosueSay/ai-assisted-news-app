# Diseño de base de datos

Diseño de la base de datos MongoDB de la aplicación de noticias asistida por IA.

Esta documentación describe únicamente cómo queda la base de datos y qué reglas rigen sus datos.
No describe el backend, ni algoritmos, ni procedimientos de implementación. Cuando aparece una
regla, se enuncia el criterio y los campos que lo expresan, no la forma de ejecutarlo.

## Alcance

Dentro del alcance:

- colecciones, campos, tipos y valores permitidos,
- relaciones entre colecciones,
- significado de cada valor de enumeración,
- reglas que deben cumplirse sobre los datos,
- datos que la estructura permite obtener.

Fuera del alcance:

- cómo se calcula o decide un valor,
- endpoints, servicios, capas de aplicación,
- algoritmos de ordenamiento, clasificación o verificación,
- lógica de interfaz.

Ejemplo de la distinción: la documentación establece que una noticia se considera confirmada
cuando `verification.status = "confirmed"`. No establece con qué procedimiento el equipo llega a
esa conclusión.

## Documentos

| Documento | Contenido |
| --- | --- |
| [Colecciones](database/01-colecciones.md) | Esquema de cada colección, campos y relaciones |
| [Criterios de contenido](database/02-criterios-de-contenido.md) | Publicación, verificación, fuentes, imágenes e IA declarada |
| [Criterios de personalización](database/03-criterios-de-personalizacion.md) | Interacciones, intereses, ubicación y orden del feed |
| [Criterios de chat y costos](database/04-criterios-de-chat-y-costos.md) | Sesiones de chat, confianza, presupuesto de IA y auditoría |
| [Tiempo de lectura](database/05-tiempo-de-lectura.md) | Campos de duración estimada y datos que habilitan |
| [Decisiones descartadas](database/06-decisiones-descartadas.md) | Qué se quitó del diseño y por qué |
| [Checklist de replicación](99-checklist-replicacion.md) | Verificación de que la base se puede recrear desde cero |

El alcance es la base de datos. Infraestructura, despliegue y operación no forman parte de esta
documentación.

## Convenciones

- Colecciones en plural y `camelCase` compuesto cuando aplica: `users`, `userInteractions`.
- Campos en `camelCase`.
- Identificador primario `_id` de tipo `ObjectId` en todas las colecciones.
- Fechas en tipo `Date` de BSON, en UTC.
- Las enumeraciones se escriben como lista de literales permitidos; cualquier valor fuera de la
  lista es inválido.
- `null` se usa solo cuando la ausencia del valor tiene significado propio.
- Idioma: prosa en español, nombres de colecciones y campos en inglés.

## Colecciones del diseño

| Colección | Naturaleza | Propósito |
| --- | --- | --- |
| `users` | Persistente | Cuenta, preferencias declaradas e intereses inferidos |
| `locations` | Catálogo precargado | Ubicaciones seleccionables y alcance geográfico |
| `news` | Persistente | Noticia, su procedencia, verificación y alcance |
| `userInteractions` | Persistente | Registro de lectura usado para inferir intereses |
| `chatSessions` | Temporal con expiración | Conversación y metadatos de cada respuesta |
| `aiUsage` | Persistente | Consumo y costo estimado de llamadas de IA |
| `auditLogs` | Persistente | Acciones administrativas sobre noticias |

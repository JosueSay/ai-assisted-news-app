# Tiempo de lectura

Parte de la [documentación de base de datos](README.md).

Incorporación de la duración estimada de lectura al modelo. Es una mejora de costo nulo: no
requiere IA, no genera registros en `aiUsage` y se sostiene sobre un dato que la noticia ya
contiene. Su valor no está en mostrar un rótulo, sino en que convierte `dwellTimeSeconds` en una
medida comparable entre noticias de longitud distinta.

## Campos

Se agregan dos campos a `news` y ninguno a las demás colecciones.

| Campo | Tipo | Obligatorio | Descripción |
| --- | --- | --- | --- |
| `wordCount` | Number | Sí | Cantidad de palabras del cuerpo de la noticia. |
| `estimatedReadingMinutes` | Number | Sí | Duración estimada de lectura, en minutos enteros. |

```javascript
// ------------------------------------------
// Lectura
// ------------------------------------------
wordCount: Number,
estimatedReadingMinutes: Number,
```

## Regla de cálculo

```text
estimatedReadingMinutes = ceil(wordCount / 200)
```

Reglas:

- La velocidad de referencia es de 200 palabras por minuto. Es un parámetro del diseño: si se
  ajusta, se ajusta en este documento y se recalcula el campo en toda la colección.
- El redondeo es hacia arriba y el valor mínimo es 1: ninguna noticia publicada muestra 0 minutos.
- `wordCount` cuenta las palabras de `content`. No incluye `title`, `summary`, pies de imagen ni
  créditos.
- Ambos campos son enteros no negativos.

## Momento en que se fijan

Reglas:

- Los dos campos quedan establecidos al pasar la noticia a `status = "published"`, junto con
  `publishedAt`.
- Toda noticia con `status = "published"` tiene `wordCount` y `estimatedReadingMinutes` con valor.
- Si `content` cambia después de publicada, ambos campos se recalculan y `updatedAt` se actualiza.
- En estado `draft` los campos pueden estar ausentes o desactualizados; no se consideran válidos
  hasta la publicación.

## Coherencia

- `estimatedReadingMinutes` siempre es consistente con `wordCount` según la regla de cálculo: no
  es un valor que se edite por separado.
- El campo es un dato derivado y almacenado de forma deliberada, para no recalcularlo en cada
  consulta ni depender de `content` para ordenar o filtrar por duración.
- Al ser derivado, ante cualquier discrepancia el dato autoritativo es `content`.

## Datos que habilita

La duración estimada no aporta por sí sola: aporta al cruzarse con `userInteractions`. Ninguno de
los datos siguientes requiere campos adicionales.

### Proporción de lectura

```text
proporción de lectura = dwellTimeSeconds / (estimatedReadingMinutes * 60)
```

Es el dato central que desbloquea la mejora: normaliza el tiempo de permanencia contra la longitud
de la noticia. Sin él, 90 segundos en una nota de 2 minutos y 90 segundos en un reportaje de 12
minutos son indistinguibles.

| Rango orientativo | Lectura de la señal |
| --- | --- |
| Muy por debajo de 1 | Apertura breve, sin lectura sostenida |
| Cercana a 1 | Lectura completa a ritmo normal |
| Por encima de 1 | Lectura detenida o relectura |

Los umbrales concretos no se fijan aquí: se fija que el dato es calculable a partir de campos
existentes.

### Calidad de la señal `read`

- `read` se registra por avance en el contenido. Contrastarlo con la proporción de lectura permite
  distinguir un avance rápido de una lectura efectiva.
- La combinación de `type = "read"` con una proporción de lectura razonable es una señal más firme
  que cualquiera de las dos por separado.

### Peso de la señal para intereses inferidos

- Permite que `inferredInterests[].score` distinga una apertura de una lectura sostenida, en lugar
  de tratar toda interacción por igual.
- La escala del peso queda fuera de esta documentación; el dato necesario para aplicarla existe.

### Segmentación por duración

- `estimatedReadingMinutes` permite agrupar el catálogo por lectura corta, media o larga y usar esa
  agrupación como criterio de composición del feed.
- Aporta a la diversidad descrita en
  [criterios de personalización](03-criterios-de-personalizacion.md): la variedad de duración es
  independiente de los intereses aprendidos.

### Métricas agregadas

Datos obtenibles cruzando `news` con `userInteractions`:

| Métrica | Campos involucrados |
| --- | --- |
| Proporción media de lectura por tema | `news.topics`, `estimatedReadingMinutes`, `dwellTimeSeconds` |
| Proporción media de lectura por ubicación | `news.geographicScope`, `userInteractions.context.simulatedLocationId` |
| Relación entre longitud y lectura completa | `wordCount`, `userInteractions.type` |
| Longitud típica de las noticias más leídas | `wordCount`, conteo de interacciones |
| Abandono por posición en el feed | `context.feedPosition`, proporción de lectura |
| Tiempo total de lectura por usuario | `dwellTimeSeconds` agregado por `userId` |

## Alcance de la mejora

- Se agregan únicamente `wordCount` y `estimatedReadingMinutes` en `news`.
- No se agregan campos a `userInteractions`: la proporción de lectura es derivable y almacenarla
  duplicaría un dato que depende de otros dos.
- No se crean colecciones nuevas.
- No interviene ningún proveedor de IA, por lo que la mejora no afecta el presupuesto descrito en
  [criterios de chat y costos](04-criterios-de-chat-y-costos.md).

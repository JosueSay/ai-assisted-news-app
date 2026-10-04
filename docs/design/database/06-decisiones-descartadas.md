# Decisiones descartadas

Parte de la [documentación de base de datos](README.md).

Campos y colecciones que se consideraron y quedaron fuera del modelo, con el motivo. El registro
evita que vuelvan a proponerse y explica ausencias que de otro modo parecerían olvidos.

## Prioridad editorial

Se eliminó por completo el bloque `editorial` de `news`.

Motivo: el autor no debe poder aumentar artificialmente la prioridad de su propia noticia. La
posición en el feed se determina con ubicación, temas seleccionados, intereses inferidos y
actualidad, según lo descrito en
[criterios de personalización](03-criterios-de-personalizacion.md).

Consecuencia: no existe ningún campo en `news` que influya directamente en el orden del feed por
decisión del autor.

## Interacciones fuera del modelo

Se eliminaron de `userInteractions.type` los valores `saved`, `shared`, `hidden` e `impression`.

Motivo: esas funciones no están definidas en la aplicación. Registrar interacciones que no
existen en la experiencia produce datos vacíos y una colección que no refleja el producto.

Consecuencia: `userInteractions.type` admite solo `opened` y `read`. Si alguna de esas funciones
se incorpora más adelante, el valor correspondiente se agrega en ese momento.

## Cambio de ubicación como interacción

Se eliminó el valor `location_change` de `userInteractions.type`.

Motivo: la ubicación vigente ya vive en `users.simulatedLocationId`, y cada interacción conserva
la ubicación del momento en `context.simulatedLocationId`. Un tipo de interacción adicional
duplicaría información que el modelo ya tiene.

Consecuencia: `userInteractions` contiene exclusivamente interacciones de lectura.

## Estado de revisión separado

No existe un estado intermedio entre `draft` y `published` en `news.status`.

Motivo: no hay un proceso de revisión separado en el flujo de trabajo previsto.

Consecuencia: la revisión, cuando ocurre, se registra en `verification.reviewedBy` y
`verification.reviewedAt`, sin bloquear la publicación mediante un estado propio.

## Auditoría de entidades distintas de noticias

`auditLogs.entityType` admite un único valor: `news`.

Motivo: las acciones administrativas previstas recaen solo sobre noticias.

Consecuencia: el campo se conserva como tal, y no como una enumeración, para permitir ampliarlo
sin cambiar la forma del documento si en el futuro se auditan otras entidades.

## Proporción de lectura almacenada

No se agrega un campo con la proporción de lectura en `userInteractions`.

Motivo: es un valor derivable de `dwellTimeSeconds` y `news.estimatedReadingMinutes`.
Almacenarlo crearía un tercer dato que hay que mantener sincronizado con los otros dos.

Consecuencia: la proporción se calcula al consultar, según lo descrito en
[tiempo de lectura](05-tiempo-de-lectura.md).

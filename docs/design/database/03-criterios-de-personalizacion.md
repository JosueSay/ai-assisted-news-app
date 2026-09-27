# Criterios de personalización

Parte de la [documentación de base de datos](README.md).

Reglas sobre los datos que sostienen la experiencia personalizada: qué interacciones se registran,
cómo se distinguen los intereses declarados de los inferidos, qué papel cumple la ubicación y qué
señales intervienen en el orden del feed. La documentación indica qué datos entran en cada
criterio, no el algoritmo que los combina.

## Interacciones registradas

`userInteractions.type` admite dos valores y ninguno más. Toda interacción que no esté en esta
lista queda fuera del modelo, según lo detallado en
[decisiones descartadas](06-decisiones-descartadas.md).

| Valor | Cuándo se registra |
| --- | --- |
| `opened` | El usuario entra al detalle de una noticia. |
| `read` | El usuario alcanza el umbral de lectura definido, en el orden del 90 % del contenido. |

Reglas:

- El umbral de `read` se fija por debajo del final absoluto del contenido: exigir el final exacto
  del desplazamiento dejaría fuera lecturas completas.
- `dwellTimeSeconds` registra el tiempo activo dentro de la noticia. Es la señal que distingue una
  apertura accidental de un interés real.
- `dwellTimeSeconds` admite `null` cuando la medición no está disponible; su ausencia no invalida
  el registro de la interacción.
- Cada interacción conserva en `context` la ubicación vigente y la posición en el feed, de modo
  que el registro siga siendo interpretable aunque el usuario cambie de ubicación más adelante.

## Intereses

El modelo separa dos orígenes distintos y no los mezcla en el mismo campo.

| Origen | Campo | Naturaleza |
| --- | --- | --- |
| Declarado | `users.onboarding.selectedTopics` | Temas elegidos explícitamente durante el onboarding. |
| Inferido | `users.inferredInterests` | Temas derivados del comportamiento registrado en `userInteractions`. |

Reglas:

- El interés inicial, antes de que exista historial, proviene de `onboarding.selectedTopics`.
- El interés inferido se sostiene sobre `opened`, `read` y el tiempo de lectura; esas señales
  elevan gradualmente el `score` de los temas relacionados.
- `inferredInterests[].score` se mueve en el rango de 0 a 1.
- `inferredInterests[].updatedAt` indica la última vez que ese tema cambió de puntaje.
- Los temas de `inferredInterests` comparten vocabulario con `news.topics`, que es el campo con el
  que se comparan.

## Ubicación

Reglas:

- La ubicación vigente del usuario es `users.simulatedLocationId` y es un valor único, no un
  histórico.
- La ubicación inicial se selecciona durante el onboarding y después puede cambiarse manualmente.
- El cambio de ubicación no genera un registro en `userInteractions`: esa colección solo contiene
  interacciones de lectura.
- El histórico implícito de ubicaciones queda en `userInteractions.context.simulatedLocationId`,
  que conserva la ubicación de cada lectura.

## Relevancia geográfica

Reglas:

- La relevancia geográfica se establece comparando `users.simulatedLocationId` contra
  `news.geographicScope.locationIds`.
- Las noticias con `geographicScope.level = "international"` no requieren coincidencia con una
  ciudad concreta.
- Ambos extremos de la comparación usan la misma enumeración de niveles, de modo que una ubicación
  de nivel ciudad y un alcance de nivel país son comparables entre sí.

## Orden del feed

Señales que participan en la posición de una noticia en el feed:

| Señal | Campo |
| --- | --- |
| Ubicación | `users.simulatedLocationId` frente a `news.geographicScope` |
| Temas declarados | `users.onboarding.selectedTopics` frente a `news.topics` |
| Intereses inferidos | `users.inferredInterests` frente a `news.topics` |
| Actualidad | `news.publishedAt` |

Reglas:

- No existe ningún campo con el que el autor pueda elevar la posición de su propia noticia. El
  orden depende exclusivamente de las señales de la tabla.
- La combinación concreta de esas señales queda fuera de esta documentación: aquí se fija qué
  datos están disponibles y cuáles no pueden intervenir.

## Diversidad del feed

Requisito del proyecto sobre la composición del feed:

- El feed debe poder exponer contenido importante de alcance local, nacional o internacional
  aunque no coincida con los intereses aprendidos del usuario.
- Los campos que hacen posible cumplirlo son `news.geographicScope.level` y
  `news.publishedAt`, que permiten identificar contenido relevante con independencia de
  `inferredInterests`.
- La forma de reservar ese espacio en el feed no se define aquí.

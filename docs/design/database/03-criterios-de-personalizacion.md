# Criterios de personalización

Parte de la [documentación de base de datos](README.md).

Reglas sobre los datos que sostienen la experiencia personalizada: qué interacciones se registran,
cómo se distinguen los intereses declarados de los inferidos, qué papel cumple la ubicación, cómo
se puntúa el feed y qué diversidad se conserva.

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
- Para la primera versión, se conserva un evento por combinación de usuario, noticia y tipo. Un
  reintento secuencial no crea otra interacción ni duplica su aporte. La primera ubicación y
  posición se preservan; el tiempo activo de `opened` puede actualizarse al salir de la noticia.
- El índice compuesto de usuario/noticia/tipo es de consulta, no único: esta deduplicación no es
  una garantía ante escrituras concurrentes.

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
- Una apertura aporta `0.02` una sola vez cuando acumula al menos 30 segundos activos; una lectura
  al 90 % aporta `0.08` una sola vez. Si todo el cuerpo cabe en el viewport, se requieren además
  5 segundos activos con al menos 90 % visible, para no convertir una apertura fugaz en lectura.
  Cada aporte se aplica a cada tema de la noticia y el puntaje se limita a `1.0`. Los temas
  declarados no se modifican por este cálculo.
- El backend reconstruye los puntajes a partir de las interacciones persistidas; repetir una
  petición puede reparar una escritura parcial sin sumar dos veces el mismo tipo de evento.

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
- Se suman estos componentes deterministas, sin añadir campos ni requerir un modelo de IA:

  | Componente | Puntuación |
  | --- | --- |
  | Ubicación exacta en `geographicScope.locationIds` | 30 |
  | Alcance `international`, si no hubo coincidencia exacta | 10 |
  | Una o más coincidencias con `onboarding.selectedTopics` | 20 |
  | Interés inferido coincidente | `20 × el mayor score coincidente` |
  | Actualidad | `max(0, 20 × (1 − edad_en_días / 14))`; fecha futura cuenta como edad cero |

- Una fecha de publicación ausente aporta cero puntos de actualidad. Se ordena por puntuación
  descendente, fecha de publicación descendente e identificador ascendente. El servidor puntúa
  todos los candidatos `published` antes de devolver como máximo 50; el cliente conserva ese orden.
- La razón de selección expuesta al lector identifica la señal positiva de mayor puntuación; los
  empates siguen el orden ubicación, tema declarado, interés inferido y actualidad.
- Al salir del detalle se vuelve a consultar el feed después de finalizar el envío del tiempo
  activo. Una lectura que termina de guardarse después también provoca una nueva consulta.
  Mientras el detalle está abierto, el ranking y las mediciones de lectura se mantienen estables.

## Diversidad del feed

Requisito del proyecto sobre la composición del feed:

- El feed debe poder exponer contenido relevante por alcance local, nacional o internacional
  aunque no coincida con los intereses aprendidos del usuario.
- Los campos que hacen posible cumplirlo son `news.geographicScope.level` y
  `news.publishedAt`, que permiten identificar contenido relevante con independencia de
  `inferredInterests`.
- La cobertura geográfica y la actualidad son el proxy disponible; no representan una declaración
  editorial de importancia ni sustituyen una decisión de revisión de contenido.
- En las primeras diez posiciones se reservan, cuando existe contenido, las posiciones 4 y 9 para
  las noticias más recientes de alcance internacional o con ubicación distinta de la persona.
  Si falta oferta, la posición se completa con la siguiente noticia del ranking; nunca se inventa
  contenido. La noticia reservada explica que amplía la cobertura geográfica.
- Las reservas eligen entre noticias aún no mostradas por fecha de publicación descendente e
  identificador ascendente en caso de empate, con fechas ausentes al final. Los temas declarados
  y los intereses inferidos no alteran ese orden de diversidad.
- Las posiciones 1–3, que se muestran como principal y secundarias, respetan el orden compuesto por
  el servidor. La diversidad no elimina noticias locales pertinentes ni cambia sus datos.

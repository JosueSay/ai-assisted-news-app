# Criterios de contenido

Parte de la [documentación de base de datos](README.md).

Reglas que rigen los datos de una noticia: su estado de publicación, su verificación, su
procedencia, su imagen y su alcance geográfico. Cada criterio define qué significa un valor y qué
debe cumplirse, no el procedimiento para llegar a él.

## Publicación

`news.status` tiene dos valores y no existe un estado intermedio de revisión.

| Valor | Significado |
| --- | --- |
| `draft` | La noticia solo existe en administración. No aparece en la aplicación móvil ni puede ser citada por el chat. |
| `published` | La noticia es visible en la aplicación móvil y puede ser citada por el chat. |

Reglas:

- Al pasar de `draft` a `published` se establece `publishedAt`.
- Mientras `status` sea `draft`, `publishedAt` vale `null`.
- Solo las noticias con `status = "published"` pueden aparecer en `chatSessions.messages[].responseMetadata.citedNewsIds`.

## Verificación

`news.verification.status` declara qué tan asentada está la información. La documentación fija el
significado de cada valor; no define con qué método se determina.

| Valor | Significado |
| --- | --- |
| `confirmed` | Noticia confirmada. |
| `developing` | Hecho en desarrollo, sujeto a cambios. |
| `insufficient_sources` | No hay respaldo suficiente. |
| `conflicting_sources` | Las fuentes disponibles se contradicen. |

Reglas:

- Una noticia se considera confirmada únicamente cuando `verification.status = "confirmed"`.
- Cualquier otro valor corresponde a una noticia incierta, y esa condición debe comunicarse de
  forma explícita donde se muestre la noticia.
- `reviewedBy`, `reviewedAt` y `notes` admiten `null`: registran la revisión cuando existe, sin
  condicionar el valor de `status`.

## Fuentes

`news.sources` contiene la procedencia de la noticia. Cada elemento declara de dónde proviene la
información.

| Valor de `sourceType` | Significado |
| --- | --- |
| `official` | Fuente institucional u oficial. |
| `media` | Medio de comunicación. |
| `primary_source` | Documento o material original. |
| `witness` | Testimonio directo. |
| `other` | Cualquier otro origen. |

Reglas:

- `accessedAt` siempre está presente: indica cuándo se consultó la fuente.
- `publishedAt` admite `null` porque no toda fuente declara fecha de publicación.
- `supports` indica qué afirmación de la noticia respalda esa fuente, y admite `null`.
- La trazabilidad de una respuesta del chat se resuelve en dos saltos:
  `citedNewsIds` apunta a las noticias utilizadas y cada noticia contiene sus propias `sources`.

## Imagen

`news.image.type` declara la naturaleza de la imagen.

| Valor | Significado |
| --- | --- |
| `photograph` | Fotografía real. |
| `illustration` | Ilustración no fotográfica. |
| `ai_generated` | Imagen generada con IA. |
| `ai_modified` | Imagen real alterada con IA. |
| `none` | La noticia no tiene imagen. |

Reglas:

- Cuando `type` vale `ai_generated` o `ai_modified`, `aiDisclosure` debe tener contenido.
- Una imagen con `type` `ai_generated` o `ai_modified` no puede presentarse como fotografía real.
- Cuando `type` vale `none`, `url` y `alt` valen `null`.
- `credit` y `rights` registran autoría y condiciones de uso cuando existen.

## Uso declarado de IA

`news.aiAssistance` deja constancia de qué partes de la noticia se produjeron con asistencia de IA.

| Campo | Qué declara |
| --- | --- |
| `summaryGenerated` | El resumen se generó con IA. |
| `topicsGenerated` | Los temas se generaron con IA. |
| `imageGenerated` | La imagen se generó con IA. |
| `humanReviewed` | Una persona revisó el contenido asistido por IA. |

Reglas:

- Los cuatro campos son booleanos y siempre están presentes.
- `imageGenerated` y `image.type` deben ser coherentes entre sí: una imagen declarada como
  generada por IA se refleja en ambos lugares.

## Alcance geográfico

`news.geographicScope` define a qué territorio pertenece la noticia.

| Valor de `level` | Significado |
| --- | --- |
| `city` | Alcance de ciudad. |
| `region` | Alcance regional. |
| `country` | Alcance nacional. |
| `international` | Alcance internacional. |

Reglas:

- `locationIds` referencia entradas de `locations` y puede contener más de una.
- Cuando `level` vale `international`, la noticia no depende de coincidir con una ciudad concreta.
- La comparación entre el alcance de la noticia y la ubicación del usuario se documenta en
  [criterios de personalización](03-criterios-de-personalizacion.md).

## Temas y palabras clave

- `topics` es la lista de temas de la noticia y es el campo que se compara con
  `users.onboarding.selectedTopics` y con `users.inferredInterests[].topic`.
- `keywords` acompaña a la noticia para su localización, sin participar en la definición de
  intereses.
- Ambos son arreglos de cadenas y comparten vocabulario con los temas ofrecidos en el onboarding.

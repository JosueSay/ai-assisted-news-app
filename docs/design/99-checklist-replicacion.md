# Checklist de replicación

Parte de la [documentación de diseño](README.md).

Verificación de que la base de datos se puede recrear desde cero leyendo únicamente esta
documentación. Se ejecuta sobre un entorno limpio: si algún paso obliga a preguntar o a leer
código, la documentación está incompleta y se corrige el documento que falló.

## Registro de ejecuciones

| Fecha | Entorno | Ejecutado por | Resultado | Huecos encontrados |
| --- | --- | --- | --- | --- |
| | | | | |

## 1. Estructura

- [ ] Las siete colecciones de [colecciones](database/01-colecciones.md) existen con el nombre documentado.
- [ ] Cada campo tiene tipo, obligatoriedad y significado definidos.
- [ ] Las enumeraciones admiten exactamente los valores listados, sin valores extra.
- [ ] `users.firebaseUid` y `news.slug` son únicos.
- [ ] `chatSessions` expira según `expiresAt`.

## 2. Catálogo y datos iniciales

- [ ] El catálogo de `locations` está cargado y sus entradas tienen `active` definido.
- [ ] Los temas usados en `onboarding.selectedTopics` y en `news.topics` comparten vocabulario.
- [ ] Ningún dato inicial contiene información personal real.

## 3. Reglas de contenido

- [ ] Toda noticia con `status = "published"` tiene `publishedAt`.
- [ ] Toda noticia con `status = "draft"` tiene `publishedAt` en `null`.
- [ ] Toda imagen con `type` `ai_generated` o `ai_modified` tiene `aiDisclosure` con contenido.
- [ ] `image.type` y `aiAssistance.imageGenerated` son coherentes entre sí.
- [ ] Toda noticia publicada tiene al menos el estado de verificación definido.

## 4. Tiempo de lectura

- [ ] Toda noticia publicada tiene `wordCount` y `estimatedReadingMinutes`.
- [ ] `estimatedReadingMinutes` es igual a `ceil(wordCount / 200)` y nunca vale 0.
- [ ] La proporción de lectura se puede calcular cruzando `userInteractions.dwellTimeSeconds` con `news.estimatedReadingMinutes`.

## 5. Personalización

- [ ] `userInteractions.type` admite solo `opened` y `read`.
- [ ] Cada interacción conserva `context.simulatedLocationId`.
- [ ] `inferredInterests[].score` se mantiene dentro del rango de 0 a 1.
- [ ] Ningún campo de `news` permite al autor alterar la posición en el feed.

## 6. Chat y costos

- [ ] `responseMetadata.aiUsed` solo vale verdadero cuando `strategy = "llm"`.
- [ ] Toda respuesta con `strategy = "llm"` tiene su registro en `aiUsage`.
- [ ] Las respuestas con `intent = "unsupported"` no generan registro en `aiUsage`.
- [ ] `citedNewsIds` apunta únicamente a noticias con `status = "published"`.
- [ ] La suma de `aiUsage.estimatedCostUsd` es calculable y se contrasta contra el presupuesto.

## 7. Parámetros

- [ ] Los parámetros abiertos del diseño tienen valor en la tabla de [parámetros](database/README.md#parámetros-del-diseño).
- [ ] Un cambio en la velocidad de lectura de referencia implica recalcular `estimatedReadingMinutes` en toda la colección.

## 8. Cierre

- [ ] Los huecos encontrados se corrigieron en el documento correspondiente, no solo en esta lista.

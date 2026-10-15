# Generador de noticias demo

Parte de la [documentación de base de datos](README.md).

Dataset reproducible de 32 noticias sintéticas para desarrollo. La fuente
ejecutable está en `backend/news/demo_news.py` (generación pura),
`backend/news/seed_news.py` (persistencia idempotente) y
`backend/news/news_check.py` (inspección no destructiva).

## Carácter sintético

DEMO / SYNTHETIC DATA: ninguna noticia describe acontecimientos reales. No se
atribuyen hechos a organizaciones, gobiernos, medios ni personas reales. Los
actores son colectivos y vecinos ficticios en localidades demo; las fuentes
son ficticias (`Demo News Source N`) con URLs reservadas
(`https://example.com/demo/...`); cada `verification.notes` lo declara
explícitamente. No intervienen IA, red ni APIs externas.

## Las 32 noticias

Exactamente 2 noticias por cada uno de los 16 países del catálogo
([catálogos y seeders](09-catalogos-y-seeders.md)):

| País | Noticias |
| --- | --- |
| CA, MX, GT, CR, AR, BR, CU, JM, ES, FR, JP, CN, EG, ZA, AU, NZ | 2 cada uno |

Todas usan `geographicScope.level = country` con el `locationIds`
determinista del país. No se agregan locations ni se supera el total de 32.

## Determinismo

La misma configuración produce siempre los mismos slugs, títulos, topics,
locations, estados, contenidos, timestamps de fixture e `_id`. No hay azar
sin semilla, ni fecha actual, ni identificadores aleatorios: los `_id` son
fijos por posición (`6720...0001`–`6720...0020` en hexadecimal) y las fechas
derivan de bases fijas de septiembre de 2026.

## Topics

Solo valores de `backend/news/topics.py`, de 1 a 3 por noticia, sin
duplicados internos. Los 14 topics aparecen al menos una vez. El topic
`internacional` se usa en noticias de contenido transfronterizo ficticio
(clubes de cocina, postales entre escuelas, foro de plazas) sin cambiar el
nivel geográfico `country`.

## Estados y verificación

- `status`: 28 `published` y 4 `draft` (MX, ES, JP, ZA, un país distinto cada
  uno). Los drafts tienen `publishedAt = null` y no aparecen en el feed ni
  pueden citarse en el chat.
- `verification.status`: mayoría `confirmed` (20) más `developing` (5),
  `insufficient_sources` (3) y `conflicting_sources` (4) para probar la UI y
  el chat. Sin confidence numérico.

## Fuentes

Cada noticia lleva fuentes demo. Las `confirmed` llevan 2–3; las
`developing`, 2; las `insufficient_sources`, 1 a propósito; las
`conflicting_sources`, 2 con `supports` opuestos dentro de la ficción. No hay
fact checking: la contradicción es deliberada para probar incertidumbre.

## Imágenes

Sin imágenes reales: fixtures `photograph`, `illustration`, `ai_generated`,
`ai_modified` y `none` (todas presentes). Las `ai_*` llevan `aiDisclosure`;
las `none` tienen `url` y `alt` nulos; las URLs son placeholders
`https://example.com/demo/img/...`. `aiAssistance.imageGenerated` coincide
con `image.type == ai_generated`. No se registra `aiUsage` porque no hubo
llamadas IA.

## Tiempo de lectura

Calculado con `count_words`, `estimate_reading_minutes` y
`compute_reading_time` (200 palabras por minuto, mínimo 1). Cada `published`
guarda `wordCount` y `estimatedReadingMinutes` coherentes con `content`. El
dataset mezcla lecturas cortas (~1 minuto), medias (~2 minutos) y largas
(>=3 minutos).

## Autor

`news.authorId` exige referencia a `users`, pero MongoDB no impone foreign
keys: tanto el modelo como el validator solo exigen tipo ObjectId. Por eso la
persistencia no requiere insertar ningún user y el Loop 05 no crea ninguno.
El generador usa un identificador sintético determinista documentado en el
código; la correspondencia con un usuario real (autoría de redacción) queda
pendiente de decisión humana en un loop futuro. `verification.reviewedBy`
queda en `null` en todas las fixtures.

## Idempotencia

`make db-seed-news` asegura el esquema, valida cada noticia con `News` antes
de escribir (un documento inválido aborta sin persistir nada) e inserta solo
las faltantes por `slug`. Primera ejecución: `inserted: 32`. Segunda:
`inserted: 0, unchanged: 32`. Nunca modifica ni elimina; nunca escribe en
otras colecciones (en particular, nunca en `users`).

`make db-news-check` solo lee y reporta cantidad, slugs únicos, cobertura de
16 países con 2 noticias cada uno, topics válidos y su cobertura, estados,
verificación, coherencia de imágenes y tiempos de lectura, además de
documentos ajenos (se reportan, nunca se borran).

## Comandos

```bash
make db-test            # suite offline, sin Atlas
make db-init            # asegura colecciones, validators e índices
make db-seed-catalogs   # prerrequisito: catálogo locations
make db-seed-news       # inserta solo noticias demo faltantes (idempotente)
make db-seed-news       # segunda ejecución: inserted 0, unchanged 32
make db-news-check      # inspección no destructiva del dataset
make db-schema-check    # verifica que el esquema físico no derivó
```

## Seed vs reseed controlado

Seed inserta únicamente lo faltante y preserva todo lo existente, incluidos
documentos ajenos. La reconstrucción controlada del dataset existe como
`make db-reseed` con confirmación exacta y está documentada en
[automatización y reseed](11-automatizacion-y-reseed.md); requiere autorización
humana explícita.

## Limitaciones conocidas

- `authorId` es un placeholder sintético sin documento `users`: la autoría
  real está pendiente de decisión humana.
- El dataset cubre el nivel `country`; probar el nivel `international` como
  `geographicScope` requeriría una decisión de diseño futura (no se amplió a
  más de 32 noticias en este loop).

# Loop 08 — Imágenes reales para noticias demo

## 1. Resultado

**COMPLETADO.** Fecha: 2026-10-19. Modelo: `openai/gpt-6-astra`.

Las 23 noticias demo con imagen visible ya no usan placeholders
`https://example.com/demo/img/...`. Usan 19 URLs HTTPS únicas de Wikimedia
Commons, verificadas individualmente en su página `File:` y comprobadas por
HTTP. Las 9 noticias `none` siguen sin URL.

## 2. Skills

- `test-driven-development` (principal): tests offline red antes de
  `demo_images.py`, `news_images_check.py` y la detección de drift; green y
  refactor posteriores. Cada test nuevo falló primero por ausencia de la
  funcionalidad.
- `code-reviewer`: aplicado al diff completo antes del commit. Sin BLOCKER ni
  MAJOR; un MINOR corregido durante la revisión (ver §17).
- `security-compliance`: activada por incorporar recursos externos y requests
  HTTP. Escaneo acotado y threat model en §18.
- `systematic-debugging`: usada de forma acotada para el `429` intermitente de
  Wikimedia (ver §11); no hubo bug de producción.

## 3. Problema corregido

`demo_news.py` construía todas las imágenes visibles con
`https://example.com/demo/img/{slug}.jpg`, host reservado con rutas
inexistentes. El frontend mostraba "Imagen no disponible" aunque el documento
declarara `photograph`, `illustration` o `ai_generated`, y el tipo no tenía
relación verificable con ningún recurso. La documentación
`10-generador-noticias-demo.md` afirmaba "sin imágenes reales".

## 4. Estrategia de imágenes

- Catálogo versionado en `backend/news/demo_images.py`; sin descubrimiento en
  runtime ni servicios aleatorios.
- Una URL fija por asset, reutilizada por slug cuando el tema coincide.
- Cada asset revisado en Commons para autoría, licencia y, si aplica,
  declaración de generación con IA.
- Sin binarios en el repositorio: solo URL, crédito y derechos.
- `image_alt` por fixture se eliminó; el `alt` ahora deriva del asset y declara
  el uso ilustrativo.

## 5. Fuentes

Wikimedia Commons (`upload.wikimedia.org`), 7 fotografías, 8 iconos Twemoji y
4 imágenes generadas con IA. Detalle y tabla completa en
`docs/design/database/13-imagenes-demo.md`.

## 6. Licencias y créditos

- Fotografías: CC BY-SA 2.5, CC BY-SA 3.0, CC BY-SA 4.0 y PD-self.
- Twemoji: CC BY 4.0 ("Copyright 2019 Twitter, Inc and other contributors").
- IA: 2 CC0 1.0 y 2 CC BY 4.0.
- `credit` incluye autor, título y página `File:`; `rights` incluye licencia,
  URL y nota de miniatura sin cambios editoriales.

## 7. Distribución de tipos

| Tipo | Noticias |
| --- | --- |
| `photograph` | 9 |
| `illustration` | 10 |
| `ai_generated` | 4 |
| `none` | 9 |

23 visibles, 19 URLs únicas. `ai_modified` ya no aparece: no había evidencia de
modificación con IA. Las tres fixtures afectadas
(`demo-cr-01-monitoreo-quebradas`, `demo-eg-01-postales-escuelas`,
`demo-nz-02-foro-plazas`) se reclasificaron a `illustration`, se les quitó
`aiDisclosure` y se ajustaron los párrafos que mencionaban la imagen alterada.
El enum conserva `ai_modified` para uso futuro.

## 8. IA y disclosures

Las 4 `ai_generated` conservan `aiDisclosure` con software declarado en Commons
y la frase de que no son evidencia fotográfica. `aiAssistance.imageGenerated`
es `true` solo en ellas. Fotografías e ilustraciones tienen
`aiDisclosure = null` e `imageGenerated = false`. No se registra `aiUsage`.

## 9. Determinismo

Mismas fixtures producen siempre las mismas URLs, créditos y tipos. No hay
fecha actual, azar ni APIs de descubrimiento. `_image()` falla cerrado si el
tipo de la fixture no coincide con el asset revisado, y `get_demo_image()` falla
con `KeyError` para un slug visible no catalogado.

## 10. Tests

- Nuevo `backend/news/tests/test_news_images_check.py` (34 tests): rechazo de
  URLs no aprobadas sin red, HEAD sin descarga, fallback 405/416/501, MIME,
  404/429/500, reintento acotado de 429, redirects validados, dedupe, CLI y
  espaciado del lote.
- `test_demo_news.py`: distribución exacta, HTTPS/host, sin query/fragmento ni
  credenciales, crédito con página Commons, derechos con URL, `alt` honesto y
  disclosure solo en IA.
- `test_news_check.py`: drift de `image` completo parametrizado por campo.
- `make db-test`: **249 passed**, sin red ni Atlas.

## 11. HTTP image check

`make db-news-images-check` (nuevo target, online, `--no-deps`): 19/19 OK con
`Content-Type: image/*`. Durante la ejecución se observó que Wikimedia responde
`429` intermitente con `Retry-After: 1` cuando las peticiones se espacian 1 s.
Se añadió un reintento único acotado (1–10 s) y un espaciado de lote de 2 s;
con eso el check pasa de forma estable. También se acepta `416` en HEAD como
señal de fallback a `GET` parcial, sin relajar el éxito: solo cuenta un 2xx con
MIME de imagen. El check nunca lee el cuerpo ni declara éxito falso.

## 12. Resultado local

```text
make db-reseed-dry-run  -> 16 locations, 32 news controladas; 0 externos
make db-reseed CONFIRM="RESEED ai_assisted_news"
                        -> deleted 32/16, inserted 16/32, verification OK
make db-news-check      -> OK, 32/32, 16/16, 4 drafts / 28 published
make db-news-images-check -> OK, 19 URLs
make db-verify          -> schema OK, catalogs OK, demo news OK
```

## 13. Atlas dry-run

Ejecutado sin escribir:

```text
make db-reseed-dry-run NEWS_DB_MODE=atlas COMPOSE_PROFILES= NEWS_MONGODB_DATABASE=ai_assisted_news
```

Resultado: 16 locations y 32 news controladas, 0 externos, sin cambios. No se
leyó el contenido de `keys/`; solo se comprobó que `keys/mongodb_uri` existe.

## 14. Comando manual Atlas

Solo tras decisión humana:

```bash
make db-reseed-dry-run NEWS_DB_MODE=atlas COMPOSE_PROFILES= NEWS_MONGODB_DATABASE=ai_assisted_news
make db-reseed NEWS_DB_MODE=atlas COMPOSE_PROFILES= NEWS_MONGODB_DATABASE=ai_assisted_news CONFIRM="RESEED ATLAS ai_assisted_news"
```

El agente **no** ejecutó el segundo comando.

## 15. Documentación

- Nuevo `docs/design/database/13-imagenes-demo.md` (problema, estrategia,
  procedencia, licencias, IA, validación offline/HTTP, reseed, limitaciones).
- Actualizados `10-generador-noticias-demo.md`, `02-criterios-de-contenido.md`,
  `11-automatizacion-y-reseed.md` (conteo de tests), `12-verificacion-final.md`,
  `docs/design/database/README.md`, `backend/news/README.md` y
  `docs/image-credits.md` (que seguía afirmando placeholders locales).

## 16. Makefile

Nuevo target `db-news-images-check`: explícitamente online, no destructivo,
independiente de `db-test`, sin DB ni secretos. No se modificó ningún comando
existente.

## 17. Code review

Revisión con `code-reviewer` (correctness → safety → maintainability →
performance → tests):

- MINOR corregido: el espaciado del lote estaba fijado a 1 s, insuficiente
  frente al limitador de Wikimedia; ahora `BATCH_PAUSE_SECONDS = 2` y el test
  offline lo verifica.
- MINOR corregido: `HEAD 416` no hacía fallback y podía reportar un fallo falso;
  ahora 405/416/501 hacen fallback a `GET` parcial.
- Sin BLOCKER ni MAJOR. `probe_image` no lee el cuerpo, valida redirects y
  acota reintentos; `check_images` deduplica y conserva la entrada.

## 18. Seguridad

```text
secret values exposed: NO
keys read directly: NO
external API credentials used: NO
external documents modified: NO
Atlas destructive reseed executed by agent: NO
assistant modified: NO
```

Escaneo acotado (`backend/news`, `docs/design/database`, `Makefile`): 10
hallazgos `mongodb-uri` preexistentes del baseline (URIs internas y fixtures de
test sin credenciales reales); 0 nuevos. `keys/` nunca escaneado.

Threat model del cambio: URL manipulada → allowlist de host/esquema, sin query
ni credenciales; redirect a host no aprobado → validación de cada `Location`;
respuesta enorme → nunca se lee el cuerpo; rate limit → un reintento acotado y
fallo honesto; asset con licencia dudosa → revisión individual y tipos
honestos; imagen presentada como evidencia → `alt` y disclosure explícitos.

## 19. Archivos modificados

Nuevos:

```text
backend/news/demo_images.py
backend/news/news_images_check.py
backend/news/tests/test_news_images_check.py
docs/design/database/13-imagenes-demo.md
```

Modificados:

```text
Makefile
backend/news/demo_news.py
backend/news/news_check.py
backend/news/tests/test_demo_news.py
backend/news/tests/test_news_check.py
backend/news/README.md
docs/design/database/02-criterios-de-contenido.md
docs/design/database/10-generador-noticias-demo.md
docs/design/database/11-automatizacion-y-reseed.md
docs/design/database/12-verificacion-final.md
docs/design/database/README.md
docs/image-credits.md
```

## 20. Decisiones

- Reclasificar `ai_modified` a `illustration` en lugar de inventar modificación
  IA: no había evidencia verificable. Aprobado por la instrucción humana de
  mantener tipos honestos.
- Compartir assets entre noticias del mismo tema (3 parks, 2 books, 2 water) en
  lugar de forzar 23 archivos distintos.
- Mantener `none` sin URL; no rellenar con una imagen genérica.
- Aceptar 416 como señal de fallback, no como éxito.
- No modificar el seeder para que actualice: el reseed controlado es la vía.

## 21. Blockers

Ninguno. Pendiente humano no bloqueante: decidir y ejecutar el reseed Atlas con
el comando de §14. El limitador de Wikimedia puede devolver 429; el check lo
maneja con un reintento y espaciado de 2 s, pero una caída prolongada se
reportará como fallo.

## 22. Git

Commit (sin push):

```text
fix: use real images for demo news
```

Verificado pre-commit: `make db-test` (249 passed),
`make db-news-images-check` (19/19), reseed local + `db-news-check` +
`db-verify` OK, `git diff --check` limpio y sin secretos en staging. No se
modificaron `backend/assistant/` ni los archivos untracked del usuario
`backend/loops/08-real-news-images.md` y
`backend/prompts/08-real-news-images.md`.

## Trazabilidad

```text
[x] modelos sincronizados (sin cambios; enum ai_modified se conserva)
[x] documentación sincronizada
[x] diagrama sincronizado (sin cambio estructural)
[x] tests sincronizados
[x] Makefile sincronizado
[x] secrets/bootstrap sincronizados (sin secreto nuevo)
```

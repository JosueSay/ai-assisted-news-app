# Imágenes del dataset demo

Parte de la [documentación de base de datos](README.md).

Este documento fija la procedencia, licencias y criterios de las imágenes de
las 32 noticias sintéticas descritas en
[10 Generador de noticias demo](10-generador-noticias-demo.md). El catálogo
ejecutable vive en `backend/news/demo_images.py`; el check HTTP, en
`backend/news/news_images_check.py`.

## Problema corregido

Hasta el Loop 07 todas las imágenes visibles apuntaban a
`https://example.com/demo/img/{slug}.jpg`. Ese host es reservado y las rutas no
existen: el frontend mostraba el fallback "Imagen no disponible" aunque el
documento declarara `photograph`, `illustration` o `ai_generated`. Además, el
tipo declarado no tenía relación verificable con ningún recurso real.

El dataset sigue siendo DEMO / SYNTHETIC DATA. Las imágenes nuevas son
representaciones ilustrativas: ninguna documenta los acontecimientos ficticios
ni se presenta como evidencia.

## Estrategia elegida

- Fuente única: **Wikimedia Commons**, servida desde `upload.wikimedia.org`.
- URLs versionadas en el repositorio, deterministas y sin descubrimiento en
  tiempo de ejecución.
- Cada asset fue revisado individualmente en su página `File:` de Commons para
  confirmar autoría, licencia y, cuando aplica, la declaración de generación con
  IA.
- No se usan servicios aleatorios (`source.unsplash.com/random`), hotlinks de
  medios, URLs temporales ni recursos con autenticación.
- No se almacenan binarios en el repositorio: solo la URL HTTPS, el crédito y
  los derechos.

## Distribución

23 noticias tienen imagen visible y 19 URLs son únicas (tres assets temáticos se
comparten entre noticias del mismo tema):

| `image.type` | Noticias |
| --- | --- |
| `photograph` | 9 |
| `illustration` | 10 |
| `ai_generated` | 4 |
| `none` | 9 |

`ai_modified` no aparece en el dataset. No había evidencia de modificación con
IA en los recursos verificables y no se etiqueta una imagen como alterada sin
prueba. Las tres fixtures que antes usaban ese tipo
(`demo-cr-01-monitoreo-quebradas`, `demo-eg-01-postales-escuelas`,
`demo-nz-02-foro-plazas`) se reclasificaron como `illustration`, se eliminó su
`aiDisclosure` y se ajustaron los párrafos que mencionaban la imagen alterada.
El modelo conserva el valor `ai_modified` en el enum para uso futuro.

## Procedencia y licencias

Fotografías (representación ilustrativa del tema, nunca del evento ficticio).
`demo-br-01`, `demo-cn-02` y `demo-za-01` comparten el mismo archivo:

| Noticias | Archivo de Commons | Autor | Licencia |
| --- | --- | --- | --- |
| `demo-ca-01-sensores-jardin` | `Garden.jpg` | Shengzhi Li | CC BY-SA 2.5 |
| `demo-gt-02-liga-fin-semana` | `Football_pitch.jpg` | LensEye Media | CC BY-SA 4.0 |
| `demo-ar-01-asamblea-salon` | `Meeting_room.jpg` | Rashtriya Paryavaran | CC BY-SA 4.0 |
| `demo-br-01-caminatas-matutinas`, `demo-cn-02-estiramiento-parques`, `demo-za-01-limpieza-parques` | `Heerde_-_Vosbergerweg_-_Park.jpg` | Koosg | CC BY-SA 3.0 |
| `demo-jm-01-noche-acustica` | `Acoustic_guitar.jpg` | Massimo Giuliani | PD-self |
| `demo-fr-01-ruta-lectura` | `Two_bookshelves_full_of_books_belonging_to_Unitedmissionary_(2010).jpg` | Unitedmissionary | CC BY-SA 3.0 |
| `demo-au-01-ciclismo-recreativo` | `Three_rusty_bicycles.jpg` | Pratap555 | CC BY-SA 4.0 |

Las ilustraciones son ocho Twemoji distintos (CC BY 4.0, "Copyright 2019
Twitter, Inc and other contributors") servidos como PNG de 960 px. `books` y
`water` se comparten entre dos noticias cada uno. Las tres fixtures
reclasificadas desde `ai_modified` reutilizan iconos temáticos ya presentes
(`water`, `mail`, `tree`), por eso no añaden archivos nuevos.

Imágenes generadas con IA (todas con `aiDisclosure`):

| Slug | Archivo de Commons | Autor declarado | Licencia | Software |
| --- | --- | --- | --- | --- |
| `demo-mx-01-teatro-barrial` | `Collage_con_materiales_reciclados_generado_por_Gemini.png` | Gemini | CC0 1.0 | Gemini |
| `demo-br-02-taller-reparacion` | `DALL·E 2025-02-21 ... RGB light stick ...webp` | ChatGPT DALLE | CC BY 4.0 | ChatGPT DALLE |
| `demo-cn-01-clubes-cocina` | `Generative_AI_can_be_used_to_create_realistic_images_of_food_dishes.jpg` | Dennis Sylvester Hurd | CC0 1.0 | Midjourney |
| `demo-nz-01-simulacro-evacuacion` | `Safety_Management_Cycle_diagram.png` | OpenAI ChatGPT (GPT-5.6 Sol) | CC BY 4.0 | OpenAI ChatGPT |

El campo `image.credit` incluye autor, título y la página `File:` de Commons. El
campo `image.rights` registra la licencia con su URL y la nota de que se usa la
miniatura de Commons cuando corresponde, sin cambios editoriales.

## Ilustración frente a evidencia

Todas las imágenes visibles usan un `alt` con la forma:

```text
<descripción>. Representación ilustrativa; no documenta el acontecimiento demo.
```

Ninguna fotografía se presenta como prueba del acontecimiento ficticio: la
noticia, sus fuentes y sus notas siguen declarando el carácter sintético. Las
imágenes `ai_generated` añaden un `aiDisclosure` que indica el software
declarado en Commons y que no son evidencia fotográfica.

`image.type = none` mantiene `url` y `alt` en `null`; no se rellena con una
imagen genérica.

## Uso declarado de IA

`aiAssistance.imageGenerated` vale `true` únicamente para las cuatro fixtures
`ai_generated`, coherente con `image.type`. Las ilustraciones y fotografías
tienen `aiDisclosure = null` y `imageGenerated = false`. No se registra
`aiUsage`: el dataset no ejecuta llamadas a modelos.

## Validación offline

`make db-test` no usa red ni credenciales. Los tests comprueban:

- distribución exacta de tipos (9/10/4/9);
- esquema `https`, host `upload.wikimedia.org`, sin query, fragmento ni
  credenciales en la URL;
- crédito con página `File:` de Commons y derechos con URL de licencia;
- `alt` con "ilustrativa" y "no documenta";
- disclosure presente solo en `ai_generated`;
- `none` con URL nula;
- detección de drift: `news_check.py` compara el documento `image` completo
  contra la fixture esperada, de modo que una base con placeholders antiguos
  falla aunque el resto del documento coincida.

## Validación HTTP

`make db-news-images-check` es explícitamente online, no depende de MongoDB ni
carga secretos:

- solo acepta hosts `upload.wikimedia.org` y `thumb.wikimedia.org`, HTTPS, sin
  credenciales, query ni fragmento;
- usa `HEAD` y solo cae a un `GET` parcial (`Range: bytes=0-0`) si el servidor
  responde `405`, `416` o `501`; nunca descarga el cuerpo;
- valida cada `Location` de redirección (máximo 3);
- exige `Content-Type: image/*`;
- ante `429` hace como máximo un reintento, solo si `Retry-After` es numérico
  entre 1 y 10 segundos;
- espacia las peticiones del lote 2 segundos para no activar el limitador de
  Wikimedia;
- deduplica URLs y reporta todos los slugs afectados;
- termina con código distinto de cero si alguna URL falla.

Un `200` no prueba licencia ni veracidad: la licencia se verificó en la página
del archivo.

## Actualización mediante reseed

`make db-seed-news` solo inserta noticias faltantes por `slug`; no actualiza
documentos existentes. Por eso una base ya sembrada conserva los placeholders
antiguos. La reconstrucción correcta es el reseed controlado documentado en
[11 Automatización y reseed](11-automatizacion-y-reseed.md):

```bash
make db-reseed-dry-run
make db-reseed CONFIRM="RESEED ai_assisted_news"
make db-news-check
make db-verify
```

En Atlas el agente solo ejecuta el dry-run; el reseed destructivo requiere
decisión humana y la frase `RESEED ATLAS ai_assisted_news`.

## Limitaciones

- Las imágenes son ilustrativas y temáticas: no corresponden al lugar ni al
  acontecimiento ficticio.
- Tres assets se comparten entre noticias del mismo tema; no hay una imagen
  distinta por noticia.
- Las licencias y la autoría se verificaron en la fecha del loop; un cambio en
  la página de Commons requeriría revisar el catálogo.
- El check HTTP depende de la disponibilidad y del limitador de Wikimedia; un
  `429` persistente se reporta como fallo, no como éxito.

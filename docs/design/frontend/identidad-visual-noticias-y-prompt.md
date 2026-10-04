# Identidad visual y prompt de implementación — Frontend de noticias

Versión 1.0 · 4 de octubre de 2026 · Idioma de interfaz: español

## 1. Propósito y alcance

Este archivo es la especificación visual y funcional para que un agente transforme el frontend existente en una experiencia editorial responsive, de una sola página con navegación. Debe permitir reproducir el diseño sin depender de esta conversación.

**Entregable de esta etapa:** documentación y prompt. El repositorio del frontend, su marca y su stack no están identificados en este documento. No se afirma haber modificado la aplicación ni descargado sus imágenes. El agente implementador deberá inspeccionar el proyecto real y ejecutar el prompt del apartado 12.

**Interpretación de “móvil y app”:** una web con experiencia de aplicación en teléfonos y tabletas. Si ya existe una app o contenedor nativo, adaptar los mismos tokens a ese entorno. Esta especificación no exige crear una app nativa nueva, autenticación, backend ni instalación PWA.

Conservar el nombre y logotipo existentes. Si el proyecto carece de marca, usar provisionalmente **El Foco**, escrito en Newsreader 700 con una pequeña línea roja inferior. No sustituir una marca real por este nombre de ejemplo.

## 2. Base de UI UX Pro Max y decisiones de diseño

Habilidad: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill). Ya estaba instalada en el entorno de elaboración y su buscador se ejecutó correctamente; no fue necesario reinstalarla.

Consultas utilizadas:

```bash
python3 <UI_UX_PRO_MAX_DIR>/scripts/search.py \
  'news editorial magazine trustworthy' --design-system \
  -p 'Editorial Noticias' -f markdown

python3 <UI_UX_PRO_MAX_DIR>/scripts/search.py \
  'news magazine' --domain product -n 2
```

Resultados pertinentes: Minimalism & Swiss Style + Flat Design para News/Media Platform; Newsreader + Roboto para periodismo; énfasis en contraste, jerarquía, cuadrícula y rendimiento. Se revisaron también las reglas de interacción móvil y safe areas de la habilidad.

**Síntesis editorial propia:** se conserva esa base, pero se sustituye el fondo rosado sugerido por marfil y el texto rojizo por tinta oscura. El patrón genérico de conversión con hero/CTA se adapta a una portada periodística: noticia principal, secundarios, actualidad y secciones. No usar una landing comercial con beneficios, testimonios y botón gigante.

### Concepto: “Editorial clara”

Una publicación contemporánea, sobria y reconocible: fondo de papel cálido, titulares serif, interfaz sans serif, fotografía protagonista y líneas finas. El carácter procede de la composición y la tipografía, sin efectos decorativos excesivos.

- Prioridad perceptiva: titular → fotografía → resumen → categoría y metadatos.
- Sensación: credibilidad, actualidad y calma al leer.
- Densidad media: suficiente contenido visible sin convertir la portada en una pared de tarjetas.
- Rojo reservado para identidad y noticias destacadas; azul para acciones y selección.
- Estilo claro obligatorio en esta entrega. No añadir un selector oscuro sin diseñar y comprobar todos sus estados.

## 3. Colores y tokens semánticos

| Token | Valor | Uso obligatorio |
|---|---|---|
| `--bg` | `#F7F5F0` | Fondo general marfil |
| `--surface` | `#FFFFFF` | Lectura, paneles, búsqueda y controles |
| `--surface-muted` | `#EEEAE2` | Fondos secundarios y placeholder |
| `--ink` | `#18212B` | Titulares y texto principal |
| `--text-secondary` | `#52606D` | Resúmenes, fecha y autor |
| `--brand` | `#B42318` | Línea de marca y etiqueta editorial |
| `--brand-hover` | `#912018` | Hover de acción roja si existe |
| `--action` | `#1D4ED8` | Enlaces, botones primarios y selección |
| `--action-hover` | `#1E40AF` | Hover de acciones |
| `--action-soft` | `#EAF0FF` | Fondo de selección con texto azul |
| `--border` | `#D8D3C9` | Separadores decorativos |
| `--control-border` | `#737B84` | Contorno perceptible de campos |
| `--success` | `#17643B` | Confirmaciones con texto e icono |
| `--danger` | `#B42318` | Errores acompañados de mensaje |
| `--on-solid` | `#FFFFFF` | Texto sobre rojo o azul sólidos |

Usar aproximadamente 80% de superficies neutras, 15% de texto/estructura y 5% de acentos; es una guía visual, no un cálculo por píxel. Las fotografías quedan fuera de esta proporción.

No asignar un color saturado distinto a cada sección. Usar nombre de categoría + posición; el color nunca será el único indicador. Los separadores suaves no sustituyen el borde de un control interactivo.

Texto normal: contraste mínimo 4.5:1. Texto grande y elementos gráficos informativos: 3:1. Verificar también hover, selección y foco. No poner texto secundario con opacidad reducida sobre fotografías.

## 4. Tipografía y jerarquía

**Titulares:** Newsreader, pesos 600 y 700; fallback Georgia, serif. **Interfaz, resumen y lectura:** Roboto, pesos 400, 500 y 700; fallback Arial, sans-serif. Máximo dos familias. Cargar WOFF2 con licencia conservada, `font-display: swap` y subconjunto que incluya español.

| Elemento | Móvil <768 px | Tablet 768–1023 px | Escritorio ≥1024 px | Peso / interlineado |
|---|---:|---:|---:|---|
| Marca | 28 px | 32 px | 36 px | Newsreader 700 / 1.05 |
| Titular principal de portada | 36 px | 44 px | 56 px | Newsreader 600 / 1.08 |
| Título de artículo abierto | 36 px | 44 px | 56 px | Newsreader 600 / 1.08 |
| Encabezado de sección | 28 px | 30 px | 32 px | Newsreader 600 / 1.15 |
| Titular de tarjeta | 24 px | 26 px | 28 px | Newsreader 600 / 1.2 |
| Titular compacto | 20 px | 20 px | 22 px | Newsreader 600 / 1.25 |
| Resumen | 16 px | 17 px | 18 px | Roboto 400 / 1.55 |
| Cuerpo del artículo | 18 px | 19 px | 20 px | Roboto 400 / 1.7 |
| Navegación y botones | 14 px | 14 px | 15 px | Roboto 500 / 1.4 |
| Autor y fecha | 13 px | 13 px | 14 px | Roboto 400 / 1.5 |
| Categoría | 12 px | 12 px | 12 px | Roboto 700 / 1.4 |
| Etiqueta de barra inferior | 12 px | — | — | Roboto 500 / 1.3 |

Convertir px a rem con raíz de 16 px; no fijar el tamaño raíz para impedir las preferencias del usuario. Títulos con `letter-spacing: -0.02em`; categorías en mayúsculas con `0.06em`. No aplicar mayúsculas a párrafos o titulares.

Usar `text-wrap: balance` en títulos cuando esté disponible. El titular principal y el del artículo se muestran completos. Solo los resúmenes de tarjetas pueden truncarse a tres líneas. No truncar noticias para compensar una mala cuadrícula. Texto de lectura limitado a 68ch y centrado.

## 5. Espaciado, superficies e iconos

- Escala única: 4, 8, 12, 16, 24, 32, 48, 64 y 96 px.
- Distancia categoría/titular: 8 px; titular/resumen: 12 px; resumen/metadatos: 16 px.
- Separación entre secciones: 40 px móvil, 56 px tablet, 64 px escritorio.
- Radios: imágenes 8 px; botones y campos 8 px; paneles 12 px; chips 999 px.
- Tarjetas editoriales: fondo integrado con la página, sin sombra, borde inferior de 1 px cuando sea necesario.
- Paneles flotantes: blanco y sombra `0 12px 36px rgb(24 33 43 / 0.14)`.
- Iconos: una sola familia SVG, preferentemente Lucide si el proyecto no tiene una; trazo 1.75–2 y tamaños de 20/24 px. No emojis estructurales.
- Botones: mínimo 44 px de alto, padding horizontal 16 px y separación de 8 px. Objetivo táctil preferido 48×48 px.
- Botón primario azul con texto blanco; secundario blanco con borde de control; acción editorial discreta como enlace subrayado.
- Foco: anillo azul de 3 px con offset blanco de 2 px, sin recortes por overflow.

## 6. Composición y adaptación responsive

Contenedor: `width: min(100% - 2 * var(--gutter), 1248px)`, centrado. Nunca fijar un ancho que exceda el viewport.

| Rango | Margen lateral | Columnas base | Gap | Navegación |
|---|---:|---:|---:|---|
| 320–767 px | 16 px | 1 | 24 px | Header compacto + barra inferior |
| 768–1023 px | 24 px | 2 | 24 px | Header con menú de secciones |
| ≥1024 px | 32 px | 12 | 32 px | Header + navegación horizontal |

### Orden de la portada

1. Aviso discreto: **“Edición de demostración · Noticias ficticias”**. Forma parte del flujo; no ocupa una barra fija adicional.
2. Cabecera con marca, búsqueda y acceso a guardados. Header sticky de 64 px en móvil y 80 px en escritorio. Alturas mínimas que pueden crecer con texto ampliado.
3. Navegación de categorías en escritorio. En móvil, chips de filtro que envuelven en varias líneas; no producir scroll horizontal de la página.
4. Bloque principal: una noticia dominante y dos secundarias.
5. “Últimas noticias”: listado con hora, categoría y titular; 6 entradas visibles.
6. Bloques de categorías: Actualidad, Tecnología, Economía, Cultura y Deportes.
7. Footer con marca, enlaces internos y aclaración de demostración.

**Escritorio:** principal de 8 columnas con imagen 16:9 y texto debajo; columna lateral de 4 columnas con dos noticias secundarias, imagen 16:9 y titular de 24 px. Titular dominante alineado a la izquierda, sin un gran eslogan comercial. Secciones inferiores con tres noticias por fila.

**Tablet:** principal a ancho completo; debajo, dos secundarias lado a lado. Tarjetas inferiores en dos columnas. Evitar forzar tres columnas pequeñas.

**Móvil:** principal a ancho completo, imagen antes del titular; secundarias como filas con imagen de 104×80 px a la izquierda y texto a la derecha. A 320 px o con texto ampliado, esas filas pasan a una columna si no hay espacio suficiente. El resto del feed alterna tarjetas con fotografía y filas compactas mediante variantes explícitas, no tamaños aleatorios.

No establecer altura fija en bloques de texto. Mantener el mismo orden de lectura en DOM y visual. No usar un carrusel automático como noticia principal.

### Experiencia tipo app

Barra inferior solo debajo de 768 px: **Inicio, Secciones, Buscar, Guardados**, siempre con icono y texto. Altura base 64 px más `env(safe-area-inset-bottom)`. Fondo blanco, borde superior suave, selección azul con fondo azul tenue.

Reservar en el contenido un padding inferior igual a la altura real de la barra + 16 px. Respetar safe areas superiores/laterales en pantallas con recortes. Si se abre el teclado virtual, la búsqueda y sus resultados deben seguir siendo utilizables sin que la barra tape el campo.

En una app nativa existente, traducir medidas a unidades lógicas y mantener mínimos de 44 pt en iOS y 48 dp en Android; conservar controles y comportamiento Atrás propios de la plataforma.

## 7. Navegación single page e interacciones

Single page significa una sola aplicación y documento base, con vistas y estado navegables. No significa una portada inmóvil ni enlaces vacíos. Conservar el router existente; para un proyecto sin router puede usarse hash.

Contrato propuesto para hash, adaptable al router real sin perder comportamiento:

| Estado | URL equivalente | Resultado |
|---|---|---|
| Portada | `#/inicio` | Muestra portada y restaura su posición |
| Categoría | `#/seccion/tecnologia` | Filtra noticias y marca categoría activa |
| Directorio | `#/secciones` | Lista todas las categorías |
| Buscar | `#/buscar?q=energia` | Campo enfocado y resultados por texto |
| Guardados | `#/guardados` | Lista de artículos guardados |
| Artículo | `#/noticia/demo-001` | Vista de lectura con URL compartible |

- Todos los elementos visibles de navegación deben funcionar sin recargar el documento.
- Atrás/Adelante restaura vista, búsqueda, filtros y posición de scroll cuando corresponda.
- Una recarga en artículo o búsqueda restaura ese estado desde la URL.
- Una selección explícita agrega historial; escribir cada letra en búsqueda actualiza con replace y debounce de 200 ms, sin llenar el historial.
- Cambiar de vista mueve el foco al título principal y actualiza `document.title`. Regresar a una lista restaura foco al enlace de origen cuando exista.
- Artículos desconocidos: mensaje “No encontramos esta noticia” y botón “Volver al inicio”.
- Búsqueda local por título, resumen y categoría, sin distinguir mayúsculas ni tildes. Estado vacío con acción para limpiar la búsqueda.
- Guardar usa un botón separado del enlace del artículo, `aria-pressed` y persistencia local con manejo de errores. Nunca anidar un botón dentro de un enlace de tarjeta.
- No añadir login, suscripciones o un formulario de newsletter sin función real. Los enlaces legales no deben apuntar a `#`.

### Lectura de una noticia

Vista dentro de la SPA con Volver, categoría, título, resumen, autor ficticio, fecha, tiempo de lectura, imagen y crédito, cuerpo, guardar y noticias relacionadas. Ancho del cuerpo 68ch; imagen puede alcanzar 960 px. Etiqueta visible **“Noticia simulada”**. El artículo abre como vista completa, no como un modal que dificulte la lectura móvil.

### Estados y movimiento

Hover: subrayar titular y cambiar el color del enlace, sin desplazar el layout. Feedback de pulsación: 100 ms. Transiciones de color: 160 ms. Paneles: 220 ms con ease-out. Respetar `prefers-reduced-motion`; sin parallax, scroll secuestrado, pulso permanente ni animaciones de entrada en cada tarjeta.

Datos locales se muestran inmediatamente; no simular espera de red. Reservar dimensiones de imagen. Si una imagen falla, sustituirla por un bloque neutro con icono y texto “Imagen no disponible”. Menús y paneles deben cerrar con Escape y devolver foco; los modales, si existen, requieren gestión de foco e impedir interacción con el fondo.

## 8. Fotografías y contenido de demostración

### Dirección fotográfica

Fotografía documental contemporánea: espacios urbanos, tecnología en uso, comercio, actividades culturales y deporte. Luz natural, colores moderados y escenas plausibles. No aplicar filtros de marca ni overlays oscuros de forma sistemática. No poner titulares sobre fotos: la base editorial sitúa el texto fuera de la imagen.

Obtener imágenes reales de fuentes con permiso de uso o generar imágenes expresamente ilustrativas. El agente debe descargar y comprobar assets concretos; no inventar URLs ni usar endpoints de imágenes aleatorias. Fuentes candidatas: Unsplash, Pexels o Wikimedia Commons, comprobando las condiciones de cada recurso. Una foto ilustrativa no demuestra que el evento ficticio haya ocurrido.

Guardar assets en el directorio público equivalente del proyecto, con nombres estables; preferir AVIF/WebP y derivados de 480, 960 y 1440 px cuando proceda. Usar `srcset`/`sizes`, dimensiones explícitas y `object-fit: cover`. Cargar prioritariamente solo la imagen principal visible; lazy loading en las inferiores. No estirar ni repetir una misma foto como solución para toda la portada.

Documentar en `docs/image-credits.md`: archivo, artículo, URL de origen, autor, licencia/condiciones comprobadas, fecha y uso ilustrativo. Conservar licencias de fuentes tipográficas. No inventar créditos.

### Dataset mínimo

20 noticias ficticias: cuatro por categoría. Una destacada y dos secundarias seleccionadas mediante IDs estables. Textos originales en español, sin lorem ipsum, falsas declaraciones de personas reales ni atribuciones a medios reales. Deben parecer piezas completas de una demo, sin presentarse como hechos verificados.

Cada noticia: ID, slug, título de 45–90 caracteres como objetivo flexible, resumen de 110–190 caracteres, categoría, autor ficticio, fecha ISO con zona, cuerpo de 4–7 párrafos breves, tiempo de lectura calculado, imagen y descripción alternativa. Distribuir fechas en una ventana fija de demostración; no cambiar titulares o fechas de forma aleatoria en cada render.

Ejemplos creativos para desarrollar, todos ficticios:

| Categoría | Titular de ejemplo | Imagen sugerida |
|---|---|---|
| Actualidad | Un nuevo paseo peatonal reúne comercio y espacios de descanso | Calle peatonal arbolada |
| Tecnología | Jóvenes desarrollan sensores para cuidar los huertos urbanos | Electrónica y plantas |
| Economía | Pequeños comercios prueban un mercado digital comunitario | Puesto de mercado |
| Cultura | Bibliotecas de barrio abren una ruta de lectura al aire libre | Libros y espacio público |
| Deportes | Una liga comunitaria recupera las canchas del vecindario | Cancha sin marcas comerciales dominantes |

Modelo de datos orientativo; adaptar al lenguaje del proyecto:

```ts
type Category = 'actualidad' | 'tecnologia' | 'economia' | 'cultura' | 'deportes';
interface DemoArticle {
  id: string;
  slug: string;
  title: string;
  summary: string;
  category: Category;
  author: string;
  publishedAt: string;
  body: string[];
  readingMinutes: number;
  isDemo: true;
  image: {
    src: string;
    alt: string;
    width: number;
    height: number;
    credit: string;
    sourceUrl: string;
    license: string;
  };
}
```

Separar los datos de los componentes. Usar un pequeño adaptador de lectura para facilitar una API futura, sin construir ahora esa API. Las rutas de imágenes indicadas por el dataset deben existir. Si no hay red para obtenerlas, documentar el bloqueo y usar placeholders honestos, sin afirmar que la selección fotográfica está terminada.

## 9. Base CSS transferible

Los valores de este documento son la fuente de verdad. Mapearlos al sistema existente, sea CSS, Tailwind, theme de componentes o tokens nativos; evitar hex y espaciados arbitrarios dispersos.

```css
:root {
  --bg: #F7F5F0;
  --surface: #FFFFFF;
  --surface-muted: #EEEAE2;
  --ink: #18212B;
  --text-secondary: #52606D;
  --brand: #B42318;
  --brand-hover: #912018;
  --action: #1D4ED8;
  --action-hover: #1E40AF;
  --action-soft: #EAF0FF;
  --border: #D8D3C9;
  --control-border: #737B84;
  --success: #17643B;
  --danger: #B42318;
  --on-solid: #FFFFFF;
  --font-heading: 'Newsreader', Georgia, serif;
  --font-body: 'Roboto', Arial, sans-serif;
  --gutter: 1rem;
  --radius: .5rem;
  --bottom-nav: 4rem;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: var(--font-body); }
.container { width: min(calc(100% - 2 * var(--gutter)), 78rem); margin-inline: auto; }
img { display: block; max-width: 100%; height: auto; }
h1, h2, h3 { font-family: var(--font-heading); letter-spacing: -.02em; text-wrap: balance; }
p { overflow-wrap: break-word; }
.reader-body { max-width: 68ch; margin-inline: auto; font-size: 1.125rem; line-height: 1.7; }
:focus-visible { outline: 3px solid var(--action); outline-offset: 2px; }
@media (min-width: 48rem) { :root { --gutter: 1.5rem; } }
@media (min-width: 64rem) { :root { --gutter: 2rem; } }
@media (max-width: 47.999rem) {
  body { padding-bottom: calc(var(--bottom-nav) + env(safe-area-inset-bottom) + 1rem); }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
```

Este CSS es una base, no una implementación completa. Medir la altura real de barras si crecen con accesibilidad y actualizar los offsets; no confiar exclusivamente en la constante de 4rem.

## 10. Plan de ejecución en el repositorio

1. **Inspeccionar:** leer `AGENTS.md`, estructura, manifest de dependencias, rutas, componentes, estilos, assets y comandos disponibles. Identificar la marca y stack reales. No asumir React/Next ni migrar el proyecto.
2. **Planificar y documentar antes de editar UI:** copiar este documento a `docs/identidad-visual.md`; registrar componentes reutilizables, correspondencia de tokens, rutas y orden de cambios en `docs/plan-frontend.md`.
3. **Fundación visual:** cargar fuentes, tokens, layout global, foco, botones y variantes de noticia.
4. **Contenido:** preparar 20 noticias e imágenes verificadas y sus créditos. Asegurar que todas las noticias abran una lectura completa.
5. **Portada responsive:** implementar primero móvil, después tablet y escritorio; refinar composición principal/secundarias y ritmo de secciones.
6. **Interacciones:** navegación, búsqueda, lectura, guardados, historial, estados vacíos y errores.
7. **Verificación visual y funcional:** revisar matriz del apartado 11, corregir y documentar evidencia. Ejecutar build/lint/pruebas existentes pertinentes sin inventar resultados.
8. **Entrega:** resumir cambios, archivos, comandos realmente ejecutados, capturas y limitaciones. Conservar las convenciones y funcionalidades del proyecto.

## 11. Criterios de aceptación

### Visuales y responsive

- [ ] Tokens y fuentes coinciden con esta especificación; no hay un rediseño improvisado adicional.
- [ ] Revisado en 320, 375, 390, 768, 1024 y 1440 px; móvil también en orientación horizontal.
- [ ] No hay scroll horizontal de página, titulares cortados, imágenes deformadas ni contenido tapado por barras.
- [ ] Verificado con zoom/texto ampliado al 200%, teclado virtual y safe areas.
- [ ] Capturas de portada móvil/escritorio, búsqueda móvil y artículo móvil/escritorio.
- [ ] Principal, secundarios y filas compactas se diferencian por jerarquía, no por ornamentación excesiva.

### Funcionales

- [ ] Inicio, cinco categorías, Secciones, Buscar y Guardados funcionan.
- [ ] Las 20 noticias se pueden abrir y todas sus imágenes tienen resolución de recurso o fallback.
- [ ] Búsqueda vacía/sin coincidencias y guardados vacíos tienen mensajes útiles.
- [ ] Guardar y quitar persiste tras recargar; el fallo de almacenamiento no rompe la UI.
- [ ] URLs de artículo y búsqueda funcionan al recargar; Atrás/Adelante restaura estado.
- [ ] No quedan botones sin acción, enlaces vacíos o funciones fingidas.

### Accesibilidad y rendimiento

- [ ] Landmarks, un H1 por vista, encabezados coherentes y enlace “Saltar al contenido”.
- [ ] Navegación completa por teclado, foco visible y orden correcto; selección comunicada semánticamente.
- [ ] Imágenes informativas con alt; decorativas con alt vacío; controles con nombre accesible.
- [ ] Contraste medido en pares reales y estados; texto normal ≥4.5:1.
- [ ] Objetivos táctiles al menos 44×44 px y espacios suficientes entre acciones.
- [ ] Reduced motion, sin reproducción automática ni contenido que aparezca solo al hacer hover.
- [ ] Dimensiones de imágenes reservadas y carga diferida bajo el primer viewport.
- [ ] Objetivos de rendimiento: LCP ≤2.5 s, CLS ≤0.1 e INP ≤200 ms cuando puedan medirse en condiciones representativas. Registrar método y entorno; no presentar una prueba local como garantía de campo.
- [ ] Build/lint disponibles ejecutados y revisión de consola sin errores causados por los cambios.

## 12. Prompt listo para entregar al agente implementador

Copiar el siguiente prompt y adjuntar **este archivo completo**. El prompt define el trabajo funcional; los apartados anteriores fijan el estilo visual.

```text
Actúa como diseñador UI/UX y desarrollador frontend del proyecto existente.

OBJETIVO
Transforma nuestro frontend en una página de noticias con identidad editorial consistente, excelente presentación en escritorio/tablet/móvil y experiencia móvil tipo app. Implementa una sola aplicación con navegación funcional, noticias simuladas e imágenes reales ilustrativas. Usa como fuente de verdad el Markdown adjunto “Identidad visual y prompt de implementación — Frontend de noticias”, versión 1.0.

ANTES DE PROGRAMAR
1. Lee AGENTS.md y revisa el repositorio. Identifica el stack, router, marca, estilos, componentes y scripts reales. Preserva el framework y las convenciones del proyecto.
2. Usa la habilidad UI UX Pro Max. Primero verifica si ya está instalada y lee su SKILL.md. Si no existe, consulta las instrucciones vigentes del repositorio https://github.com/nextlevelbuilder/ui-ux-pro-max-skill y realiza la instalación correspondiente al entorno antes de diseñar. No afirmes haberla instalado si no pudiste verificarla.
3. Guarda la identidad visual adjunta en docs/identidad-visual.md y escribe docs/plan-frontend.md con diagnóstico breve, tokens, componentes, rutas, datos y pasos de implementación. Planifica antes de editar la UI y continúa después con la implementación.
4. Conserva el nombre y logo existentes. Solo si no hay marca, usa provisionalmente El Foco. No inventes datos del proyecto ni lo confundas con el repositorio de la habilidad.

ESTILO OBLIGATORIO
Aplica “Editorial clara”: fondo #F7F5F0, superficies blancas, tinta #18212B, texto secundario #52606D, acento editorial #B42318 y acciones #1D4ED8. Newsreader para titulares, Roboto para interfaz y lectura. Respeta las tablas completas de tamaños, espaciados, radios, composición y estados del documento. Cuadrícula editorial, fotografías cuidadas, bordes discretos y tarjetas sin sombras decorativas. No conviertas la portada en una landing comercial ni añadas gradientes, glassmorphism o carruseles automáticos.

TRABAJO FUNCIONAL
- Implementa portada con una noticia principal, dos secundarias, últimas noticias y cinco categorías: Actualidad, Tecnología, Economía, Cultura y Deportes.
- Crea 20 noticias ficticias originales en español, cuatro por categoría, con contenido completo, fechas estables, autor ficticio y lectura individual. Usa aviso global de demostración y etiqueta en cada artículo. Separa dataset y componentes para sustituirlo por una API más adelante.
- Obtén y descarga fotografías ilustrativas pertinentes con condiciones de uso verificadas. Usa rutas locales estables, tamaños responsive y créditos en docs/image-credits.md. No uses URLs inventadas, imágenes aleatorias o fotografías como prueba del hecho ficticio.
- Haz funcionales categorías, búsqueda local, lectura, guardados persistidos localmente y estado en URL. Respeta Atrás/Adelante, enlaces directos y restauración de scroll/foco. No dejes acciones vacías.
- En móvil usa header compacto y barra inferior con Inicio, Secciones, Buscar y Guardados. Respeta safe areas, teclado y área táctil. En tablet/escritorio aplica la navegación y cuadrícula del documento.
- Implementa estados vacíos, imagen fallida, noticia desconocida, foco, hover y pulsación. No añadas esperas artificiales a datos locales.
- Si existe una app nativa, adapta los tokens a su plataforma. Si solo hay web, entrega la experiencia responsive tipo app sin crear otra aplicación por iniciativa propia.

CALIDAD Y ENTREGA
Verifica la matriz de aceptación del Markdown: 320–1440 px, móvil horizontal, texto ampliado, teclado, contraste, reduced motion, historial, búsqueda, guardados y lectura. Ejecuta los scripts pertinentes que realmente existan. Captura portada y artículo en móvil/escritorio y búsqueda móvil, corrige lo que falle y registra la evidencia en docs/verificacion-frontend.md.

Entrega el frontend implementado, documentación actualizada, dataset e imágenes con créditos. Explica qué cambiaste, qué verificaste y cualquier limitación concreta. No declares completada una verificación que no hayas realizado. Si hay un bloqueo de acceso a assets o instalación, descríbelo con precisión y completa todo el trabajo disponible sin inventar resultados.
```

## 13. Fuentes y trazabilidad

- Repositorio oficial de la habilidad: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- README consultado mediante GitHub; blob SHA: `8c4918afb508556ff45c5514798d3d671a4525ac`.
- Habilidad instalada: consultas de sistema visual y producto detalladas en el apartado 2; reglas móviles de `references/pro-rules.md`.
- Paleta marfil/tinta, composición concreta, tamaños, rutas y dataset propuesto: decisiones de esta especificación, no una reproducción literal del generador.
- El agente debe registrar por separado las fuentes de imágenes y tipografías que efectivamente incorpore.

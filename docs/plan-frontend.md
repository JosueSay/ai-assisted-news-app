# Plan frontend editorial

## Diagnostico

- Stack real: Expo + React Native + TypeScript.
- Marca existente: `AI News`; se conserva.
- Navegacion previa: estado local simple sin router.
- Contenido previo: tres noticias demo sin categorias, lectura ni guardados.
- Estilo previo: paleta oscura basica, incompatible con la identidad editorial clara.

## Tokens aplicados

- Fondo marfil `#F7F5F0`.
- Superficie `#FFFFFF`.
- Tinta `#18212B`.
- Texto secundario `#52606D`.
- Acento editorial `#B42318`.
- Accion `#1D4ED8`.
- Titulares con Newsreader; interfaz y lectura con Roboto.

## Componentes

- `AppButton`: variantes primaria, secundaria y ghost.
- `ArticleImage`: imagen real cuando exista; fallback honesto cuando falte asset.
- `ArticleCard`: variantes lead, standard, secondary y compact.
- `NewsFeedScreen`: portada, secciones, busqueda, guardados y lectura.

## Datos

- Dataset local en `frontend/src/data/demoArticles.ts`.
- 20 noticias ficticias en espanol, cuatro por categoria.
- Cada noticia tiene slug, autor ficticio, fecha fija, cuerpo, minutos de lectura y metadata de imagen.

## Navegacion

- Estado interno compatible con hash en web:
  - `#/inicio`
  - `#/secciones`
  - `#/buscar?q=...`
  - `#/guardados`
  - `#/seccion/<categoria>`
  - `#/noticia/<slug>`
- En nativo se usa el mismo estado sin dependencia de router externa.

## Pendientes

- Descargar fotografias reales con licencias verificadas y documentarlas.
- Dividir `NewsFeedScreen` en subcomponentes menores si la pantalla sigue creciendo.
- Verificar visualmente con capturas en 320, 375, 768, 1024 y escritorio.
- Medir contraste y performance en entorno representativo.

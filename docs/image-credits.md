# Creditos de imagenes

Estado: imagenes del dataset demo verificadas (Loop 08, 2026-10-19).

El dataset demo usa imagenes de Wikimedia Commons con URL HTTPS estable,
credito y licencia. El catalogo ejecutable y la procedencia completa estan en
`backend/news/demo_images.py` y
`docs/design/database/13-imagenes-demo.md`.

Cada asset visible registra en el documento `news.image`:

- `url` HTTPS del archivo o de su miniatura de Commons;
- `credit` con autor, titulo y pagina `File:` de Commons;
- `rights` con la licencia y su URL;
- `alt` que declara el uso ilustrativo y que la imagen no documenta el
  acontecimiento ficticio.

No se descargaron ni se versionaron binarios: el frontend consume la URL
remota y muestra "Imagen no disponible" si la red falla. Las noticias con
`image.type = none` mantienen `url` y `alt` en `null`.

`make db-news-images-check` comprueba por HTTP que las URLs responden con
`Content-Type: image/*`. Un `200` no sustituye la verificacion de licencia,
que se hizo individualmente en la pagina del archivo.

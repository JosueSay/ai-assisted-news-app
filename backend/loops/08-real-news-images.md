# Loop 08 — Imágenes reales para noticias demo

## Objetivo

Reemplazar las URLs placeholder de imágenes del dataset demo por imágenes reales y visualizables, manteniendo trazabilidad de:

- procedencia;
- crédito;
- derechos/licencia;
- tipo de imagen;
- relación con la noticia demo;
- contenido generado/modificado mediante IA cuando corresponda.

Este loop modifica únicamente la representación visual del dataset demo y lo necesario para validarla, sembrarla y documentarla.

NO implementar nuevas funcionalidades de producto.

---

## Skills

Principal:

`.skills/test-driven-development/SKILL.md`

Antes del commit:

`.skills/code-reviewer/SKILL.md`

Usar:

`.skills/security-compliance/SKILL.md`

solo si aparece un cambio relacionado con seguridad, URLs o recursos externos que lo justifique.

Usar `systematic-debugging` únicamente ante fallos inesperados.

---

## Lecturas obligatorias

Leer:

- `AGENTS.md`;
- handoffs 05–07;
- `docs/design/database/`;
- `backend/news/demo_news.py`;
- `backend/news/models/news.py`;
- tests del generador;
- seeder/check de noticias;
- Makefile.

No modificar el diseño fuera de este alcance.

---

# 1. Problema actual

Las noticias demo utilizan URLs placeholder como:

`https://example.com/demo/img/...`

Estas URLs cumplen estructuralmente el modelo pero no proporcionan imágenes visibles en la aplicación.

El dataset debe utilizar recursos visuales realmente accesibles.

---

# 2. Principio de las imágenes

Las imágenes deben ser:

- accesibles mediante HTTPS;
- apropiadas para la noticia sintética;
- provenientes de una fuente cuya utilización sea razonablemente documentable;
- estables para desarrollo/demo;
- no engañosas.

No presentar una fotografía real como evidencia del acontecimiento ficticio descrito por una noticia demo.

Las noticias siguen siendo:

`DEMO / SYNTHETIC DATA`

---

# 3. Procedencia

Cada imagen externa debe conservar como mínimo:

- URL utilizada por la app;
- crédito;
- información de derechos/licencia disponible;
- tipo.

Usar los campos existentes:

`image.url`
`image.credit`
`image.rights`
`image.type`
`image.aiDisclosure`

No agregar campos al modelo salvo necesidad demostrada.

---

# 4. Selección de fuentes

Preferir fuentes que permitan uso claro y estable para demo/desarrollo.

No utilizar:

- hotlinks arbitrarios de medios;
- Google Images;
- imágenes cuya licencia/procedencia no pueda explicarse;
- URLs temporales;
- URLs que requieran autenticación;
- URLs con tokens;
- imágenes de acontecimientos reales que puedan confundirse con evidencia de la noticia ficticia.

Si se utilizan servicios de imágenes con URLs públicas, documentar el origen y las condiciones relevantes.

---

# 5. Estrategia visual

No es obligatorio que las 32 noticias tengan 32 imágenes distintas.

Se permite reutilizar imágenes cuando conceptualmente corresponda, pero evitar que todo el dataset parezca idéntico.

Debe mantenerse cobertura de los tipos existentes cuando sea posible:

- photograph;
- illustration;
- ai_generated;
- ai_modified;
- none.

Para `none`:

`url = null`

y no debe agregarse imagen.

---

# 6. Fotografías

Las fotografías reales utilizadas son únicamente ilustrativas.

Debe quedar claro documentalmente que:

> La fotografía representa visualmente el tema general y no documenta el acontecimiento ficticio descrito por la noticia demo.

No utilizar fotografías de personas identificables cuando no sean necesarias.

---

# 7. IA

Para fixtures:

`ai_generated`
`ai_modified`

no fingir que una imagen real externa fue generada mediante IA.

Si actualmente no existen assets realmente generados/modificados con IA disponibles, mantener esos fixtures únicamente cuando puedan representarse honestamente.

Si cumplir correctamente esto requiere generar o almacenar assets propios, detener esa parte y reportar la decisión en vez de etiquetar incorrectamente imágenes externas.

---

# 8. URLs

Agregar una comprobación de disponibilidad separada de los tests unitarios normales.

Los tests offline NO deben depender de Internet.

La validación offline debe comprobar:

- HTTPS;
- host válido;
- no `example.com` para imágenes que deberían visualizarse;
- coherencia con `type`.

Crear una comprobación explícita, por ejemplo:

`make db-news-images-check`

Esta comprobación puede realizar requests HTTP únicamente cuando el desarrollador la ejecuta explícitamente.

---

# 9. HTTP check

La comprobación online debe:

- utilizar timeout corto;
- seguir redirects razonables;
- aceptar únicamente respuestas exitosas;
- comprobar cuando sea viable que `Content-Type` sea `image/*`;
- no descargar archivos completos cuando HEAD o una petición parcial sea suficiente;
- reportar URL/noticia fallida;
- no modificar DB.

No considerar una URL accesible como prueba de licencia o veracidad.

---

# 10. Determinismo

El dataset debe seguir siendo determinista.

No usar APIs aleatorias como:

`source.unsplash.com/random`

ni URLs cuyo contenido cambie arbitrariamente entre ejecuciones.

Las mismas fixtures deben producir las mismas URLs.

---

# 11. Seeder existente

Actualmente `db-seed-news` NO modifica noticias existentes.

Por seguridad, mantener ese comportamiento.

No convertirlo en update/upsert destructivo solo para cambiar imágenes.

El cambio de fixtures significa que Atlas/local pueden quedar con las versiones anteriores.

Por tanto, utilizar el mecanismo seguro de reseed existente para reconstruir el dataset controlado cuando corresponda.

NO modificar documentos externos.

---

# 12. Actualización local

Después de cambiar fixtures:

1. tests;
2. check online de imágenes;
3. reseed dry-run local;
4. reseed local autorizado;
5. news check;
6. images check;
7. db-verify.

Verificar que las 32 noticias reconstruidas correspondan a las fixtures nuevas.

---

# 13. Atlas

El agente NO debe ejecutar reseed destructivo contra Atlas.

Debe:

- validar fixtures offline;
- ejecutar comprobación HTTP de imágenes;
- ejecutar Atlas dry-run;
- proporcionar comando manual exacto al desarrollador.

El desarrollador decidirá si aplica el reseed Atlas.

---

# 14. Tests

Aplicar TDD.

Cubrir como mínimo:

- fixtures deterministas;
- URLs de imágenes válidas;
- ninguna imagen visible usa `example.com`;
- `none` mantiene URL nula;
- photograph tiene crédito/derechos;
- illustration tiene crédito/derechos;
- ai_generated exige disclosure;
- ai_modified exige disclosure;
- check HTTP separado de tests offline;
- fallo HTTP se reporta;
- Content-Type no imagen se reporta;
- check no modifica DB.

No hacer requests reales desde `make db-test`.

---

# 15. Documentación

Crear:

`docs/design/database/13-imagenes-demo.md`

Documentar:

- problema de placeholders;
- estrategia elegida;
- procedencia;
- licencias/créditos;
- diferencia entre ilustración y evidencia;
- IA;
- validación offline;
- validación HTTP;
- actualización mediante reseed;
- limitaciones.

Actualizar:

- `backend/news/README.md`;
- `docs/design/database/README.md`;
- `10-generador-noticias-demo.md`;

cuando corresponda.

---

# 16. Makefile

Agregar:

`db-news-images-check`

Debe ser:

- no destructivo;
- explícitamente online;
- independiente de `db-test`.

No romper comandos existentes.

---

# 17. Verificación

Ejecutar:

`make db-test`

Después:

`make db-news-images-check`

Después validar local mediante el flujo seguro de reseed.

No continuar si existen URLs rotas.

---

# 18. Code review

Aplicar `code-reviewer`.

Revisar especialmente:

- URLs;
- determinismo;
- licencias/créditos;
- etiquetado IA;
- ausencia de hotlinks inseguros;
- requests HTTP;
- timeouts;
- tests;
- comportamiento del reseed.

---

# 19. Seguridad

Confirmar:

- secrets exposed: NO;
- keys read directly: NO;
- external APIs with credentials: NO;
- external documents modified: NO;
- Atlas destructive reseed by agent: NO;
- assistant modified: NO.

---

# Commit

Si Definition of Done está completa:

`fix: use real images for demo news`

No hacer push.

---

# Handoff

Crear:

`backend/loops/handoffs/08-real-news-images-result.md`

Incluir:

1. Resultado.
2. Skills.
3. Problema corregido.
4. Estrategia de imágenes.
5. Fuente(s).
6. Licencias/créditos.
7. Distribución de tipos.
8. IA/disclosures.
9. Determinismo.
10. Tests.
11. HTTP image check.
12. Resultado local.
13. Atlas dry-run.
14. Comando manual Atlas.
15. Documentación.
16. Makefile.
17. Code review.
18. Seguridad.
19. Archivos modificados.
20. Decisiones.
21. Blockers.
22. Git.

---

# Definition of Done

Loop 08 termina cuando:

- las imágenes visibles ya no utilizan placeholders inexistentes;
- las URLs son deterministas;
- las URLs fueron comprobadas online;
- las imágenes tienen procedencia/crédito/derechos;
- las fotografías no se presentan como evidencia del evento ficticio;
- etiquetado IA es honesto;
- tests offline pasan;
- HTTP check pasa;
- local fue actualizado y verificado;
- Atlas dry-run fue verificado;
- Atlas NO fue reseedeado por el agente;
- documentación está sincronizada;
- Makefile está sincronizado;
- code-reviewer fue aplicado;
- no se expusieron secretos;
- existe handoff;
- existe commit.

---

# Stop Conditions

Detener y solicitar decisión humana si:

- no puede determinarse un uso razonablemente permitido de las imágenes;
- para mantener `ai_generated`/`ai_modified` es necesario generar assets propios;
- se requiere cambiar el modelo;
- se requiere modificar schema;
- una fuente exige API key;
- se requiere almacenar binarios nuevos sin decisión previa;
- se necesita ejecutar reseed destructivo en Atlas;
- se necesita modificar `backend/assistant/`.

No resolver silenciosamente.

# fix: alinear API y chat con el contrato canónico de noticias

Tras integrar los PR #4 (`c756e4f`) y #5 (`4228506`), el chat y la API reutilizaban
los modelos de DB, pero mantenían catálogos de cinco temas y el arranque recomendado
usaba el seeder antiguo. Esto descartaba o clasificaba incorrectamente noticias del
dataset aprobado de 32 documentos.

Ahora API, frontend y chat consumen los 14 topics canónicos. Las categorías y enums
TypeScript se generan desde Python y su comprobación detecta drift. El HTTP conserva
topics, ubicación, verificación, todas las fuentes y metadatos de imágenes/IA. El
detalle por slug permite abrir citas fuera de la página del feed.

La publicación y el chat administrativo comparten `local-admin:<username>` y el
mismo Bearer verificado en servidor. Se conserva el ObjectId anterior y el perfil
existente; no se fusionan ni eliminan datos antiguos. El arranque local del chat
selecciona `news` y su prompt, igual que Docker. La documentación utiliza
`db-bootstrap` / `db-verify` y conserva `db-seed-demo` como legacy explícito.

El esquema, modelos de persistencia, catálogos, índices, validators, TTL, generador
y seeders aprobados en `4228506` permanecen intactos. No se cierra la validación de
strings topics ni se implementa Firebase Authentication.

El chat consulta MongoDB para contar noticias y listarlas por país, en lugar de
confundir sus cinco ejemplos con la colección completa. Los conteos distinguen
total, publicadas y borradores; los grupos ofrecen cantidades y un ejemplo por
país. Ambos casos usan `database_query` y no consumen IA. Los filtros de país/tema
se aplican en MongoDB antes del límite de ejemplos. El contexto LLM incluye
inventario real, alcance de la selección y países resueltos desde `locations`;
el prompt `news-v3` distingue muestras y totales y prioriza los datos actuales.
El planificador también usa los mensajes de la sesión para seguimientos como
«de qué países son», «resúmelas» y «ok sí hazlo», manteniendo las citas y filtros
que correspondan. El historial del proveedor incluye la oferta anterior; las
aceptaciones ambiguas deben aclarar la opción deseada. Se conservan TTL y aislamiento.

Validación:

- 311 pruebas backend aprobadas; dos checks opcionales omitidos en el montaje offline.
- TypeScript y 11 pruebas frontend aprobadas; Expo export web correcto.
- Integración con MongoDB 8 efímera: bootstrap idempotente, 28 publicaciones,
  filtros de los 14 topics, citas, token/identidad admin y esquema aprobados;
  conteos 32/28/4 y 37/33/4 al coexistir los datasets, agrupación por país y
  actualización del conteo al crear un borrador mediante API.
  Seguimientos de tres turnos mantienen sesión, seis mensajes y las mismas citas.
- `make news-contract` y `make news-contract-check` aprobados.
- Ruff, configuración Compose y `git diff --check` aprobados.

La integración no monta secretos, no publica MongoDB y no usa Atlas ni volúmenes
existentes. No se realizaron migraciones, reseeds destructivos ni llamadas reales
a IA. Detalles y trazabilidad en
`backend/loops/handoffs/news-shared-contract-result.md`.


También se incorpora selección explícita del proveedor mediante `make chatbot-stub`
y `make chatbot-api` (`chatbot-openai`), conservando el resto de `.env`. El modo
API comprueba presencia del archivo de key sin leerlo y exige precios configurados.
`make chatbot-config-test`: 11 pruebas aprobadas sin DB ni credenciales. Handoff:
`backend/loops/handoffs/chatbot-provider-selection-result.md`.

Consulta DB, contexto geográfico y prompt:
`backend/loops/handoffs/news-chat-database-queries-result.md`.

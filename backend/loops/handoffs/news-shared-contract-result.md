# News Shared Contract — Result

## Identificación del loop

- Identificador: `news-shared-contract`.
- Nombre: alineación del contrato compartido entre DB, API, frontend y chat.
- Fecha de cierre: 2026-10-15.
- Estado: completado; cambios pendientes de commit.
- Continuidad: parte del handoff `news-chat-integration-result.md` y de los
  resultados DB 04–07. Conserva la numeración de esos loops y el baseline `4228506`.
- Handoff: `backend/loops/handoffs/news-shared-contract-result.md`.

## Skills utilizadas

| Skill | Aplicación y evidencia |
| --- | --- |
| [planning-with-files](../../../.skills/planning-with-files/SKILL.md) | Plan y memoria de trabajo en `/tmp/news-contract-alignment/task_plan.md`; resultados duraderos volcados en este handoff. |
| [test-driven-development](../../../.skills/test-driven-development/SKILL.md) | Regresiones escritas antes de implementar: 13 fallos backend y uno frontend reproducidos; correcciones y suite final aprobada con las fixtures canónicas. |
| [systematic-debugging](../../../.skills/systematic-debugging/SKILL.md) | Localización de la normalización desigual de `medio_ambiente` y del mínimo de espacio libre de MongoDB en la prueba temporal; causa, corrección y reintento documentados. |
| [code-reviewer](../../../.skills/code-reviewer/SKILL.md) | Revisión de contratos, identidad administrativa, diff, compatibilidad y comparación de los archivos protegidos contra `4228506`. |
| [security-compliance](../../../.skills/security-compliance/SKILL.md) | Verificación del Bearer administrativo, prueba sin secretos, escaneo acotado y tabla de riesgos/controles incluida en este handoff. |
| `ui-ux-pro-max` (skill del entorno) | Guía acotada para carga/errores al abrir citas, semántica accesible y conservación de componentes/tokens existentes. Se registran abajo los límites de validación visual. |

## Objetivo y autorización

Alinear la integración de chat del PR #4 (`c756e4f913846ce782e32b696f69616ca3b67741`)
con el esquema, base, modelos y seeders del PR #5
(`42285068fc8571a933a9ca47d03e0b98e3386f67`), según instrucción explícita del usuario.
Se revisaron el handoff de integración y los handoffs de los loops 04–07. El alcance
es mantenimiento de los consumidores existentes, autorizado en AGENTS.md.

## Resultado

Completado. El dominio aprobado continúa en `backend/news/`. No cambian modelos de
persistencia, colecciones, campos, enums, validators, índices, TTL, catálogo TOPICS,
dataset ni seeders. Se comprobó su igualdad con `4228506` mediante Git.

- API usa los 14 topics; preserva topics, alcance, verificación, todas las fuentes y
  metadatos de imagen/IA en el contrato HTTP. Conserva campos de presentación existentes.
- Chat deriva filtros de `news.topics.TOPICS`, mantiene separados ciencia/tecnología
  y negocios/economía, y normaliza correctamente medio_ambiente.
- Expo recibe categorías y tipos de enums (incluidos estrategia, intención y confianza
  del chat) generados desde Python. Los filtros comparan todos los topics de la noticia.
- Las citas consultan el detalle por slug aunque falte en la página del feed.
  Se conservan estados de carga/error y se muestran verificación, fuentes y declaración IA.
- Administración y chat utilizan la misma identidad local-admin y ObjectId previo,
  con el mismo token verificado en servidor. El perfil existente se conserva.
- Entry point `assistant.news_chat.run` carga el .env raíz y selecciona news/news.md;
  Docker utiliza el mismo entry point e instala también los requisitos de news.
  Los modos históricos permanecen explícitos mediante assistant.app.
- Se corrigió la resolución de keys/... desde el .env raíz; ../../keys/... legacy
  conserva su resolución. No cambian los nombres ni contenidos de secretos.
- Compose monta el código compartido y levanta chatbot junto con frontend; los
  cambios Python requieren reiniciar procesos. Cambios de dependencias requieren rebuild.
- Arranque recomendado usa db-bootstrap/db-verify (32 fixtures), conservando
  db-seed-demo como legacy explícito. No se ejecutaron seeders en DB existentes.

## Archivos creados/modificados

Nuevos: `backend/news/{presentation,export_contract,identity}.py`,
`backend/assistant/news_chat/run.py`, `frontend/src/generated/newsContract.ts`,
`backend/news/tests/test_export_contract.py`,
`backend/assistant/tests/test_shared_news_contract.py`,
`tests/integration/test_news_shared_contract.py`, `scripts/news-integration-test.sh`,
`backend/.dockerignore`, `docs/architecture/contrato-compartido-noticias.md` y este handoff.

Modificados: `backend/news/{api,auth,config}.py`,
`backend/assistant/{app.py,Dockerfile}`, `backend/assistant/news_chat/{intent,retrieval,service}.py`,
tests de API/config/news_app, frontend types/services/NewsFeedScreen y tests,
Makefile, Compose, PR_DESCRIPTION.md, READMEs raíz/news/assistant/frontend/integración,
y notas de vigencia en docs/api/README.md y docs/architecture/README.md.
Se documentan consumidores en docs/design/database/09-catalogos-y-seeders.md.

## Decisiones

- No cerrar topics a nivel de DB/modelos: continúan strings libres según la decisión
  pendiente del diseño. El catálogo aprobado no se modifica.
- DTOs de transporte convierten ObjectId a string; reutilizan Source y AiAssistance
  canónicos y no crean un esquema Mongo paralelo.
- No fusionar/eliminar usuarios admin antiguos ni migrar sus sesiones automáticamente.
  En adelante se usa la identidad canónica después de verificar el token.
- No introducir ODM, nuevas dependencias arquitectónicas, Firebase ni ingesta.
- La prueba de integración utiliza MongoDB efímera sobre tmpfs y una red interna;
  no monta keys/, volúmenes de datos ni publica puertos. Solo retira recursos propios.

## Comandos y verificaciones

- Tests red: fixtures canónicas reprodujeron 13 fallos backend y el filtro multitema
  del frontend falló antes de implementar las correcciones.
- Docker offline con código readonly, sin red/keys, ejecutando
  `python -m pytest -c assistant/pyproject.toml assistant/tests news/tests -q -p no:cacheprovider`.
- `npm run typecheck` y `npm test` desde frontend.
- `EXPO_NO_DOTENV=1 EXPO_NO_TELEMETRY=1 npx expo export --platform web --output-dir /tmp/news-contract-alignment/web`.
- `make news-contract` y `make news-contract-check`; exportador directo con --check.
- `make news-integration-test`: construye una imagen con requisitos de ambos módulos.
- Ruff sobre archivos afectados; news se comprueba con target py310 por su compatibilidad
  documentada, assistant con su configuración py312. Formato revisado.
- `docker compose --env-file /dev/null --profile news-local config --quiet`,
  `bash -n scripts/news-integration-test.sh`, `git diff --check` y revisión del diff.
- Comparación contra 4228506 de modelos/schema/TOPICS/seeders/dataset/bootstrap/reseed/
  verify y 07-diagrama: sin diferencias.
- Escaneo seguro limitado a archivos del cambio, excluyendo keys y env: ocho
  hallazgos mongodb-uri corresponden a ejemplos/local/fixture sin credenciales;
  no se reprodujeron valores. No hay secretos staged (staging vacío).

## Tests y resultados

- Backend: 275 aprobados, 1 omitido (smoke HTTP contra el servicio externo configurado).
- Frontend: 11 aprobados y TypeScript correcto.
- Expo web: bundle exportado correctamente (2237 módulos).
- MongoDB 8 real efímera: 1 prueba de integración aprobada. Bootstrap inicial
  crea 16 ubicaciones/32 noticias; la segunda ejecución no inserta nada. API expone
  28 publicaciones y los 14 temas; cada cita abre su detalle. Token/identidad admin,
  validators, índices y TTL correctos; aiUsage vacío con stub.
- El primer intento de integración falló por el mínimo de espacio libre de MongoDB
  en tmpfs de 512 MiB. Se amplió únicamente ese recurso temporal a 1 GiB; reintento aprobado.
- Advertencia deprecada de Starlette/httpx ya presente; no afecta los resultados.
- Contenedores/red de integración retirados al finalizar; no se tocaron datos existentes.

## Revisión de seguridad acotada

| Riesgo | Control y evidencia |
| --- | --- |
| Reclamar identidad admin desde el cliente | Bearer validado con el mismo verificador de la API; 401 sin token o con token inválido |
| Divergencia de temas/enums | Generación TypeScript + check versionado y regresión con las 32 fixtures |
| Exposición de credenciales en builds/tests | Contexto backend excluye env/cache; keys fuera del contexto y sin montar en integración |
| Tests contra DB real del desarrollador | MongoDB propia, red interna, nombre de host validado y DB inicialmente vacía |
| Sobrescritura de usuarios/datos | Se preserva perfil canónico; no migraciones, drops o reseeds sobre datos existentes |

## Trazabilidad

- [x] Modelos revisados: sin cambios frente a 4228506; API/chat importan los mismos.
- [x] Documentación sincronizada: contrato actual, arranque, tipos, tests y PR description.
- [x] Diagrama revisado: 07-diagrama sin cambios porque no hay cambios estructurales;
  el flujo de consumidores se documenta aparte en docs/architecture.
- [x] Tests sincronizados: contrato canónico, identidad, rutas locales e integración real.
- [x] Makefile sincronizado: news-contract, news-contract-check, news-integration-test.
- [x] Secrets/bootstrap revisados: mismos archivos requeridos, setup-keys y keys/README
  no requieren cambios. No se leyó, modificó ni imprimió contenido de keys/.
- [x] Seeders y scripts revisados: seeders aprobados intactos; harness nuevo aislado.

## Pendientes y límites

No bloqueos para este cambio. Atlas y llamadas reales a OpenAI no se ejecutaron.
No se probó visualmente en dispositivo ni se hizo auditoría de temas/dynamic type;
la UI conserva componentes/tokens existentes y se verificó mediante types/tests/bundle.
Google/invitado siguen con identidad provisional; la autenticación verificada y una
migración de identidades antiguas requieren trabajo separado. No se redefine el
flujo JEV de capacidades ni el presupuesto en este cambio.

## Git y continuidad

Sin commit ni push. Working tree con los cambios de este handoff, staging vacío;
ningún secreto staged. No se modifica la historia. Para revisar: `git diff`,
`make news-contract-check`, `make news-integration-test`.
El despliegue debe reconstruir los servicios para incorporar los cambios de
requisitos/entry point y reiniciarlos; no requiere migración de esquema ni reseed.

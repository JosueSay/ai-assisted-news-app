# Chatbot Provider Selection — Result

## Identificación

- Loop: `chatbot-provider-selection`.
- Fecha: 2026-10-15.
- Estado: completado, sin commit ni push.
- Handoff anterior revisado: `news-shared-contract-result.md`.
- Objetivo autorizado: elegir mediante Make entre chat stub y API OpenAI, con DB
  local o Atlas, respetando el dominio y seeders del PR `4228506`.

## Skills utilizadas

| Skill | Uso |
| --- | --- |
| `test-driven-development` | Ocho tests fallaron antes de implementar; regresión adicional para valores entre comillas exportados por Make. Once tests finales aprobados. |
| `code-reviewer` | Revisión de actualización atómica de .env, preservación de DB/URLs/permisos, guardas y pruebas de los targets Make aislados. |
| `systematic-debugging` | El caso entre comillas se reprodujo, se trazó a los valores literales exportados por Make y se corrigió normalizando esos parámetros antes de validarlos. |
| `security-compliance` | Comprobación de key exclusivamente por metadatos, sin leer secretos; tests temporales, validación de valores y ausencia de llamadas a IA. |

No se requirió planificación multifase ni skill de UI. No se cargaron skills ajenas
al alcance ni se delegaron tareas.

## Cambios y archivos

- `Makefile`: `chatbot-stub`, `chatbot-api`, `chatbot-openai` y
  `chatbot-config-test`. Los precios/modelo pueden pasarse como variables Make
  exportadas sin interpolación en comandos shell.
- `scripts/configure_chatbot.py`: selector stdlib. Requiere .env existente, conserva
  la configuración restante y permisos, elimina definiciones duplicadas de campos
  seleccionados y reemplaza el archivo atómicamente al completar las validaciones.
- `tests/unit/test_configure_chatbot.py`: once pruebas sin Docker, DB ni secretos.
- `README.md`, `backend/assistant/README.md` y `.env.example`: documentan elección,
  requisitos del modo API y aplicación mediante `make chatbot-up`.
- Este handoff registra el loop y sus evidencias.

## Comportamiento y decisiones

`make chatbot-stub` guarda CHATBOT_PROVIDER=stub, sin exigir key ni precios.
`make chatbot-api` / `make chatbot-openai` seleccionan OpenAI si existe un archivo
regular no vacío keys/openai_api_key y ambos precios por millón de tokens son
finitos y no negativos, conforme a la configuración existente del assistant.
No se inventan tarifas ni se cambia el presupuesto. OPENAI_MODEL es opcional;
si no está configurado, la aplicación conserva su default existente.

El selector no lee contenido de keys/. La validez de la credencial solo la
comprueba la aplicación al usar el proveedor. No se agrega ni cambia ningún
archivo secreto requerido; setup-keys y keys/README no necesitan modificaciones.
No se levantan contenedores ni se hacen llamadas a IA al seleccionar el modo.
`make chatbot-up` aplica la elección después de una configuración exitosa.

Los comandos env-local/env-atlas siguen creando un .env completo con stub;
la selección del proveedor se realiza después. Si faltan requisitos, el selector
termina sin modificar .env. Conserva DB, URLs, parámetros ajenos y comentarios
fuera de los campos seleccionados. No se acepta .env como symlink.

## Comandos y resultados

- `python3 -m unittest discover -s tests/unit -p test_configure_chatbot.py -v`: red
  inicial (8 fallos), luego green.
- `make chatbot-config-test`: 11 tests aprobados (idempotencia, preservación de
  configuración, requisitos faltantes, valores inválidos/cotizados, no lectura de
  secretos, y ejecución real de Make stub/API dentro de proyectos temporales).
- Ruff check/format sobre los dos archivos nuevos: correcto (target Python 3.10).
- `git diff --check`: correcto.
- Revisión del diff de Makefile/.env.example y del selector; staging sin cambios.

Las pruebas no abren ni modifican el .env real ni archivos secretos del workspace.
No se repitieron las suites de DB/UI: no cambia su comportamiento ni contrato.
Se conservó el trabajo previo sin commitear. No se ejecutó el selector sobre la
configuración real del usuario ni se inició el chatbot durante este loop.

## Trazabilidad

- [x] Modelos: revisados, sin cambios.
- [x] Documentación: comandos y requisitos sincronizados.
- [x] Diagrama: revisado; sin cambios estructurales, no requiere edición.
- [x] Tests: once pruebas nuevas y comando Make independiente.
- [x] Makefile: opciones y pruebas añadidas.
- [x] Secrets/bootstrap: mismos archivos; no se requiere actualización de setup-keys.
- [x] Seeders/esquema/DB del PR 4228506: sin cambios en este loop.

## Revisión de seguridad acotada

| Riesgo | Control |
| --- | --- |
| Leer una key al configurar el modo | Solo is_file/stat; test que rechaza cualquier apertura del archivo |
| Perder DB/URLs al seleccionar proveedor | Actualización de campos seleccionados; preservación e idempotencia probadas |
| Parámetros inválidos o inyección de líneas | Precios finitos, modelo restringido, normalización y ausencia de interpolación shell |
| Dejar un .env parcial o con permisos distintos | Archivo temporal, conservación del modo y reemplazo atómico |
| Activar consumo de IA durante configuración | Selección separada de chatbot-up; sin llamadas ni arranque automático |

## Pendientes, bloqueos y Git

Sin bloqueos. El usuario debe elegir el proveedor y completar manualmente los
requisitos de OpenAI si desea utilizarlo. No se verificaron credenciales reales,
precios externos, Atlas ni llamadas OpenAI; los tests usan valores ficticios
sin atribuirlos a un modelo real.

Sin commit/push. Working tree con este cambio y el trabajo previo de alineación;
staging vacío. No se modifica historia Git. No se ejecutaron operaciones DB,
migraciones ni reseeds. Para continuar: seleccionar modo, ejecutar chatbot-up y
retomar la prueba local guiada que solicitó el usuario.

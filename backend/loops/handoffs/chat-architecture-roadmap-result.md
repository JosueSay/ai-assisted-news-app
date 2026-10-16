# Chat Architecture Roadmap — Result

## Identificación y objetivo

- Loop: `chat-architecture-roadmap`.
- Fecha: 2026-10-15.
- Estado: documentación completada; implementación de las brechas pendiente.
- Objetivo solicitado: documentar los siguientes pasos de arquitectura del chat
  después de la confirmación del funcionamiento con Atlas.
- Handoff anterior leído: `news-chat-conversation-context-result.md`.
- Fuente de DB: `docs/design/database/`, especialmente criterios de chat y costos.
- Referencia funcional: diagrama JEV + CODE + LLM aportado por el usuario.

## Skills aplicadas

- `planning-with-files`: plan temporal en `/tmp/news-chat-architecture-docs/task_plan.md`.
- `code-reviewer`: contraste documental contra código, comportamiento y límites del
  dominio actual. No se implementaron cambios de comportamiento que requieran TDD.

## Cambios y archivos

Nuevo documento:

- `docs/architecture/chatbot-jev-code-llm-pendientes.md`.

Contiene el estado actual, dos diagramas Mermaid versionados, tabla de brechas
por bloque, propuesta inicial de catálogo, seis loops sugeridos con criterios de
aceptación, decisiones pendientes y checklist de cierre de la arquitectura.

Enlaces añadidos a:

- `README.md`.
- `docs/architecture/README.md`.
- `docs/architecture/contrato-compartido-noticias.md`.
- `backend/assistant/README.md`.
- `PR_DESCRIPTION.md`.

Este handoff es el segundo archivo nuevo del loop.

## Secuencia propuesta

1. `chat-capability-contracts`: estado, contexto de negocio y catálogo.
2. `chat-scope-routing`: OUT_OF_SCOPE, PARTIAL y BUSINESS.
3. `chat-partial-routing`: parte atendible y fallback.
4. `chat-capability-routing`: capacidad, parámetros y aclaraciones.
5. `chat-capability-execution`: dispatcher CODE/LLM y presentación común.
6. `chat-architecture-verification`: integración de memoria, rutas y verificaciones.

Son identificadores sugeridos, no loops ejecutados ni funcionalidades implementadas.
Se registró como pendiente la interpretación técnica de JEV; no se eligió motor,
framework, nueva colección ni dependencia arquitectónica por inferencia.

## Verificaciones y resultados

- Inspección de `intent.py`, `conversation.py`, `retrieval.py`, `service.py`,
  prompt news-v3, documentación vigente y handoff anterior.
- Búsqueda acotada de JEV, catálogo y routing: no hay implementación con el contrato
  completo del diagrama. Se documentan las piezas parciales existentes.
- Validación por script de enlaces relativos en los documentos afectados: correcta.
- Bloques Markdown cerrados, dos diagramas Mermaid y seis etapas: correctos.
- Diagramas revisados como fuente Mermaid; no se instala ni ejecuta un renderizador.
- `git diff --check`: correcto.
- Staging vacío. Sin commit ni push. Working tree conserva todos los cambios anteriores.
- No se ejecutaron suites de runtime: solo se modificó Markdown.

La salida de `make db-verify` en Atlas y el funcionamiento manual de las consultas
fueron proporcionados/confirmados por el usuario. Este loop no consultó Atlas,
MongoDB local ni OpenAI. Los 311 tests citados en el documento son la evidencia del
loop previo y no se presentan como una ejecución nueva.

## Trazabilidad

- [x] Modelos revisados: no modificados.
- [x] Documentación sincronizada: estado implementado separado del objetivo pendiente.
- [x] Diagrama revisado: dos flujos conversacionales añadidos; `07-diagrama.md` de DB no requiere cambios.
- [x] Tests revisados: criterios de futuras pruebas documentados; sin cambios de comportamiento.
- [x] Makefile revisado: no requiere cambios en este loop documental.
- [x] Secrets/bootstrap revisados: mismos archivos y responsabilidades, sin cambios.

## Continuidad

Próximo paso recomendado: definir contratos y catálogo en `chat-capability-contracts`.
La implementación futura debe mantener el esquema y seeders de `4228506`, sesiones
de 3600 segundos, citas publicadas, DB independiente de NOVU y presupuesto USD 20.
Si requiere estado persistido nuevo, se debe resolver y aprobar el cambio de DB
antes de implementarlo. No se amplía el alcance a autenticación o despliegue público.

Sin bloqueos para la tarea documental. Las decisiones técnicas pendientes están
visibles en el roadmap; no se detuvo ninguna implementación ya autorizada para
pedir aprobación. No se abrió ni modificó ningún secreto ni el `.env` real.

# Loop 08 — Arquitectura conversacional JEV + CODE + LLM

## Objetivo

Implementar el routing de alcance y capacidades del chat de noticias mediante
routers internos deterministas y un catálogo cerrado que separe ejecución CODE
de ejecución LLM.

Este documento se reconstruyó el 2026-10-17 desde el handoff de implementación
para completar la secuencia documental. No sustituye el prompt original ni
representa una ejecución nueva del loop.

## Fuentes y continuidad

- `AGENTS.md` y `docs/design/database/` como restricciones y diseño aprobado.
- [Roadmap previo](handoffs/chat-architecture-roadmap-result.md).
- [Arquitectura conversacional](../../docs/architecture/chatbot-jev-code-llm-pendientes.md).
- [Contexto conversacional previo](handoffs/news-chat-conversation-context-result.md).

## Alcance implementado

1. Contratos de turno y catálogo con `capability`, `execution`, `resource` y `presentation`.
2. Clasificación `OUT_OF_SCOPE`, `PARTIAL` y `BUSINESS` sin llamadas a IA.
3. Atención del fragmento de noticias en peticiones mixtas y ayuda de alcance.
4. Selección determinista de capacidades y parámetros desde el catálogo.
5. CODE para listados, detalle, búsqueda, conteos y agrupación por país;
   LLM únicamente para resumen y explicación de noticias publicadas.
6. Integración del historial, presentación, presupuesto y persistencia existentes.

Se mantienen la base `ai_assisted_news`, siete colecciones, TTL de 3600 segundos,
registro real en `aiUsage`, presupuesto funcional de USD 20 y modelos aprobados.
No se incorporan servicios externos de routing ni acceso arbitrario del modelo a MongoDB.

## Verificaciones y aceptación

- Suite aislada backend, sin credenciales ni Atlas.
- Integración contra MongoDB efímera con bootstrap, consultas, routing y esquema.
- Ruff check/format sobre módulos y pruebas afectados.
- Revisión del diff, seguridad y trazabilidad DB según `AGENTS.md`.

Los comandos exactos, resultados históricos y límites de la verificación están
en el handoff; esta reconstrucción documental no vuelve a ejecutarlos.

## Entregables

- [Handoff del loop 08](handoffs/08-chat-architecture-implementation-result.md).
- [Captura de telemetría OpenCode](images/loop-8-gpt-6-luna.png).

La captura registra trabajo del agente; no es gasto de producción ni un registro de `aiUsage`.

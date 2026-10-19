# Loop 09 — Contexto de noticia e historial del chat

## Objetivo

Al abrir el asistente desde una noticia, iniciar una consulta contextual y mejorar
el historial local, el scroll del hilo y el envío con Enter.

Este documento se reconstruyó el 2026-10-17 desde el handoff de implementación
para completar la secuencia documental. No sustituye el prompt original ni
representa una ejecución nueva del loop.

## Fuentes y continuidad

- `AGENTS.md` y `docs/design/database/` como restricciones y diseño aprobado.
- [Loop 08: arquitectura](08-chat-architecture-implementation.md) y su
  [handoff](handoffs/08-chat-architecture-implementation-result.md).
- [Integración del chat](handoffs/news-chat-integration-result.md).
- [Contexto conversacional](handoffs/news-chat-conversation-context-result.md).

## Alcance implementado

1. Enviar automáticamente «Explícame esta noticia: <título>» con el `newsId`
   existente al abrir el chat desde una noticia.
2. Mantener conversaciones locales por usuario, con migración del formato anterior
   y filtrado por vigencia de una hora.
3. Mostrar historial lateral en escritorio y desplegable en móvil.
4. Dar scroll propio al hilo, mostrar los últimos mensajes y enviar con Enter.
5. Evitar envíos durante la carga inicial o mientras hay una solicitud en curso.
6. Verificar que el backend recibe y atribuye el contexto a la noticia seleccionada.

Se conserva el contrato HTTP, el routing CODE/LLM y el TTL de MongoDB. No se
modifican modelos, colecciones, índices, validaciones, seeders, secretos o dependencias.

## Verificaciones y aceptación

- Pruebas del historial: aislamiento por usuario, expiración, títulos y migración.
- Prueba del envío conjunto de mensaje contextual y `newsId`.
- Regresión backend sobre contexto de noticia enviado al proveedor falso.
- Typecheck, tests frontend, exportación web y suite backend aislada.
- Validación visual/manual de CTA, historial, scroll y Enter en escritorio/móvil:
  **pendiente según el handoff original**.

Los comandos exactos, resultados históricos y límites de la verificación están
en el handoff; esta reconstrucción documental no vuelve a ejecutarlos.

## Entregables

- [Handoff del loop 09](handoffs/09-news-chat-context-and-ux-result.md).
- [Captura de telemetría OpenCode](images/loop-9-gpt-6-luna.png).

La captura registra trabajo del agente; no es gasto de producción ni un registro de `aiUsage`.

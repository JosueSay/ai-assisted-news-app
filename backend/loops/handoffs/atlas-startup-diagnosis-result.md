# Atlas startup diagnosis

- Fecha: 2026-10-17.
- Objetivo: diagnosticar el chatbot unhealthy al iniciar con Atlas.
- Skill: `.skills/systematic-debugging/SKILL.md`.
- Handoff previo consultado: `local-bootstrap-drift-diagnosis-result.md`.

## Evidencia y resultado

El chatbot falla durante el ping de arranque con
`ServerSelectionTimeoutError` y `TLSV1_ALERT_INTERNAL_ERROR` en el handshake
TLS con Atlas. Una conexión TLS independiente, sin credenciales y desde el
host, reproduce el fallo. La API responde HTTP 200 en `/health`, pero su
cuerpo declara `status=degraded`, `mongodbMode=atlas` y
`mongodbConnected=false`. El HTTP 200 no acredita conectividad a MongoDB.

El fallo observado precede a la autenticación MongoDB y a cualquier llamada
a OpenAI. No se atribuye todavía a una causa específica de configuración:
queda pendiente comprobar la IP pública autorizada en Network Access de Atlas,
el estado del clúster y, si persiste, restricciones de red/TLS.

## Acciones y verificaciones

- `docker compose ps --all`.
- Lectura de logs de chatbot y API con filtrado de URI y credenciales antes
  de emitir salida.
- Inspección de código de arranque, configuración, conexión y Dockerfiles.
- Handshake TLS con `socket` y `ssl` desde el host, sin claves ni URI secreta.
- GET local `/health` de la API, inspeccionando únicamente campos de estado.
- Consulta de documentación oficial MongoDB sobre TLS y acceso por IP.

No se ejecutaron tests unitarios: no hay cambios de comportamiento.
No se leyó ni modificó contenido de `keys/`, ni se ejecutaron operaciones DB,
seeders, llamadas IA o cambios de configuración.

## Cambios y continuidad

Único archivo creado por este diagnóstico: este handoff. Sin commit ni push.
El working tree conserva cambios anteriores ajenos al diagnóstico.
Se pidió al usuario comprobar/agregar su IP actual en Atlas y confirmar que
esté activa. Después se debe repetir el handshake y verificar conectividad
real antes de reintentar el arranque de los tres servicios.

## Trazabilidad

- Modelos: sin cambios estructurales; no requieren sincronización.
- Documentación: diagnóstico registrado en este handoff.
- Diagrama: sin cambios estructurales; no requiere actualización.
- Tests: sin cambios de comportamiento; no requieren actualización.
- Makefile: revisado en el contexto previo; sin cambios requeridos.
- Secrets/bootstrap: sin cambios de requisitos ni archivos secretos.

Estado: diagnóstico del fallo TLS confirmado; resolución pendiente de la
comprobación externa de acceso/red en Atlas. No se afirma que esté resuelto.

## Seguimiento: IP previamente activa

El usuario informa que su IP ya figuraba activa. Se repitió el handshake
sin credenciales contra los tres nodos, tanto con negociación predeterminada
como forzando únicamente TLS 1.2 con verificación de certificados: todos
fallan con la misma alerta TLS. Docker reproduce el fallo. Host y Docker
usan distintas versiones OpenSSL (3.6.3 y 3.5.6) y reportan la misma IP
pública de salida, consultada mediante HTTPS a `api4.ipify.org`.
No se almacena aquí la dirección personal; se mostró al usuario para
comparación exacta con Network Access del proyecto correspondiente.

Pendiente: confirmar coincidencia exacta de IP/proyecto, disponibilidad
del clúster y presencia de VPN. No se deshabilitó TLS ni se cambió código,
dependencias, credenciales o configuración. La causa externa concreta
sigue sin confirmarse.

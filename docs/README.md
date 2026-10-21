# Documentación del proyecto

Fuente central para decisiones y contratos que afectan a más de un servicio.

- `architecture/`: límites, dependencias y flujos entre componentes.
- `api/`: contratos HTTP y eventos compartidos.
- `decisions/`: decisiones de arquitectura con contexto y consecuencias.
- `testing/`: estrategia y comandos de validación global.
- `design/`: diseño de la base de datos MongoDB y sus criterios de uso.
- [Alcance pendiente del Proyecto 2](reviews/alcance-pendiente-proyecto-2.md): ocho
  puntos con estado actual, tareas concretas, alcance, abordaje y resultado esperado.
- [Firebase: configuración y verificación](reviews/firebase-auth-configuracion.md):
  guía del punto 1, conservada separadamente del alcance general.
- [Desplegar con Firebase paso a paso](deploy/firebase-paso-a-paso.md): configuración
  de Auth, Cloud Run, Atlas y publicación del portal en Hosting.

La documentación específica de un servicio permanece junto al servicio correspondiente.

# Preparación del despliegue

Guía operativa: [Firebase paso a paso](../docs/deploy/firebase-paso-a-paso.md).
Los scripts integran Firebase Auth, Cloud Run, CORS y Firebase Hosting. La
verificación automática usa comandos simulados y MongoDB temporal; no sustituye
la prueba en el proyecto Firebase real.

- [ ] Seleccionar el proyecto Firebase/Google Cloud y habilitar facturación.
- [ ] Registrar la app web, habilitar Google/Anonymous y autorizar los dominios.
- [ ] Configurar `PROJECT_ID`, región y Project ID Firebase común.
- [ ] Ejecutar `make gcp-bootstrap` y autorizar la IP NAT en Atlas.
- [ ] Completar manualmente los secretos requeridos en `keys/` y ejecutar
      `make gcp-secrets CHATBOT_PROVIDER=openai`; MongoDB y OpenAI son obligatorios.
- [ ] Configurar `OPENAI_MODEL` y sus precios de entrada/salida en el entorno o
      `deploy/gcp/config.sh`.
- [ ] Inicializar/verificar esquema y catálogos en la base de noticias.
- [ ] Ejecutar `ALLOW_PUBLIC=1 make gcp-deploy CHATBOT_PROVIDER=openai`.
- [ ] Completar `frontend/.env` con configuración pública Firebase y URLs HTTPS.
- [ ] Ejecutar `make firebase-check-config` y `make firebase-deploy`.
- [ ] Comprobar login, preferencias, lectura, feed y chat en el sitio publicado.
- [ ] Comprobar un resumen o explicación con IA y su registro en `aiUsage`.
- [ ] Si se activa CI: configurar las variables del entorno GitHub `production`,
      incluido `CHATBOT_PROVIDER=openai` y ambos precios.

No se requiere contraseña admin local ni clave JSON de cuenta de servicio para
verificar Firebase ID tokens. Hosting se publica por separado del pipeline Cloud
Run. No se ha ejecutado un deploy real como parte de esta integración.

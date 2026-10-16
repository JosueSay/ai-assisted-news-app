# Pruebas de integración

```bash
make news-integration-test
```

Construye la imagen de tests del assistant con los requisitos compartidos de news.
Crea una red Docker interna y una MongoDB temporal sin puertos publicados, sin
montar `keys/` y sin reutilizar volúmenes. El almacenamiento tmpfs es de 1 GiB
(MongoDB 8 exige espacio libre mínimo además del journal). Al terminar solo retira
los contenedores y la red creados por este comando; no ejecuta drops ni reseeds.

La prueba realiza bootstrap canónico dos veces, verifica las 32 noticias y 16
ubicaciones, consume las 28 publicaciones mediante la API y consulta los 14 topics
desde el chat, abriendo cada cita por slug. También verifica que administración y
chat compartan identidad y token y que se mantengan validators, índices y TTL.
Usa exclusivamente `stub`: no hay llamadas reales a IA ni credenciales externas.

Está separada de las suites unitarias y no se conecta a Atlas ni a la MongoDB de
desarrollo. Una ejecución directa sin el entorno del harness se omite.

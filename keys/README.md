# keys

Este directorio contiene archivos con secretos (URIs, API keys, tokens) necesarios para
ejecutar el proyecto en entorno local.

## Reglas

- **Nunca versionar** estos archivos. El directorio está en `.gitignore`.
- Cada archivo contiene **únicamente el valor del secreto**, sin metadatos, comentarios ni
  líneas adicionales.
- El proyecto no lee secretos de variables de entorno directamente: los lee desde estos archivos.

## Archivos requeridos

| Archivo | Propósito | ¿Debe crearlo el desarrollador? |
| --- | --- | --- |
| `mongodb_uri` | URI de conexión a MongoDB Atlas para la aplicación de noticias. | Sí |

## Formato esperado

### `mongodb_uri`

Contiene únicamente la URI de MongoDB Atlas. Sin comillas, sin saltos de línea extra:

```
mongodb+srv://usuario:contraseña@cluster.xxxxx.mongodb.net/
```

## Cómo crear `mongodb_uri`

1. Copiar la URI desde MongoDB Atlas (Database → Connect → Drivers).
2. Reemplazar `<password>` con la contraseña real.
3. Crear el archivo:

   ```bash
   echo 'mongodb+srv://...' > keys/mongodb_uri
   ```

4. Verificar que Git no lo trackea:

   ```bash
   git status keys/
   ```

## Seguridad

- No compartir el contenido de estos archivos.
- No incluirlos en logs, issues, tickets ni commits.
- Si por error se versiona un secreto, rotar la credencial inmediatamente.
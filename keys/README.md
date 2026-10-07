# keys

Este directorio contiene archivos con secretos (URIs, API keys, tokens) necesarios para
ejecutar el proyecto en entorno local.

## Reglas

- **Nunca versionar** estos archivos. `.gitignore` ignora todo el directorio excepto este README.
- Cada archivo contiene **únicamente el valor del secreto**, sin metadatos, comentarios ni
  líneas adicionales.
- El proyecto no lee secretos de variables de entorno directamente: los lee desde estos archivos.

## Archivos requeridos

| Archivo | Propósito | ¿Debe crearlo el desarrollador? |
| --- | --- | --- |
| `mongodb_uri` | URI de conexión a MongoDB Atlas para la aplicación de noticias. | Sí |
| `news_admin_password` | Contraseña local del usuario admin para crear noticias manualmente. | Sí |
| `client_id` | Identificador de cliente para autenticación futura (reservado). | Sí (vacío) |
| `client_secret` | Secreto de cliente para autenticación futura (reservado). | Sí (vacío) |

## Preparación automática

```bash
make setup-keys
```

Crea los archivos faltantes vacíos. No sobrescribe archivos existentes.

## Formato esperado

### `mongodb_uri`

Contiene únicamente la URI de MongoDB Atlas. Sin comillas, sin saltos de línea extra:

```
mongodb+srv://usuario:contraseña@cluster.xxxxx.mongodb.net/
```

### `client_id` y `client_secret`

Reservados para autenticación futura. Deben estar presentes aunque vacíos. No son leídos,
validados ni utilizados por la infraestructura de MongoDB actual.

### `news_admin_password`

Contiene únicamente la contraseña del admin local usado por `POST /admin/login`.
Debe tener un valor no vacío antes de intentar crear noticias desde el panel admin.
No colocar esta contraseña en `.env`, `.env.example`, logs ni commits.

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

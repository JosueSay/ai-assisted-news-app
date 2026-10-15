# Catálogos y seeders

Parte de la [documentación de base de datos](README.md).

Datos base reproducibles de AI Assisted News App: catálogo `locations` en MongoDB y
catálogo estático de topics versionado en código. La fuente ejecutable está en
`backend/news/seed_catalog.py`, `backend/news/topics.py` y `backend/news/seed_check.py`.

## Locations iniciales

El catálogo inicial contiene exactamente 16 países a nivel `country`:

| Código | País | Región |
| --- | --- | --- |
| CA | Canadá | América |
| MX | México | América |
| GT | Guatemala | América |
| CR | Costa Rica | América |
| AR | Argentina | América |
| BR | Brasil | América |
| CU | Cuba | América |
| JM | Jamaica | América |
| ES | España | Europa |
| FR | Francia | Europa |
| JP | Japón | Asia |
| CN | China | Asia |
| EG | Egipto | África |
| ZA | Sudáfrica | África |
| AU | Australia | Oceanía |
| NZ | Nueva Zelanda | Oceanía |

Cada documento cumple el modelo `Location`: `level` es `country`, `city` y `region`
son nulos, `active` es verdadero, no hay coordenadas GPS y no existe `isSimulated`
(la ubicación simulada del usuario es una referencia `simulatedLocationId`, no un
atributo del catálogo).

## Por qué son 16 países

Son los países fijados por el alcance del proyecto: cobertura inicial en América
(8), Europa (2), Asia (2), África (2) y Oceanía (2). No se agregan ciudades ni
regiones en este loop; el catálogo puede crecer en loops futuros sin cambiar su
mecánica.

## Identidad mediante countryCode

La identidad natural de cada entrada `country` es `countryCode` (ISO 3166-1
alpha-2), no el nombre traducido ni el `_id`. El seeder comprueba existentes con
`find_one({"countryCode": ...})`:

- si el código ya existe, la entrada queda intacta y cuenta como `unchanged`;
- si falta, se inserta con un `_id` determinista fijo por código.

Los `_id` deterministas solo aplican a inserciones nuevas: un documento previo con
el mismo `countryCode` pero distinto `_id` no se reescribe ni se duplica. No se
creó un índice único sobre `locations.countryCode`; esa decisión queda pendiente
de evaluar junto al esquema físico (Loop 03) y no se modifica silenciosamente.

## Catálogo de topics

`users.onboarding.selectedTopics`, `users.inferredInterests[].topic` y
`news.topics` son strings que comparten un único vocabulario controlado:

```text
actualidad, tecnologia, ciencia, economia, negocios, politica, deportes,
salud, educacion, cultura, entretenimiento, medio_ambiente, seguridad,
internacional
```

Los valores persistidos son minúsculas, sin espacios y estables. La API mínima en
`backend/news/topics.py` ofrece `get_topics()`, `is_valid_topic()` y
`normalize_topic()` (solo recorte de espacios y minúsculas, sin traducciones
automáticas ni plegado de acentos). No usa IA.

## Por qué topics no es colección

Crear una octava colección MongoDB para 14 strings estables agregaría lecturas,
índices y sincronización sin beneficio: el catálogo cambia con el código, no con
el uso. Por eso vive versionado en el repositorio y no existen colección,
validator ni índices `topics`. Los modelos mantienen sus campos como strings
libres (ver decisión pendiente abajo).

## Comportamiento idempotente

`make db-seed-catalogs` asegura el esquema existente y solo inserta entradas
faltantes por `countryCode`. La segunda ejecución resulta en `inserted: 0` y
`unchanged: 16`. Nunca elimina documentos, colecciones ni índices; nunca modifica
documentos existentes (ni del catálogo ni ajenos); nunca escribe en otras
colecciones.

`make db-seed-check` inspecciona de forma no destructiva (solo lectura) y reporta
`missing`, `duplicates` y `unexpected` por `countryCode`, sin eliminar nada. Un
dato ajeno previo se reporta como `unexpected` y no se borra.

## Comandos

```bash
make db-test            # suite offline, sin Atlas
make db-init            # asegura colecciones, validators e índices
make db-seed-catalogs   # inserta solo catálogos autorizados (idempotente)
make db-seed-catalogs   # segunda ejecución: inserted 0, unchanged 16
make db-seed-check      # inspección no destructiva del catálogo
```

`db-seed-catalog` (singular) se conserva como alias del comando plural.

## Seed vs reseed controlado

Seed inserta únicamente lo faltante y preserva todo lo existente. La reconstrucción
controlada del dataset (borrar y recrear solo las 16 locations y 32 news demo verificadas
por ownership) existe como `make db-reseed` con confirmación exacta y está documentada en
[automatización y reseed](11-automatizacion-y-reseed.md); requiere autorización humana
explícita según los guardarraíles del proyecto.

## Decisión pendiente

Convertir los strings libres de `selectedTopics`, `inferredInterests[].topic` y
`news.topics` en validación cerrada contra este catálogo sería un cambio
funcional significativo del contrato actual. El catálogo existe y los seeders lo
usan, pero los modelos no lo fuerzan todavía. Esa decisión queda para un loop
futuro con autorización explícita.

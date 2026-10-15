# Loop 04 — Catálogos y Seeders

## Objetivo

Implementar los datos base reproducibles que necesita AI Assisted News App.

Este loop implementa exclusivamente:

- catálogo `locations`;
- catálogo controlado de topics;
- seeders reproducibles;
- validación contra los modelos y validators existentes;
- inicialización segura de catálogos;
- tests;
- comandos Makefile;
- documentación y trazabilidad.

No generar todavía noticias demo.

---

## Skills

Aplicar:

### Principal

`.skills/test-driven-development/SKILL.md`

Implementar mediante:

red → green → refactor

### Complementaria

Usar `.skills/planning-with-files/SKILL.md` únicamente si el agente determina que la tarea necesita memoria multi-fase.

### Antes del commit

Aplicar:

`.skills/code-reviewer/SKILL.md`

No cargar otras skills salvo que aparezca su trigger real.

Si falla inesperadamente un test:

`.skills/systematic-debugging/SKILL.md`

No utilizar `security-compliance` salvo que aparezca un cambio relacionado con secretos o seguridad.

---

## Lecturas obligatorias

Leer:

- `AGENTS.md`
- handoffs 00–03;
- `docs/design/database/`;
- `backend/news/models/`;
- `backend/news/schema/`;
- `backend/news/README.md`;
- `Makefile`.

No reinterpretar el esquema aprobado.

---

# Catálogos

## 1. Locations

`locations` es una colección MongoDB existente y debe recibir datos reales controlados.

El catálogo inicial debe contener exactamente estos países:

### América

- Canadá
- México
- Guatemala
- Costa Rica
- Argentina
- Brasil
- Cuba
- Jamaica

### Europa

- España
- Francia

### Asia

- Japón
- China

### África

- Egipto
- Sudáfrica

### Oceanía

- Australia
- Nueva Zelanda

Total esperado:

16 países.

Para este catálogo inicial representar cada entrada a nivel:

country

No inventar ciudades o regiones durante este loop.

Cada documento debe cumplir el modelo `Location`.

Usar códigos ISO 3166-1 alpha-2 correctos:

CA
MX
GT
CR
AR
BR
CU
JM
ES
FR
JP
CN
EG
ZA
AU
NZ

`city` y `region` deben permanecer nulos cuando corresponda.

`active` debe ser true.

No agregar coordenadas GPS.

No agregar `isSimulated`.

---

# 2. Topics

El diseño utiliza:

- `users.onboarding.selectedTopics`;
- `users.inferredInterests[].topic`;
- `news.topics`.

Actualmente son strings.

Necesitamos una única fuente controlada para evitar:

tecnologia
Tecnología
technology
tech

como conceptos diferentes.

## Decisión

NO crear una octava colección MongoDB.

El catálogo de topics debe ser catálogo estático versionado en código/datos del repositorio.

Crear una definición simple y reutilizable.

Catálogo inicial:

- actualidad
- tecnologia
- ciencia
- economia
- negocios
- politica
- deportes
- salud
- educacion
- cultura
- entretenimiento
- medio_ambiente
- seguridad
- internacional

Los valores persistidos deben ser:

- minúsculas;
- sin espacios;
- estables;
- sin traducciones automáticas.

Puede existir un label separado para UI/documentación si resulta necesario, pero no agregar complejidad sin necesidad.

---

# 3. Organización de seeders

Crear una estructura explícita, por ejemplo:

backend/news/seeders/
├── __init__.py
├── locations.py
├── topics.py
└── seed.py

La estructura puede ajustarse si existe una convención mejor ya establecida.

Los datos deben estar separados de la lógica de persistencia cuando sea razonable.

---

# 4. Seeder de locations

El seeder debe:

1. usar el modelo `Location`;
2. producir exactamente 16 locations;
3. validar los documentos antes de persistir;
4. usar identificadores deterministas o una clave natural estable;
5. evitar duplicados;
6. poder ejecutarse repetidamente;
7. no eliminar locations existentes;
8. no modificar datos ajenos;
9. no tocar otras colecciones.

La segunda ejecución debe resultar conceptualmente en:

inserted: 0
unchanged: 16

No crear duplicados.

---

# 5. Identidad de catálogo

No depender de nombres traducidos para determinar unicidad.

Usar:

countryCode

como identidad natural de las entradas country del catálogo.

El seeder debe comprobar existentes mediante esa identidad.

No agregar todavía un índice unique nuevo sin evaluar primero si corresponde al esquema físico.

Si se determina necesario un índice unique sobre `locations.countryCode`, detener esa decisión y reportarla porque implicaría modificar Loop 03/schema.

No modificar silenciosamente los índices existentes.

---

# 6. Seeder de topics

Como topics NO es colección MongoDB:

- no insertar documentos `topics`;
- no crear colección `topics`;
- no crear índices.

Debe existir una API Python mínima para:

- obtener topics permitidos;
- comprobar si un topic es válido;
- normalizar únicamente cuando esté explícitamente definido.

No usar IA.

---

# 7. Integración con modelos

Evaluar si `selectedTopics`, `inferredInterests.topic` y `news.topics` deben validar contra el catálogo.

No cambiar silenciosamente el contrato existente.

Si puede integrarse sin romper el diseño aprobado y es coherente con los documentos actuales, implementar la validación mediante TDD.

Si convertir los topics libres actuales en enum/catálogo cerrado constituye un cambio funcional significativo, detener esa parte y documentar la decisión requerida.

El catálogo puede existir sin forzar todavía el modelo si existe esa duda.

---

# 8. Makefile

Mantener todos los comandos existentes.

Agregar:

make db-seed-catalogs

Debe:

- usar la infraestructura DB existente;
- asegurar que el schema exista;
- seedear únicamente catálogos autorizados;
- no borrar datos;
- no pedir confirmación porque es no destructivo;
- ser idempotente.

Agregar también, si aporta valor:

make db-seed-check

para inspeccionar de forma no destructiva el estado esperado del catálogo.

No implementar reseed todavía.

---

# 9. Local primero

Toda implementación y verificación debe realizarse primero contra Mongo local.

Orden esperado:

make db-test
make db-init
make db-seed-catalogs
make db-seed-catalogs
make db-seed-check

Verificar:

locations: 16
duplicates: 0
topics catalog: valid
schema: OK

No insertar noticias ni usuarios.

---

# 10. Atlas

Solo después de:

- tests offline exitosos;
- Mongo local exitoso;
- idempotencia local comprobada.

Puede ejecutarse el seeder contra Atlas mediante las interfaces existentes.

No leer directamente `keys/`.

Ejecutar el equivalente seguro a:

make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-seed-catalogs
make NEWS_DB_MODE=atlas COMPOSE_PROFILES= db-seed-check

y repetir `db-seed-catalogs` para verificar idempotencia.

Atlas debe terminar con exactamente las 16 entradas de catálogo esperadas para este seeder, salvo que existan datos previos ajenos; en ese caso no eliminarlos y reportar la diferencia.

---

# 11. Tests

Aplicar TDD.

Cubrir como mínimo:

## Locations data

- exactamente 16;
- códigos esperados;
- códigos sin duplicados;
- nombres no vacíos;
- level country;
- active true;
- city/region nulos;
- todos validan con `Location`.

## Topics

- catálogo esperado;
- valores únicos;
- formato estable;
- validación positiva;
- validación negativa.

## Seeder

- DB vacía → inserta 16;
- segunda ejecución → inserta 0;
- entradas existentes → no duplica;
- no elimina datos;
- no toca otras colecciones;
- documento inválido no se persiste.

## Check

- catálogo correcto → OK;
- location faltante → drift;
- duplicado → drift;
- dato inesperado → reportado sin eliminarlo.

No requerir Atlas para la suite normal.

---

# 12. Documentación

Actualizar cuando corresponda:

- `backend/news/README.md`;
- `docs/design/database/README.md`;
- `docs/design/database/07-diagrama.md`.

Crear:

`docs/design/database/09-catalogos-y-seeders.md`

Debe documentar:

- locations iniciales;
- por qué son 16 países;
- identidad mediante countryCode;
- catálogo de topics;
- por qué topics no es colección;
- comportamiento idempotente;
- comandos;
- diferencia entre seed y futuro reseed.

---

# 13. Trazabilidad

Antes de cerrar verificar:

[ ] modelos revisados
[ ] schema revisado
[ ] catálogos sincronizados
[ ] seeders sincronizados
[ ] documentación sincronizada
[ ] diagrama revisado
[ ] tests sincronizados
[ ] Makefile sincronizado
[ ] secrets/bootstrap revisados

No modificar elementos que no requieran cambios.

---

# 14. Seguridad

No:

- leer `keys/`;
- imprimir secretos;
- insertar users;
- insertar userInteractions;
- insertar chatSessions;
- insertar aiUsage;
- insertar auditLogs;
- insertar news;
- eliminar documentos;
- eliminar colecciones;
- hacer drop database;
- implementar reseed.

---

# 15. Review

Antes del commit utilizar `code-reviewer`.

Revisar especialmente:

- idempotencia;
- duplicados;
- operaciones Mongo;
- posibilidad de borrar datos accidentalmente;
- coherencia modelos/schema/docs;
- tests.

Corregir problemas encontrados antes del commit.

---

# Commit

Si todo está completo:

feat: add database catalog seeders

No hacer push.

---

# Handoff

Crear:

backend/loops/handoffs/04-catalog-seeders-result.md

Debe incluir:

1. Resultado.
2. Skills utilizadas.
3. Locations implementadas.
4. Topics implementados.
5. Estrategia de identidad/idempotencia.
6. Tests.
7. Resultado local.
8. Resultado Atlas.
9. Segunda ejecución/idempotencia.
10. Makefile.
11. Documentación.
12. Trazabilidad.
13. Seguridad.
14. Archivos modificados.
15. Review findings.
16. Decisiones.
17. Blockers.
18. Git.
19. Información para Loop 05.

---

# Definition of Done

Loop 04 termina cuando:

- existen 16 locations reales;
- todos los códigos son correctos y únicos;
- existe catálogo versionado de topics;
- no existe colección MongoDB topics;
- seeder locations es idempotente;
- existe check no destructivo;
- tests pasan;
- no hay regresiones;
- local fue probado;
- Atlas fue probado si el entorno lo permite;
- segunda ejecución no duplica;
- Makefile está sincronizado;
- documentación está sincronizada;
- code-reviewer fue aplicado;
- ningún secreto fue expuesto;
- ningún dato ajeno fue eliminado;
- existe handoff;
- existe commit.

---

# Stop Conditions

Detener y solicitar decisión humana si:

- se necesita una octava colección;
- se necesita modificar schema/índices de Loop 03;
- cerrar topics rompe el contrato actual de forma significativa;
- existen datos Atlas incompatibles que requerirían eliminación;
- se requiere reseed destructivo;
- se requiere leer keys/;
- se necesita modificar backend/assistant/.

No resolver silenciosamente.

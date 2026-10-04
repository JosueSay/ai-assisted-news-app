# Loop 00 — Backend Discovery

## Objetivo

Explorar el estado actual del backend antes de realizar cualquier implementación relacionada con MongoDB.

Este loop es únicamente de descubrimiento.

**No implementar código.  
No modificar archivos existentes.  
No crear modelos.  
No crear seeders.  
No conectarse a MongoDB.  
No realizar commits.**

El resultado debe ser un handoff que permita diseñar los siguientes loops con conocimiento real del repositorio.

---

## Contexto

El diseño aprobado de base de datos se encuentra en:

```text
docs/design/database/
```

Estos documentos son la fuente principal para entender el diseño actual.

Leer todos los archivos dentro de esa carpeta antes de analizar cómo implementar la solución.

El archivo:

```text
docs/design/99-checklist-replicacion.md
```

NO debe considerarse una especificación autoritativa.

Puede ignorarse para este loop.

---

## Restricciones

### Credenciales

No leer, inspeccionar, imprimir ni modificar ningún archivo dentro de:

```text
keys/
```

Si la carpeta existe, únicamente comprobar su existencia.

No intentar descubrir valores de credenciales desde otros archivos.

Si posteriormente se necesitan credenciales, simplemente documentar cuáles serían necesarias.

### Variables de entorno

Durante este loop únicamente identificar cómo utiliza actualmente el proyecto:

- `.env`
- `.env.example`
- variables de entorno
- archivos de configuración
- secretos

No modificar este comportamiento todavía.

### Base de datos

No realizar conexiones a MongoDB Atlas ni a ninguna otra base de datos.

No ejecutar migraciones, seeds, scripts destructivos ni comandos relacionados con datos.

### Código

No modificar código.

No instalar dependencias.

No reformatear archivos.

No crear infraestructura.

---

## Fase 1 — Leer el diseño

Leer:

```text
docs/design/database/README.md
docs/design/database/01-colecciones.md
docs/design/database/02-criterios-de-contenido.md
docs/design/database/03-criterios-de-personalizacion.md
docs/design/database/04-criterios-de-chat-y-costos.md
docs/design/database/05-tiempo-de-lectura.md
docs/design/database/06-decisiones-descartadas.md
```

Extraer:

- colecciones propuestas;
- relaciones/referencias;
- catálogos;
- campos principales;
- criterios de personalización;
- criterios de contenido;
- comportamiento esperado del chat;
- estrategia de costos;
- cálculo de tiempo de lectura;
- decisiones explícitamente descartadas.

No reinterpretar ni rediseñar todavía.

---

## Fase 2 — Explorar el backend

Inspeccionar completamente:

```text
backend/
```

Determinar como mínimo:

### Runtime

- versión de Python;
- framework utilizado;
- servidor utilizado;
- gestor de paquetes;
- forma actual de ejecutar el backend.

### Dependencias

Identificar archivos como:

```text
pyproject.toml
requirements.txt
requirements-dev.txt
uv.lock
poetry.lock
Pipfile
```

Determinar qué sistema utiliza realmente el proyecto.

### Arquitectura

Identificar:

- entrypoint;
- módulos;
- routers/controllers;
- services;
- repositories;
- models;
- schemas;
- configuración;
- tests;
- scripts;
- utilidades.

No asumir que alguna arquitectura existe: reportar únicamente lo encontrado.

---

## Fase 3 — Persistencia actual

Determinar si actualmente existe:

- MongoDB;
- PyMongo;
- Motor;
- Beanie;
- MongoEngine;
- ODM propio;
- otra base de datos;
- otra estrategia de persistencia.

Buscar también cualquier modelo existente.

No proponer todavía reemplazar tecnologías.

---

## Fase 4 — Configuración y secretos

Inspeccionar:

```text
.gitignore
.env.example
Makefile
README*
docker-compose*
Dockerfile*
```

y cualquier archivo equivalente encontrado.

Determinar:

- cómo se parametriza actualmente el backend;
- qué variables existen;
- cómo se espera proporcionar secretos;
- si `keys/` está ignorado por Git;
- si existe alguna convención equivalente.

Recordatorio:

**NO abrir archivos dentro de `keys/`.**

---

## Fase 5 — Automatización existente

Determinar si existen mecanismos como:

- Makefile;
- Taskfile;
- scripts shell;
- scripts Python;
- Docker Compose;
- comandos del package manager;
- CI/CD.

Registrar los comandos existentes relacionados con:

- instalación;
- ejecución;
- tests;
- lint;
- format;
- desarrollo local.

No ejecutar comandos destructivos.

---

## Fase 6 — Testing

Determinar:

- framework de testing;
- estructura de tests;
- fixtures existentes;
- estrategia de integración;
- configuración de coverage;
- existencia de tests de infraestructura o DB.

Ejecutar tests existentes **solo si pueden ejecutarse sin credenciales ni servicios externos**.

Si requieren secretos, MongoDB Atlas u otros servicios, no ejecutarlos y documentar el bloqueo.

---

## Fase 7 — Git

Inspeccionar:

```bash
git status
git branch --show-current
git log --oneline -10
```

Registrar:

- branch actual;
- estado del working tree;
- estilo observable de commits.

No modificar Git.

No crear commits.

No hacer checkout.

No hacer push.

---

## Entregable

Crear únicamente:

```text
backend/loops/handoffs/00-discovery-result.md
```

Si `backend/loops/handoffs/` no existe, puede crearse.

El documento debe utilizar esta estructura:

# Backend Discovery Result

## 1. Executive Summary

Resumen breve del estado actual.

## 2. Backend Stack

Tabla:

| Área | Encontrado |
| --- | --- |
| Python | |
| Framework | |
| Package manager | |
| Server | |
| Testing | |
| Database | |
| Mongo library / ODM | |
| Automation | |

## 3. Relevant Repository Structure

Mostrar únicamente el árbol relevante para backend, configuración, tests y diseño DB.

No incluir directorios irrelevantes como caches o dependencias generadas.

## 4. Current Backend Architecture

Explicar cómo está organizado actualmente el backend.

## 5. Database Design Found

Resumir fielmente lo definido en:

```text
docs/design/database/
```

No proponer cambios aquí.

## 6. Existing Persistence

Documentar cualquier infraestructura de persistencia existente.

## 7. Configuration and Secrets

Documentar cómo funciona actualmente la configuración.

Indicar explícitamente:

```text
keys/ inspected: NO
```

Indicar si `keys/` existe y si está protegido por `.gitignore`.

## 8. Existing Automation

Documentar Makefile/scripts/comandos encontrados.

## 9. Testing

Documentar tests existentes y cuáles pudieron ejecutarse.

Incluir los comandos ejecutados y su resultado.

## 10. Git State

Documentar branch, working tree y convenciones observadas.

## 11. Missing Pieces

Enumerar únicamente componentes necesarios para implementar el diseño que actualmente no existan.

No implementarlos.

## 12. Risks / Conflicts

Documentar posibles conflictos entre:

- arquitectura actual;
- diseño de `docs/design/database/`;
- estrategia propuesta de MongoDB;
- configuración existente.

No resolverlos silenciosamente.

## 13. Decisions Required Before Implementation

Enumerar decisiones que necesiten confirmación humana antes de implementar.

No tomar decisiones arquitectónicas importantes por cuenta propia.

## 14. Proposed Engineering Loops

Proponer los siguientes loops pequeños y verificables.

Para cada uno indicar:

```text
Loop:
Objective:
Inputs:
Expected changes:
Verification:
Dependencies:
Requires credentials: yes/no
Destructive operations: yes/no
Suggested commit:
```

Los loops deben ser incrementales.

No agrupar toda la implementación de MongoDB en un único loop.

---

## Definition of Done

Este loop termina únicamente cuando:

- todos los documentos de `docs/design/database/` fueron revisados;
- el backend fue explorado;
- stack y dependencias fueron identificados;
- configuración existente fue identificada;
- estrategia actual de secretos fue identificada sin leer `keys/`;
- testing existente fue identificado;
- estado de Git fue documentado;
- no se modificó código de aplicación;
- no se realizaron conexiones a DB;
- no se realizaron operaciones destructivas;
- existe `backend/loops/handoffs/00-discovery-result.md`;
- el handoff contiene suficiente información para diseñar el siguiente loop sin volver a asumir la arquitectura del backend.

## Stop Conditions

Detener el loop y documentar el bloqueo si:

- una acción requiere credenciales;
- una acción requiere acceder a `keys/`;
- se necesita modificar código para continuar;
- se requiere conectarse a infraestructura externa;
- existe una contradicción importante que requiere decisión humana.

No resolver estos bloqueos automáticamente.

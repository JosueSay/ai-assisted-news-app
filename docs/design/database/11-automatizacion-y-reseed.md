# Automatización y reseed

Parte de la [documentación de base de datos](README.md).

Flujo operativo reproducible de AI Assisted News App: preparar secretos,
inicializar schema, sembrar catálogos y noticias demo, verificarlo todo y
reconstruir de forma controlada el dataset administrado por seeders. La
fuente ejecutable está en `backend/news/reseed.py` (núcleo + CLI
destructivo), `backend/news/reseed_dry_run.py` (CLI de dry-run),
`backend/news/bootstrap.py`, `backend/news/verify.py` y el `Makefile`.

## Bootstrap

`make db-bootstrap` ejecuta conceptualmente:

```text
db-init
db-seed-catalogs
db-seed-news
db-schema-check
db-seed-check
db-news-check
```

Es idempotente (segunda ejecución: `inserted 0`, sin duplicados) y no
destructivo: nunca elimina documentos, colecciones ni índices, por eso no
pide confirmación. Sirve para: clonar repo → configurar keys/env →
levantar DB → obtener estructura + dataset demo.

Flujo recomendado para alguien nuevo (local, sin Atlas):

```bash
make setup-keys

# humano completa archivos requeridos

make db-check-config
make db-bootstrap
```

En local funciona sin Atlas (`NEWS_DB_MODE=local`); en Atlas
(`NEWS_DB_MODE=atlas`) usa la URI de `keys/mongodb_uri` sin levantar
`news-mongo`. Ver `backend/news/README.md`.

## Verify

`make db-verify` es no destructivo (solo lectura: no inserta, modifica,
elimina ni reseed). Verifica exactamente:

- schema: colecciones, validators, índices y TTL;
- catálogos: 16 locations sin faltantes/duplicados/ajenos;
- demo news: 32 noticias con cobertura, topics, estados y coherencia.

Resultado conceptual:

```text
Database verification: OK
Schema: OK
Catalogs: OK
Demo news: OK
```

Sale con código no cero si algo derivó. Los checks estrictos reportan
documentos ajenos como drift: eso es informativo, no una orden de borrar.

## Ownership del dataset

Antes de eliminar, el sistema demuestra que cada documento pertenece al
dataset controlado mediante identidades versionadas:

- locations: `countryCode` esperado + `_id` determinista esperado
  (`CATALOG_LOCATION_IDS`);
- news demo: `slug` esperado + `_id` determinista esperado
  (documentos de `demo_news.py`).

Nunca se clasifica por `level`, `status`, `topic`, fecha ni prefijos
genéricos. Un documento externo (código/slug fuera del dataset) se cuenta
como preservado, nunca como eliminable.

## Dry-run

`make db-reseed-dry-run` es completamente no destructivo y muestra conteos
provenientes de inspección real (no impresos sin comprobar):

```text
Database: ai_assisted_news
Mode: local | atlas

Controlled data:
- locations to delete: 16
- demo news to delete: 32

Preserved:
- users
- userInteractions
- chatSessions
- aiUsage
- auditLogs
- external locations
- external news

No changes performed.
```

Además informa externos preservados y avisos de drift (que harían abortar
el reseed real). No muestra secretos.

## Confirmación

`make db-reseed` requiere frase exacta vía variable `CONFIRM`:

```bash
make db-reseed CONFIRM="RESEED ai_assisted_news"              # local
make db-reseed NEWS_DB_MODE=atlas COMPOSE_PROFILES= CONFIRM="RESEED ATLAS ai_assisted_news"  # Atlas
```

Local y Atlas exigen frases diferentes; una confirmación local jamás
autoriza Atlas. Sin coincidencia exacta (vacío, Enter, `y`, `yes`, base
incorrecta): aborta con código no cero y cero modificaciones. No existe
`--force` ni bypass. Los tests ejercen la lógica destructiva con
mocks/fakes sin confirmación interactiva real; la interfaz programática
(`execute_reseed`) está separada del CLI humano.

## Orden

Autorizado el reseed:

1. validar target (modo y base conocidos);
2. validar schema;
3. validar ownership (sin drift);
4. eliminar únicamente las 32 noticias demo controladas;
5. eliminar únicamente las 16 locations controladas;
6. seed de locations;
7. seed de news;
8. catalog check;
9. news check;
10. schema check.

Si falla una verificación previa, no se borra nada. Se elimina primero
`news` y después `locations`; se reconstruye primero `locations` y
después `news`, respetando la relación conceptual
`news.geographicScope.locationIds[] -> locations._id` (MongoDB no impone
FK). La lógica interna devuelve
`deleted_locations`, `deleted_news`, `inserted_locations`,
`inserted_news` y `preserved_external` como datos estructurados.

## Preservación de externos y otras colecciones

El reseed solo toca datos controlados. Permanecen intactos: `users`,
`userInteractions`, `chatSessions`, `aiUsage`, `auditLogs`, locations
externas y noticias externas. Hay tests explícitos con documentos ajenos
en las siete colecciones.

## Local vs Atlas

- Local: tras tests offline y dry-run correcto, el agente estuvo
  autorizado a probar el reseed destructivo (target inequívocamente
  local), verificando después 16 locations, 32 news y checks OK, más
  idempotencia en segunda ejecución.
- Atlas: el agente solo ejecuta dry-run y checks no destructivos. El
  reseed real en Atlas requiere ejecución manual del desarrollador con la
  frase `RESEED ATLAS ai_assisted_news` (ver handoff del loop).

## Failure modes y recuperación

- Fallo antes de delete (confirmación, target, schema, ownership):
  cero modificaciones.
- Fallo después de delete y antes de completar el seed: se reporta estado
  incompleto con conteos parciales; no se afirma rollback porque MongoDB
  no lo realizó; `db-bootstrap`/seeders idempotentes permiten recuperar.
- Fallo de checks posteriores: se reporta que el reseed terminó pero la
  verificación falló, sin ocultarlo.
- No se asume atomicidad multi-colección ni se usan transacciones
  multi-documento: el flujo ocurre en pasos honestos.

## Por qué no existe drop/reset

Este loop autoriza únicamente reseed de datos controlados. No se crean
`db-reset`, `db-drop`, `db-drop-database` ni `db-clean-all`: un borrado
total o por filtros amplios podría eliminar datos de usuarios, chats,
consumo de IA o auditoría sin forma de recuperarlos. Los deletes usan
exclusivamente `delete_many({"_id": {"$in": [...]}})` con identidades
versionadas.

## Comandos

```bash
make db-test            # suite offline, sin Atlas (249 tests)
make db-bootstrap       # init + seeds + checks, idempotente, sin confirmación
make db-verify          # solo lectura: schema + catálogos + demo news
make db-reseed-dry-run  # plan real sin escribir
make db-reseed CONFIRM="..."  # destructivo controlado, requiere frase exacta
```

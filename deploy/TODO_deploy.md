# TODO deploy

Deploy de `news-api` y del chatbot en Google Cloud Run. Los scripts están listos y probados en local
con Docker. Todavía no se desplegó nada.

## Qué falta

- [ ] Crear el proyecto en Google Cloud y vincular la facturación.
- [ ] Instalar `gcloud` e iniciar sesión (`gcloud auth login`).
- [ ] Completar `deploy/gcp/config.sh`: `PROJECT_ID`, `REGION` (la misma región del clúster de
      Atlas) y los precios `NEWS_CHAT_INPUT_USD_PER_MILLION` y `NEWS_CHAT_OUTPUT_USD_PER_MILLION`.
- [ ] Correr `make gcp-bootstrap`.
- [ ] Agregar en Atlas, Network Access, la IP que imprime el bootstrap.
- [ ] Correr `make gcp-secrets`.
- [ ] Hacer el primer deploy: `ALLOW_PUBLIC=1 make gcp-deploy`.
- [ ] Copiar `WIF_PROVIDER` y `DEPLOYER_SA` (los imprime el bootstrap) en
      `.github/workflows/deploy.yml`.
- [ ] Probar en celulares con las URLs que imprime el deploy (ver abajo).
- [ ] Cuando exista Firebase Auth, proteger el chat. Hoy cualquiera con la URL puede gastar el
      presupuesto de IA (USD 20).

## Cómo funciona

```text
push a main -> GitHub Actions -> pytest -> deploy.sh -> Cloud Run
                                                          |
                         news-api (:8020) y news-chatbot (:8010)
                                                          |
                         Cloud NAT con IP fija -> MongoDB Atlas y OpenAI
```

- Dos servicios en Cloud Run: `news-api` y `news-chatbot`. Escalan a cero cuando nadie los usa,
  con un máximo de 2 instancias.
- Los secretos están en Secret Manager y Cloud Run los monta como archivos en `/secrets/...`. El
  código los lee igual que lee `keys/` en local.
- La salida a internet usa una IP fija (Cloud NAT). Atlas solo acepta esa IP.
- GitHub Actions entra a Google Cloud con Workload Identity Federation, sin llaves JSON, y solo
  desde la rama `main` de este repo.

## Archivos

| Archivo | Qué hace |
|---|---|
| `gcp/config.sh` | Parámetros sin secretos. Es lo único que hay que editar. |
| `gcp/bootstrap.sh` | Crea la infraestructura una sola vez. Se puede repetir sin romper nada. |
| `gcp/load-secrets.sh` | Sube `keys/mongodb_uri`, `keys/news_admin_password` y `keys/openai_api_key` a Secret Manager. |
| `gcp/deploy.sh` | Construye las imágenes, las sube y despliega los dos servicios. |
| `../.github/workflows/deploy.yml` | Corre pytest en cada PR y despliega en cada merge a `main`. |
| `../docs/deploy/README.md` | Guía completa con diagrama. |

## Cómo usarlo

| Necesito | Comando |
|---|---|
| Preparar Google Cloud (una vez) | `make gcp-bootstrap` |
| Subir o cambiar secretos | editar `keys/...` y correr `make gcp-secrets` |
| Desplegar a mano | `make gcp-deploy` |
| Desplegar automático | merge a `main` |

Para probar en celulares, poner las URLs en `frontend/.env`:

```dotenv
EXPO_PUBLIC_NEWS_API_BASE_URL=https://news-api-xxxx.run.app
EXPO_PUBLIC_ASSISTANT_API_BASE_URL=https://news-chatbot-xxxx.run.app
```

Después correr `cd frontend && npx expo start --tunnel` y escanear el QR con Expo Go.

## Notas

- Sin `make`, se pueden correr los scripts directo: `bash deploy/gcp/deploy.sh`.
- Para usar el chat sin costo de IA: `CHATBOT_PROVIDER=stub make gcp-deploy`.
- Cloud NAT y la IP fija tienen un costo mensual pequeño. Revisarlo antes de activar la facturación.

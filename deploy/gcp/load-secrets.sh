#!/usr/bin/env bash
# Sube los archivos de keys/ como nueva versión en Secret Manager.
# El valor viaja directo del archivo a gcloud: no se imprime ni se guarda en el historial.
set -euo pipefail

cd "$(dirname "$0")/../.."
source deploy/gcp/config.sh
require_project

upload() {
  local secret="$1" file="$2" required="$3"
  if [[ ! -s "$file" ]]; then
    if [[ "$required" == "required" ]]; then
      echo "$file  FALTA o está vacío (requerido)" >&2
      return 1
    fi
    echo "$file  vacío, se omite"
    return 0
  fi
  gcloud secrets versions add "$secret" --project "$PROJECT_ID" --data-file "$file" >/dev/null
  echo "$file  -> $secret  OK"
}

openai_required="optional"
[[ "$CHATBOT_PROVIDER" == "openai" ]] && openai_required="required"

upload "$SECRET_MONGODB_URI" keys/mongodb_uri required
upload "$SECRET_ADMIN_PASSWORD" keys/news_admin_password required
upload "$SECRET_OPENAI_API_KEY" keys/openai_api_key "$openai_required"

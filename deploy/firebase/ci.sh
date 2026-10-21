#!/usr/bin/env bash
# Usa las URLs del backend recién desplegado y la configuración pública de GitHub.
# La autenticación se recibe por ADC/WIF; no lee keys/ ni crea tokens permanentes.
set -euo pipefail
cd "$(dirname "$0")/../.."
source deploy/gcp/config.sh
require_project

news_url="$(gcloud run services describe "$NEWS_API_SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
chat_url="$(gcloud run services describe "$CHATBOT_SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
if [[ -z "$news_url" || -z "$chat_url" ]]; then
  echo "No se pudieron resolver las URLs de los dos servicios Cloud Run." >&2
  exit 1
fi
export EXPO_PUBLIC_NEWS_API_BASE_URL="$news_url"
export EXPO_PUBLIC_ASSISTANT_API_BASE_URL="$chat_url"
export PROJECT_ID NEWS_FIREBASE_PROJECT_ID
export EXPO_NO_DOTENV=1
bash deploy/firebase/hosting.sh

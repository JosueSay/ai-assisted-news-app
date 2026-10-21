#!/usr/bin/env bash
# Validación local del job de producción, antes de cualquier cambio cloud.
set -euo pipefail
for name in WIF_PROVIDER DEPLOYER_SA PROJECT_ID REGION \
  EXPO_PUBLIC_FIREBASE_API_KEY EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN \
  EXPO_PUBLIC_FIREBASE_PROJECT_ID EXPO_PUBLIC_FIREBASE_APP_ID; do
  if [[ -z "${!name:-}" || "${!name}" == CAMBIAR* ]]; then
    echo "::error::Falta la variable de producción ${name}; consulta docs/deploy/pipeline-paso-a-paso.md." >&2
    exit 1
  fi
done
if [[ "$EXPO_PUBLIC_FIREBASE_PROJECT_ID" != "${NEWS_FIREBASE_PROJECT_ID:-$PROJECT_ID}" ]]; then
  echo "::error::El proyecto público de Firebase debe coincidir con el configurado para Auth y Hosting." >&2
  exit 1
fi
if [[ "${CHATBOT_PROVIDER:-openai}" == openai ]]; then
  for name in NEWS_CHAT_INPUT_USD_PER_MILLION NEWS_CHAT_OUTPUT_USD_PER_MILLION; do
    if [[ ! "${!name:-}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
      echo "::error::Define ${name} con el precio del modelo en USD por millón de tokens." >&2
      exit 1
    fi
  done
fi
echo "Configuración del pipeline: OK."

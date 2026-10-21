#!/usr/bin/env bash
# Construye las imágenes, las sube a Artifact Registry y despliega news-api y el chatbot
# en Cloud Run. Lo usa el primer deploy manual y el workflow de GitHub Actions.
#
# ALLOW_PUBLIC=1 abre el acceso público a los dos servicios. Solo hace falta la primera
# vez y requiere permisos de dueño del proyecto; el pipeline no cambia permisos IAM.
set -euo pipefail

cd "$(dirname "$0")/../.."
source deploy/gcp/config.sh
require_project

if [[ "$CHATBOT_PROVIDER" == "openai" ]] \
  && [[ -z "$NEWS_CHAT_INPUT_USD_PER_MILLION" || -z "$NEWS_CHAT_OUTPUT_USD_PER_MILLION" ]]; then
  echo "Con CHATBOT_PROVIDER=openai define NEWS_CHAT_INPUT_USD_PER_MILLION y NEWS_CHAT_OUTPUT_USD_PER_MILLION." >&2
  exit 1
fi

TAG="${TAG:-$(git rev-parse --short HEAD)}"
NEWS_API_IMAGE="${REGISTRY}/news-api:${TAG}"
CHATBOT_IMAGE="${REGISTRY}/news-chatbot:${TAG}"

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> Build ${TAG}"
docker build -f backend/news/Dockerfile -t "$NEWS_API_IMAGE" .
docker build -f backend/assistant/Dockerfile --target runtime -t "$CHATBOT_IMAGE" backend
docker push "$NEWS_API_IMAGE"
docker push "$CHATBOT_IMAGE"

# Opciones comunes: salida por la VPC con IP fija y sin instancias mínimas.
common=(
  --project "$PROJECT_ID"
  --region "$REGION"
  --network "$VPC_NETWORK"
  --subnet "$VPC_SUBNET"
  --vpc-egress all-traffic
  --min-instances 0
  --max-instances "$MAX_INSTANCES"
  --cpu 1
  --memory 512Mi
  --timeout 60
)

echo "==> Deploy ${NEWS_API_SERVICE}"
gcloud run deploy "$NEWS_API_SERVICE" "${common[@]}" \
  --image "$NEWS_API_IMAGE" \
  --service-account "$(sa_email "$NEWS_API_SA")" \
  --port 8020 \
  --concurrency 40 \
  --set-secrets "/secrets/mongodb/uri=${SECRET_MONGODB_URI}:latest,/secrets/admin/password=${SECRET_ADMIN_PASSWORD}:latest" \
  --set-env-vars "NEWS_DB_MODE=atlas,NEWS_MONGODB_DATABASE=${NEWS_MONGODB_DATABASE},NEWS_MONGODB_REQUIRED=true,NEWS_MONGODB_URI_FILE=/secrets/mongodb/uri,NEWS_ADMIN_PASSWORD_FILE=/secrets/admin/password"

chatbot_secrets="/secrets/mongodb/uri=${SECRET_MONGODB_URI}:latest"
if [[ "$CHATBOT_PROVIDER" == "openai" ]]; then
  chatbot_secrets+=",/secrets/openai/key=${SECRET_OPENAI_API_KEY}:latest"
fi

echo "==> Deploy ${CHATBOT_SERVICE}"
gcloud run deploy "$CHATBOT_SERVICE" "${common[@]}" \
  --image "$CHATBOT_IMAGE" \
  --service-account "$(sa_email "$CHATBOT_SA")" \
  --port 8010 \
  --concurrency 20 \
  --set-secrets "$chatbot_secrets" \
  --set-env-vars "MONGODB_CONTEXT_MODE=news,MONGODB_REQUIRED=true,NEWS_DB_MODE=atlas,NEWS_MONGODB_DATABASE=${NEWS_MONGODB_DATABASE},NEWS_MONGODB_URI_FILE=/secrets/mongodb/uri,OPENAI_API_KEY_FILE=/secrets/openai/key,CHATBOT_PROVIDER=${CHATBOT_PROVIDER},OPENAI_MODEL=${OPENAI_MODEL},NEWS_CHAT_INPUT_USD_PER_MILLION=${NEWS_CHAT_INPUT_USD_PER_MILLION},NEWS_CHAT_OUTPUT_USD_PER_MILLION=${NEWS_CHAT_OUTPUT_USD_PER_MILLION},NEWS_AI_BUDGET_USD=${NEWS_AI_BUDGET_USD},CHAT_SESSION_TTL_SECONDS=3600,CHATBOT_PROMPT_FILE=prompts/news.md"

if [[ "${ALLOW_PUBLIC:-0}" == "1" ]]; then
  for service in "$NEWS_API_SERVICE" "$CHATBOT_SERVICE"; do
    gcloud run services add-iam-policy-binding "$service" \
      --project "$PROJECT_ID" --region "$REGION" \
      --member allUsers --role roles/run.invoker >/dev/null
  done
fi

NEWS_API_URL="$(gcloud run services describe "$NEWS_API_SERVICE" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
CHATBOT_URL="$(gcloud run services describe "$CHATBOT_SERVICE" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
cat <<EOF

URLs para el .env del frontend:
EXPO_PUBLIC_NEWS_API_BASE_URL=${NEWS_API_URL}
EXPO_PUBLIC_ASSISTANT_API_BASE_URL=${CHATBOT_URL}
EOF

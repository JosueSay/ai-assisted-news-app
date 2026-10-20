# shellcheck shell=bash disable=SC2034
# Parámetros no secretos del deploy en Google Cloud.
# Lo usan bootstrap.sh, deploy.sh, load-secrets.sh y el workflow de GitHub Actions.
# Cualquier valor se puede sobrescribir con una variable de entorno del mismo nombre.

PROJECT_ID="${PROJECT_ID:-CAMBIAR-project-id}"
# Conviene la región más cercana al clúster de Atlas.
REGION="${REGION:-us-central1}"

AR_REPO="${AR_REPO:-ai-news}"
NEWS_API_SERVICE="${NEWS_API_SERVICE:-news-api}"
CHATBOT_SERVICE="${CHATBOT_SERVICE:-news-chatbot}"

# Salida a internet con IP fija para la lista de acceso de Atlas.
VPC_NETWORK="${VPC_NETWORK:-ai-news-vpc}"
VPC_SUBNET="${VPC_SUBNET:-ai-news-run}"
VPC_SUBNET_RANGE="${VPC_SUBNET_RANGE:-10.10.0.0/26}"
ROUTER="${ROUTER:-ai-news-router}"
NAT="${NAT:-ai-news-nat}"
NAT_IP_NAME="${NAT_IP_NAME:-ai-news-egress}"

# Cuentas de servicio: una por servicio y otra para el pipeline.
NEWS_API_SA="${NEWS_API_SA:-news-api-run}"
CHATBOT_SA="${CHATBOT_SA:-news-chatbot-run}"
DEPLOYER_SA="${DEPLOYER_SA:-gh-deployer}"

# Secret Manager. El valor se carga con load-secrets.sh desde keys/.
SECRET_MONGODB_URI="${SECRET_MONGODB_URI:-news-mongodb-uri}"
SECRET_ADMIN_PASSWORD="${SECRET_ADMIN_PASSWORD:-news-admin-password}"
SECRET_OPENAI_API_KEY="${SECRET_OPENAI_API_KEY:-openai-api-key}"

# GitHub Actions con Workload Identity Federation (sin llaves JSON).
GITHUB_REPO="${GITHUB_REPO:-JosueSay/ai-assisted-news-app}"
WIF_POOL="${WIF_POOL:-github}"
WIF_PROVIDER="${WIF_PROVIDER:-ai-news-repo}"

# Aplicación.
NEWS_MONGODB_DATABASE="${NEWS_MONGODB_DATABASE:-ai_assisted_news}"
CHATBOT_PROVIDER="${CHATBOT_PROVIDER:-openai}"
OPENAI_MODEL="${OPENAI_MODEL:-gpt-5-mini}"
# Precios del modelo en USD por millón de tokens. Obligatorios con openai.
NEWS_CHAT_INPUT_USD_PER_MILLION="${NEWS_CHAT_INPUT_USD_PER_MILLION:-}"
NEWS_CHAT_OUTPUT_USD_PER_MILLION="${NEWS_CHAT_OUTPUT_USD_PER_MILLION:-}"
NEWS_AI_BUDGET_USD="${NEWS_AI_BUDGET_USD:-20}"
# Límite de instancias: acota costo de Cloud Run y de IA mientras no exista auth.
MAX_INSTANCES="${MAX_INSTANCES:-2}"

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"

require_project() {
  if [[ "$PROJECT_ID" == CAMBIAR* ]]; then
    echo "Define PROJECT_ID en deploy/gcp/config.sh o como variable de entorno." >&2
    exit 1
  fi
}

sa_email() {
  echo "$1@${PROJECT_ID}.iam.gserviceaccount.com"
}

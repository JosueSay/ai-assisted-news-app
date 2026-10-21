#!/usr/bin/env bash
# Prepara la infraestructura del proyecto en Google Cloud. Idempotente: si un recurso
# ya existe lo deja como está. No borra nada y no lee ni escribe valores secretos.
set -euo pipefail

cd "$(dirname "$0")/../.."
source deploy/gcp/config.sh
require_project

gcloud config set project "$PROJECT_ID" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

step() { echo; echo "==> $*"; }
exists() { "$@" >/dev/null 2>&1; }

step "APIs"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  cloudresourcemanager.googleapis.com

step "Artifact Registry: $AR_REPO"
exists gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" \
  || gcloud artifacts repositories create "$AR_REPO" \
       --location "$REGION" --repository-format docker \
       --description "Imágenes de AI Assisted News"

step "Cuentas de servicio"
for sa in "$NEWS_API_SA" "$CHATBOT_SA" "$DEPLOYER_SA"; do
  exists gcloud iam service-accounts describe "$(sa_email "$sa")" \
    || gcloud iam service-accounts create "$sa" --display-name "$sa"
done

step "Secretos (solo el contenedor, sin valor)"
for secret in "$SECRET_MONGODB_URI" "$SECRET_OPENAI_API_KEY"; do
  exists gcloud secrets describe "$secret" \
    || gcloud secrets create "$secret" --replication-policy automatic
done

grant_secret() {
  gcloud secrets add-iam-policy-binding "$1" \
    --member "serviceAccount:$(sa_email "$2")" \
    --role roles/secretmanager.secretAccessor --condition None >/dev/null
}
# Cada servicio lee solo los secretos que necesita.
grant_secret "$SECRET_MONGODB_URI" "$NEWS_API_SA"
grant_secret "$SECRET_MONGODB_URI" "$CHATBOT_SA"
grant_secret "$SECRET_OPENAI_API_KEY" "$CHATBOT_SA"

step "Red: VPC, subred, IP fija y Cloud NAT"
exists gcloud compute networks describe "$VPC_NETWORK" \
  || gcloud compute networks create "$VPC_NETWORK" --subnet-mode custom
exists gcloud compute networks subnets describe "$VPC_SUBNET" --region "$REGION" \
  || gcloud compute networks subnets create "$VPC_SUBNET" \
       --network "$VPC_NETWORK" --region "$REGION" --range "$VPC_SUBNET_RANGE" \
       --enable-private-ip-google-access
exists gcloud compute addresses describe "$NAT_IP_NAME" --region "$REGION" \
  || gcloud compute addresses create "$NAT_IP_NAME" --region "$REGION"
exists gcloud compute routers describe "$ROUTER" --region "$REGION" \
  || gcloud compute routers create "$ROUTER" --network "$VPC_NETWORK" --region "$REGION"
exists gcloud compute routers nats describe "$NAT" --router "$ROUTER" --region "$REGION" \
  || gcloud compute routers nats create "$NAT" \
       --router "$ROUTER" --region "$REGION" \
       --nat-external-ip-pool "$NAT_IP_NAME" \
       --nat-custom-subnet-ip-ranges "$VPC_SUBNET"

step "Permisos del pipeline ($DEPLOYER_SA)"
DEPLOYER="serviceAccount:$(sa_email "$DEPLOYER_SA")"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member "$DEPLOYER" --role roles/run.developer --condition None >/dev/null
gcloud artifacts repositories add-iam-policy-binding "$AR_REPO" --location "$REGION" \
  --member "$DEPLOYER" --role roles/artifactregistry.writer >/dev/null
gcloud compute networks subnets add-iam-policy-binding "$VPC_SUBNET" --region "$REGION" \
  --member "$DEPLOYER" --role roles/compute.networkUser >/dev/null
for sa in "$NEWS_API_SA" "$CHATBOT_SA"; do
  gcloud iam service-accounts add-iam-policy-binding "$(sa_email "$sa")" \
    --member "$DEPLOYER" --role roles/iam.serviceAccountUser >/dev/null
done

step "Workload Identity Federation para $GITHUB_REPO (solo rama main)"
exists gcloud iam workload-identity-pools describe "$WIF_POOL" --location global \
  || gcloud iam workload-identity-pools create "$WIF_POOL" \
       --location global --display-name "GitHub Actions"
exists gcloud iam workload-identity-pools providers describe "$WIF_PROVIDER" \
    --location global --workload-identity-pool "$WIF_POOL" \
  || gcloud iam workload-identity-pools providers create-oidc "$WIF_PROVIDER" \
       --location global --workload-identity-pool "$WIF_POOL" \
       --issuer-uri "https://token.actions.githubusercontent.com" \
       --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
       --attribute-condition "assertion.repository=='${GITHUB_REPO}' && assertion.ref=='refs/heads/main'"
gcloud iam service-accounts add-iam-policy-binding "$(sa_email "$DEPLOYER_SA")" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WIF_POOL}/attribute.repository/${GITHUB_REPO}" \
  >/dev/null

NAT_IP="$(gcloud compute addresses describe "$NAT_IP_NAME" --region "$REGION" --format='value(address)')"
cat <<EOF

Listo.

1. Agrega esta IP en Atlas -> Network Access: ${NAT_IP}/32
2. Carga los secretos: make gcp-secrets
3. Primer deploy: ALLOW_PUBLIC=1 make gcp-deploy

Valores para .github/workflows/deploy.yml:
  WIF_PROVIDER: projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WIF_POOL}/providers/${WIF_PROVIDER}
  DEPLOYER_SA:  $(sa_email "$DEPLOYER_SA")
EOF

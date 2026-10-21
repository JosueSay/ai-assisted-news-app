#!/usr/bin/env bash
# Publica únicamente el export web. No lee keys/ ni despliega el backend.
set -euo pipefail
cd "$(dirname "$0")/../.."
source deploy/gcp/config.sh
require_project

node frontend/scripts/check-deploy-config.cjs "$NEWS_FIREBASE_PROJECT_ID"
if [[ "${1:-}" == "--check" ]]; then
  exit 0
fi
command -v firebase >/dev/null || {
  echo "Instala Firebase CLI: npm install -g firebase-tools" >&2
  exit 1
}
# Rebuild transformed modules so a previous export cannot retain empty/old env.
(cd frontend && NODE_ENV=production npm run export:web -- --clear)
firebase deploy --only hosting --project "$NEWS_FIREBASE_PROJECT_ID" --config firebase.json

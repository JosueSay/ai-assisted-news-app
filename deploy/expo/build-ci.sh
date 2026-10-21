#!/usr/bin/env bash
# EXPO_TOKEN lo inyecta GitHub Secrets solo en este paso; nunca se imprime.
set -euo pipefail
cd "$(dirname "$0")/../.."
if [[ -z "${EXPO_TOKEN:-}" ]]; then
  echo "Falta EXPO_TOKEN en los secretos del entorno production de GitHub." >&2
  exit 1
fi
if [[ -z "${GITHUB_ENV:-}" || ! -f frontend/google-services.json ]]; then
  echo "Se requieren el runner GitHub y frontend/google-services.json." >&2
  exit 1
fi
build_result="$(mktemp)"
trap 'rm -f "$build_result"' EXIT
(
  cd frontend
  # Esperar antes de obtener credenciales WIF evita que expiren durante la cola EAS.
  npx --yes eas-cli@25.3.0 build --platform android --profile apk \
    --non-interactive --freeze-credentials --wait --json > "$build_result"
)
node frontend/scripts/android-build-result.cjs "$build_result"

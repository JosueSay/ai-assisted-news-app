#!/usr/bin/env bash
# Crea únicamente recursos temporales propios; no monta keys/ ni volúmenes de datos.
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
test_suffix="$(python3 -c 'import uuid; print(uuid.uuid4().hex[:12])')"
test_network="news-contract-network-$test_suffix"
test_mongo="news-contract-mongo-$test_suffix"
test_runner="news-contract-runner-$test_suffix"
test_image="ai-assisted-news-app-contract-tests:local"
network_created=false
mongo_created=false
cleanup() {
  docker rm -f "$test_runner" >/dev/null 2>&1 || true
  if [ "$mongo_created" = true ]; then docker rm -f "$test_mongo" >/dev/null 2>&1 || true; fi
  if [ "$network_created" = true ]; then docker network rm "$test_network" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT
docker build -f "$project_dir/backend/assistant/Dockerfile" --target test -t "$test_image" "$project_dir/backend"
docker network create --internal "$test_network" >/dev/null
network_created=true
docker run --rm -d --name "$test_mongo" --network "$test_network" \
  --tmpfs /data/db:rw,size=1024m -e GLIBC_TUNABLES=glibc.pthread.rseq=1 mongo:8.0 >/dev/null
mongo_created=true
docker run --rm --name "$test_runner" --network "$test_network" \
  -e NEWS_TEST_MONGO_HOST="$test_mongo" \
  -e OPENAI_API_KEY_FILE=/tmp/missing-key -e API_GPT= \
  -e CHATBOT_PROVIDER=stub -e MONGODB_CONTEXT_MODE=news \
  -v "$project_dir/tests/integration:/app/integration_tests:ro" \
  "$test_image" python -m pytest -c assistant/pyproject.toml \
  integration_tests/test_news_shared_contract.py -q -s -p no:cacheprovider

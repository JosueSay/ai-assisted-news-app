.PHONY: env-local env-atlas db-check-config db-ping db-test db-init db-schema-check db-seed-catalog db-seed-catalogs db-seed-check db-seed-demo db-seed-news db-news-check db-bootstrap db-verify db-reseed-dry-run db-reseed news-db-up news-db-down news-api-up setup-keys
.PHONY: chatbot-up chatbot-test news-contract news-contract-check news-integration-test
.PHONY: chatbot-stub chatbot-api chatbot-openai chatbot-config-test
.PHONY: db-news-images-check
.PHONY: gcp-bootstrap gcp-secrets gcp-deploy
.PHONY: deploy-test firebase-check-config firebase-deploy

# El .env local de Compose puede contener localhost y otro proyecto Firebase.
# Los comandos cloud usan el entorno/config.sh y el frontend usa sus propios .env.
CLOUD_TARGETS := gcp-bootstrap gcp-secrets gcp-deploy firebase-check-config firebase-deploy deploy-test
ifneq ($(filter $(CLOUD_TARGETS),$(MAKECMDGOALS)),)
ifneq ($(filter-out $(CLOUD_TARGETS),$(MAKECMDGOALS)),)
$(error Ejecuta las tareas locales y cloud en comandos make separados)
endif
else
-include .env
endif

DOCKER_COMPOSE ?= docker compose
NEWS_DB_MODE ?= local
NEWS_MONGODB_DATABASE ?= ai_assisted_news
NEWS_MONGODB_REQUIRED ?= true
NEWS_MONGODB_TIMEOUT_MS ?= 5000
NEWS_LOCAL_MONGO_PORT ?= 27018
NEWS_API_PORT ?= 8020

export NEWS_DB_MODE
export NEWS_MONGODB_DATABASE
export NEWS_MONGODB_REQUIRED
export NEWS_MONGODB_TIMEOUT_MS
export NEWS_LOCAL_MONGO_PORT
export NEWS_API_PORT
export NEWS_FIREBASE_PROJECT_ID
export COMPOSE_PROFILES
# Parámetros no secretos para seleccionar OpenAI sin interpolarlos en shell.
export OPENAI_MODEL
export NEWS_CHAT_INPUT_USD_PER_MILLION
export NEWS_CHAT_OUTPUT_USD_PER_MILLION

define ensure_news_db
	@if [ "$(NEWS_DB_MODE)" = "local" ]; then \
		echo "=== Starting local news MongoDB ==="; \
		$(DOCKER_COMPOSE) --profile news-local up -d news-mongo; \
	fi
endef

define write_common_env
	printf '%s\n' \
		'NEWS_MONGODB_DATABASE=ai_assisted_news' \
		'NEWS_MONGODB_REQUIRED=true' \
		'NEWS_MONGODB_TIMEOUT_MS=5000' \
		'NEWS_LOCAL_MONGO_PORT=27018' \
		'NEWS_API_PORT=8020' \
		'EXPO_PUBLIC_NEWS_API_BASE_URL=http://localhost:8020' \
		'NEWS_FIREBASE_PROJECT_ID=' \
		'CHATBOT_PROVIDER=stub' \
		'CHAT_SESSION_TTL_SECONDS=3600' \
		'EXPO_PUBLIC_ASSISTANT_API_BASE_URL=http://localhost:8010'
endef

env-local:
	@echo "=== Writing .env for local MongoDB ==="
	@{ \
		printf '%s\n' \
			'# AI Assisted News App local environment' \
			'NEWS_DB_MODE=local' \
			'COMPOSE_PROFILES=news-local'; \
		$(write_common_env); \
	} > .env
	@echo ".env configured for local MongoDB."
	@echo "Run: make db-check-config"

env-atlas:
	@echo "=== Writing .env for MongoDB Atlas ==="
	@{ \
		printf '%s\n' \
			'# AI Assisted News App Atlas environment' \
			'NEWS_DB_MODE=atlas' \
			'COMPOSE_PROFILES=' \
			'NEWS_MONGODB_URI_FILE=keys/mongodb_uri'; \
		$(write_common_env); \
	} > .env
	@echo ".env configured for Atlas without storing the MongoDB URI."
	@echo "Run: make setup-keys"
	@echo "Then put the Atlas URI only in keys/mongodb_uri and run: make db-check-config"

db-check-config:
	@echo "=== Checking news DB configuration ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.check_config

db-ping:
	@echo "=== Pinging news MongoDB ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.ping

db-test:
	@echo "=== Running news DB tests ==="
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m pytest news/tests -v

db-init:
	@echo "=== Initializing news DB schema ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.schema.initialize

db-schema-check:
	@echo "=== Checking news DB schema ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.schema.check

db-seed-catalog:
	@echo "=== Seeding news catalog data ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.seed_catalog

db-seed-catalogs:
	@echo "=== Seeding news catalogs (locations) ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.seed_catalog

db-seed-check:
	@echo "=== Checking news catalogs ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.seed_check

db-seed-demo:
	@echo "=== Seeding local demo news ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.seed_demo

db-seed-news:
	@echo "=== Seeding demo news dataset (Loop 05) ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.seed_news

db-news-check:
	@echo "=== Checking demo news dataset ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.news_check

# Explicitly online; versioned fixtures only, no DB dependency or secret loading.
db-news-images-check:
	@$(DOCKER_COMPOSE) --profile tools run --rm --no-deps news-tools python -m news.news_images_check

db-bootstrap:
	@echo "=== Bootstrapping news DB (init + catalogs + demo news + checks) ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.bootstrap

db-verify:
	@echo "=== Verifying news DB (schema + catalogs + demo news) ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.verify

db-reseed-dry-run:
	@echo "=== Reseed dry run (no changes will be performed) ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.reseed_dry_run

db-reseed:
	@echo "=== Reseeding controlled news DB dataset ==="
	@echo "This deletes ONLY the 16 controlled locations and 32 demo news,"
	@echo "then rebuilds them. It requires CONFIRM=\"<exact phrase>\"."
	@echo "Local: CONFIRM=\"RESEED $(NEWS_MONGODB_DATABASE)\"."
	@echo "Atlas: CONFIRM=\"RESEED ATLAS $(NEWS_MONGODB_DATABASE)\"."
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm -e CONFIRM="$(CONFIRM)" news-tools python -m news.reseed

news-db-up:
	@$(DOCKER_COMPOSE) --profile news-local up -d news-mongo

news-db-down:
	@$(DOCKER_COMPOSE) --profile news-local stop news-mongo

news-api-up:
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) up -d news-api

chatbot-stub:
	@python3 scripts/configure_chatbot.py stub

chatbot-api: chatbot-openai

chatbot-openai:
	@python3 scripts/configure_chatbot.py openai

chatbot-config-test:
	@python3 -m unittest discover -s tests/unit -p test_configure_chatbot.py -v

chatbot-up:
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) up -d --build chatbot

chatbot-test:
	@echo "=== Running assistant tests (incluye smoke test contra el chatbot) ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile test run --rm --build tests

# Estos comandos no requieren DB ni credenciales y no levantan dependencias.
news-contract:
	@$(DOCKER_COMPOSE) --profile tools run --rm --no-deps --user "$$(id -u):$$(id -g)" news-tools python -m news.export_contract

news-contract-check:
	@$(DOCKER_COMPOSE) --profile tools run --rm --no-deps news-tools python -m news.export_contract --check

setup-keys:
	@echo "=== Setting up secret files ==="
	@mkdir -p keys
	@for f in mongodb_uri openai_api_key; do \
		if [ -e "keys/$$f" ] || [ -L "keys/$$f" ]; then \
			echo "keys/$$f       EXISTS"; \
		else \
			touch "keys/$$f"; \
			echo "keys/$$f       CREATED"; \
		fi \
	done
	@echo ""
	@echo "Complete missing secret values manually."
	@echo "Then run:"
	@echo "make db-check-config"
	@echo "make db-ping"

news-integration-test:
	@bash scripts/news-integration-test.sh

# Deploy en Google Cloud (ver docs/deploy/README.md). Requiere gcloud con sesión iniciada.
# Los secretos se suben desde keys/ sin imprimirse.
gcp-bootstrap:
	@bash deploy/gcp/bootstrap.sh

gcp-secrets:
	@bash deploy/gcp/load-secrets.sh

gcp-deploy:
	@bash deploy/gcp/deploy.sh

deploy-test:
	@python3 -m unittest discover -s tests/unit -p test_deploy_scripts.py -v

firebase-check-config:
	@bash deploy/firebase/hosting.sh --check

firebase-deploy:
	@bash deploy/firebase/hosting.sh

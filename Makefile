.PHONY: env-local env-atlas db-check-config db-ping db-test db-init db-schema-check db-seed-catalog db-seed-demo news-db-up news-db-down news-api-up setup-keys

-include .env

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
export COMPOSE_PROFILES

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
		'NEWS_ADMIN_USERNAME=admin' \
		'NEWS_ADMIN_PASSWORD_FILE=keys/news_admin_password' \
		'NEWS_ADMIN_TOKEN_TTL_SECONDS=3600'
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

db-seed-demo:
	@echo "=== Seeding local demo news ==="
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) --profile tools run --rm news-tools python -m news.seed_demo

news-db-up:
	@$(DOCKER_COMPOSE) --profile news-local up -d news-mongo

news-db-down:
	@$(DOCKER_COMPOSE) --profile news-local stop news-mongo

news-api-up:
	$(call ensure_news_db)
	@$(DOCKER_COMPOSE) up -d news-api

setup-keys:
	@echo "=== Setting up secret files ==="
	@mkdir -p keys
	@for f in mongodb_uri news_admin_password client_id client_secret; do \
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

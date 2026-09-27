.PHONY: db-check-config db-ping db-test setup-keys

NEWS_ROOT := backend/news

db-check-config:
	@echo "=== Checking news DB configuration ==="
	@python3 -c "from $(subst /,.,$(NEWS_ROOT)).check_config import run_check; print(run_check())"

db-ping:
	@echo "=== Pinging news MongoDB ==="
	@python3 -c "from $(subst /,.,$(NEWS_ROOT)).ping import run_ping; print(run_ping())"

db-test:
	@echo "=== Running news DB tests ==="
	@python3 -m pytest $(NEWS_ROOT)/tests -v

setup-keys:
	@echo "=== Setting up secret files ==="
	@mkdir -p keys
	@for f in mongodb_uri client_id client_secret; do \
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

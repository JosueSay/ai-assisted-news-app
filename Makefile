.PHONY: db-check-config db-ping db-test

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
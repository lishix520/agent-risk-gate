PYTHON ?= python3
PIP ?= pip
UVICORN ?= uvicorn
APP ?= app.main:app

.PHONY: install venv run run-mcp demo-mcp run-prod test compile db-up db-down db-logs migrate init

venv:
	$(PYTHON) -m venv .venv
	@echo "source .venv/bin/activate"

install:
	$(PIP) install -r requirements.txt

run:
	$(UVICORN) $(APP) --reload --host 0.0.0.0 --port 8000

run-prod:
	$(UVICORN) $(APP) --host 0.0.0.0 --port 8000

test:
	PYTHONPATH=. $(PYTHON) -m unittest tests/test_smoke_unittest.py -v

compile:
	$(PYTHON) -m compileall -q app tests

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

init:
	docker compose up -d postgres
	@echo "Wait for postgres and run sql/init_v1_1.sql if needed"

migrate:
	bash scripts/apply_migrations.sh

run-mcp:
	$(PYTHON) -m mcp_server.server

demo-mcp:
	$(PYTHON) examples/mcp/run_adapter_e2e.py

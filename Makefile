# ============================================================================
# Agilina — a single entry point to bring up, test and verify.
# `make` without arguments lists the available targets.
# ============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE := docker compose -f infra/docker-compose.yml --env-file .env
UV      := uv
WEB     := web

.PHONY: help env install hooks infra migrate migration up down restart \
        api agent stt web test test-python test-web coverage lint format \
        typecheck arch verify keycloak-admin logs clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------ Environment ---
env: ## Create .env from .env.example, with generated local passwords
	@test -f .env || { \
		cp .env.example .env; \
		db_password=$$(openssl rand -hex 16); \
		kc_password=$$(openssl rand -hex 16); \
		sed -i.bak -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$$db_password|" \
		           -e "s|^KEYCLOAK_ADMIN_PASSWORD=.*|KEYCLOAK_ADMIN_PASSWORD=$$kc_password|" .env; \
		rm -f .env.bak; \
		echo "Created .env with generated local passwords."; \
		echo "Fill in the LiveKit, Gemini and ElevenLabs keys before using voice."; \
	}

install: env ## Install Python (uv) and web (npm) dependencies
	$(UV) sync --all-packages
	cd $(WEB) && (test -f package-lock.json && npm ci || npm install)

hooks: ## Install the pre-commit hooks (once per clone)
	$(UV) run pre-commit install --install-hooks
	$(UV) run pre-commit install --hook-type commit-msg
	$(UV) run pre-commit install --hook-type pre-push

# --------------------------------------------------------- Infrastructure ---
infra: env ## Bring up Postgres and Keycloak in containers
	$(COMPOSE) up -d postgres keycloak
	@echo "Postgres on localhost:5432 · Keycloak on http://localhost:8080"

migrate: ## Apply the pending database migrations
	cd api && $(UV) run alembic upgrade head

migration: ## Create a new migration: make migration m="description"
	cd api && $(UV) run alembic revision --autogenerate -m "$(m)"

up: install infra ## THE command: leave the whole environment ready to work
	./infra/wait-for-services.sh
	$(MAKE) migrate
	@echo ""
	@echo "Environment ready. In separate terminals:"
	@echo "  make api    → http://localhost:8000/docs"
	@echo "  make stt    → http://localhost:8001/docs"
	@echo "  make web    → http://localhost:4200"
	@echo "  make agent  → worker registered in LiveKit"

down: ## Stop the containers without deleting the data
	$(COMPOSE) down

restart: down up ## Restart the whole environment

logs: ## Follow the infrastructure logs
	$(COMPOSE) logs -f

keycloak-admin: ## Show where the Keycloak admin console is
	@echo "http://localhost:8080/admin — user and password in your .env"

# ------------------------------------------------------------ Executables ---
api: env ## Run the API with auto-reload
	@set -a; . ./.env; set +a; \
	$(UV) run uvicorn agilina_api.bootstrap.app:app --reload \
		--host $${AGILINA_API_HOST:-127.0.0.1} --port $${AGILINA_API_PORT:-8000}

agent: env ## Run the agent worker and register it in LiveKit
	@set -a; . ./.env; set +a; $(UV) run python -m agilina_agent.main dev

stt: env ## Run the transcription service
	@set -a; . ./.env; set +a; \
	$(UV) run uvicorn agilina_stt.main:app --reload --host 127.0.0.1 --port 8001

web: ## Run the Angular application
	cd $(WEB) && npm start

# ---------------------------------------------------------------- Quality ---
lint: ## Static analysis of Python and the web
	$(UV) run ruff check .
	cd $(WEB) && npm run lint

format: ## Format the Python code
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

typecheck: ## Strict type checking of the Python packages
	$(UV) run mypy shared/src api/src agent/src stt/src

arch: ## Check the architecture rules (layers and context boundaries)
	$(UV) run lint-imports

test: test-python test-web ## Run all the tests

test-python: ## Tests of the Python packages
	$(UV) run pytest

test-web: ## Tests of the Angular application
	cd $(WEB) && npm run test:ci

coverage: ## Python tests with a coverage report
	$(UV) run pytest --cov --cov-report=term-missing --cov-report=xml

verify: ## The same the pipeline runs, on your machine
	$(UV) run ruff format --check .
	$(UV) run ruff check .
	$(UV) run mypy shared/src api/src agent/src stt/src
	$(UV) run lint-imports
	$(UV) run pytest --cov --cov-report=term-missing
	cd $(WEB) && npm run lint && npm run build && npm run test:ci
	@echo ""
	@echo "Verification green. The pull request should not fail on analysis or tests."

clean: ## Delete build artifacts, caches and containers with their data
	$(COMPOSE) down -v
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache htmlcov coverage.xml .coverage
	rm -rf $(WEB)/node_modules $(WEB)/dist $(WEB)/.angular $(WEB)/coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

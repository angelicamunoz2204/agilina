# ============================================================================
# Agilina — a single entry point to bring up, test and verify.
# Everything runs in containers: the only things needed on your machine are
# Docker (with Compose) and make, plus bash, curl and openssl, which any Linux or
# macOS already has. `make` without arguments lists the targets.
# ============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

# The dev containers run as your user, so the files they create are yours.
export HOST_UID := $(shell id -u)
export HOST_GID := $(shell id -g)

COMPOSE   := docker compose -f infra/docker-compose.yml --env-file .env
# --build: `run` reuses an image that already exists under the same name; building first
# guarantees the image matches the current Dockerfile and dependencies (cached, so cheap).
TOOLS     := $(COMPOSE) --profile tools run --rm --no-deps --build tools
WEB       := $(COMPOSE) run --rm --no-deps --build web
PYPACKAGES := shared/src api/src agent/src stt/src

.PHONY: help env up infra down restart ps logs migrate migration stt agent \
        lint format typecheck arch test test-python test-integration test-web coverage verify \
        mail-test lock hooks keycloak-admin clean

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

up: env ## THE command: build and start everything, wait, migrate
	$(COMPOSE) up -d --build postgres keycloak mailpit api web
	./infra/wait-for-services.sh
	$(MAKE) migrate
	@echo ""
	@echo "Environment ready:"
	@echo "  API       http://localhost:8000/docs"
	@echo "  Web       http://localhost:4200"
	@echo "  Mailpit   http://localhost:8025   (every email the app sends lands here)"
	@echo "  Keycloak  http://localhost:8080"
	@echo "Voice (optional): make stt, make agent. Logs: make logs s=api"

infra: env ## Start only the infrastructure: Postgres, Keycloak and Mailpit
	$(COMPOSE) up -d postgres keycloak mailpit
	@echo "Postgres :5432 · Keycloak http://localhost:8080 · Mailpit http://localhost:8025"

down: env ## Stop the containers without deleting the data
	$(COMPOSE) --profile voice --profile tools down

restart: down up ## Restart the whole environment

ps: env ## List the running services
	$(COMPOSE) --profile voice ps

logs: env ## Follow the logs: make logs [s=api]
	$(COMPOSE) --profile voice logs -f $(s)

keycloak-admin: env ## Show the Keycloak admin console and its credentials
	@echo "http://localhost:8080/admin"
	@grep -E '^KEYCLOAK_ADMIN(_PASSWORD)?=' .env

# --------------------------------------------------------------- Database ---
migrate: env ## Apply the pending database migrations
	$(COMPOSE) run --rm --build -w /app/api api alembic upgrade head

# Autogenerate is deliberately not used (see docs/code-conventions.md): this creates an
# empty revision to fill in by hand, in SQL.
migration: env ## Create an empty migration to write in SQL: make migration m="description"
	@test -n "$(m)" || { echo 'Usage: make migration m="description"'; exit 1; }
	$(COMPOSE) run --rm --build -w /app/api api alembic revision -m "$(m)"

# ------------------------------------------------------------------ Email ---
mail-test: env ## Send a test email with the configured SMTP: make mail-test to=you@example.com [lang=en]
	@test -n "$(to)" || { echo "Usage: make mail-test to=address@example.com [lang=es|en]"; exit 1; }
	$(COMPOSE) run --rm --no-deps --build api python -m agilina_api.bootstrap.send_test_email --to "$(to)" $(if $(lang),--lang "$(lang)",)

# ------------------------------------------------------------------ Voice ---
stt: env ## Start the transcription service (simulated unless you set a GPU)
	$(COMPOSE) --profile voice up -d --build stt
	@echo "STT http://localhost:8001/docs"

agent: env ## Start the agent worker and register it in LiveKit
	@grep -Eq '^AGILINA_LIVEKIT_API_KEY=.+' .env && grep -Eq '^AGILINA_LIVEKIT_API_SECRET=.+' .env || { \
		echo "The agent needs LiveKit: fill AGILINA_LIVEKIT_URL, AGILINA_LIVEKIT_API_KEY and"; \
		echo "AGILINA_LIVEKIT_API_SECRET in .env, then run make agent again."; exit 1; }
	$(COMPOSE) --profile voice up -d --build stt agent
	@echo "Agent started. Check that it registered: make logs s=agent"

# ---------------------------------------------------------------- Quality ---
lint: env ## Static analysis of Python and the web
	$(TOOLS) ruff check .
	$(WEB) npm run lint

format: env ## Format the Python code
	$(TOOLS) sh -c "ruff format . && ruff check --fix ."

typecheck: env ## Strict type checking of the Python packages
	$(TOOLS) mypy $(PYPACKAGES)

arch: env ## Check the architecture rules (layers and context boundaries)
	$(TOOLS) lint-imports

test: test-python test-integration test-web ## Run all the tests

test-python: env ## Tests of the Python packages
	$(TOOLS) pytest

test-integration: env ## Integration tests against a real PostgreSQL (starts it)
	$(COMPOSE) --profile tools run --rm --build tools pytest -m integration

test-web: env ## Tests of the Angular application (headless Chromium)
	$(COMPOSE) --profile tools run --rm --no-deps --build web-test

coverage: env ## Python tests with a coverage report
	$(TOOLS) pytest --cov --cov-report=term-missing --cov-report=xml

verify: env ## The same the pipeline runs, in containers
	$(TOOLS) sh -c "ruff format --check . && ruff check . && mypy $(PYPACKAGES) && lint-imports && pytest --cov --cov-report=term-missing"
	$(MAKE) test-integration
	$(WEB) sh -c "npm run lint && npm run build"
	$(MAKE) test-web
	@echo ""
	@echo "Verification green. The pull request should not fail on analysis or tests."

# ----------------------------------------------------------- Dependencies ---
# Run it after changing pyproject.toml or web/package.json, and commit the two lock
# files: they pin the exact version of every library, so the images, the CI and every
# machine install the same thing. It does not upgrade what is already pinned.
# It uses plain uv and node images, not ours: our images require the lock to be
# up to date, and this is the command that brings it up to date.
UV_IMAGE   := ghcr.io/astral-sh/uv:0.9-python3.12-bookworm-slim
NODE_IMAGE := node:22-bookworm-slim
AS_YOU     := -u "$(HOST_UID):$(HOST_GID)" -e HOME=/tmp

lock: ## Update uv.lock and web/package-lock.json (commit them)
	docker run --rm $(AS_YOU) -e UV_CACHE_DIR=/tmp/uv -v "$(CURDIR):/app" -w /app $(UV_IMAGE) uv lock
	docker run --rm $(AS_YOU) -v "$(CURDIR)/web:/app" -w /app $(NODE_IMAGE) npm install --package-lock-only

# ------------------------------------------------------------------ Hooks ---
hooks: ## Install the git hooks (optional; needs pre-commit on your machine)
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg
	pre-commit install --hook-type pre-push

clean: ## Delete the containers with their data, the images and the caches
	-$(COMPOSE) --profile voice --profile tools down -v --rmi local
	rm -rf .pytest_cache .ruff_cache .mypy_cache .import_linter_cache htmlcov coverage.xml .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

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
# The whole web/ folder mounted as your user, for commands that rewrite files outside
# src/ and public/ (Prettier). node_modules stays the image's.
WEB_RW    := $(COMPOSE) run --rm --no-deps --build -u "$(HOST_UID):$(HOST_GID)" \
             -v "$(CURDIR)/web:/app" -v /app/node_modules web
PYPACKAGES := shared/src api/src agent/src stt/src

.PHONY: help env up infra down restart ps logs migrate migration stt agent \
        lint format typecheck arch test test-python test-integration test-keycloak test-web coverage verify \
        invite mail-test lock hooks keycloak-admin keycloak-reset credentials clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------ Environment ---
env: ## Create .env from .env.example, or complete it, with generated local passwords
	@test -f .env || { cp .env.example .env; echo "Created .env."; \
		echo "Fill in the LiveKit, Gemini and ElevenLabs keys before using voice."; }
	@# Keys added to .env.example after your .env was created are appended with their defaults.
	@for key in $$(grep -E '^[A-Z][A-Z0-9_]*=' .env.example | cut -d= -f1); do \
		grep -q "^$$key=" .env || { grep "^$$key=" .env.example >> .env; echo "Added $$key to .env"; }; \
	done
	@# Local passwords that are still empty are generated.
	@for key in POSTGRES_PASSWORD KEYCLOAK_ADMIN_PASSWORD PGADMIN_ADMIN_PASSWORD AGILINA_KEYCLOAK_API_SECRET; do \
		grep -Eq "^$$key=.+" .env || { \
			sed -i.bak -e "s|^$$key=.*|$$key=$$(openssl rand -hex 16)|" .env && rm -f .env.bak; \
			echo "Generated $$key in .env"; }; \
	done

up: env ## THE command: build and start everything, wait, migrate
	$(COMPOSE) up -d --build postgres pgadmin keycloak mailpit api web
	./infra/wait-for-services.sh
	$(MAKE) migrate
	@echo ""
	@echo "Environment ready:"
	@echo "  API       http://localhost:8000/docs"
	@echo "  Web       http://localhost:4200"
	@echo "  Mailpit   http://localhost:8025   (every email the app sends lands here)"
	@echo "  Keycloak  http://localhost:8080"
	@echo "  pgAdmin   http://localhost:5051   (credentials: make credentials)"
	@echo "Voice (optional): make stt, make agent. Logs: make logs s=api"

infra: env ## Start only the infrastructure: Postgres, pgAdmin, Keycloak and Mailpit
	$(COMPOSE) up -d postgres pgadmin keycloak mailpit
	@echo "Postgres :5432 · pgAdmin http://localhost:5051 · Keycloak http://localhost:8080 · Mailpit http://localhost:8025"

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

# The realm is imported only when Keycloak starts with an empty volume: a change to
# infra/keycloak/realm-agilina.json needs this. It deletes Keycloak's data, not Postgres'.
keycloak-reset: env ## Re-import the Keycloak realm from infra/keycloak (deletes only Keycloak's data)
	$(COMPOSE) rm -sf keycloak
	-docker volume rm agilina_keycloak-data
	$(COMPOSE) up -d --wait keycloak

credentials: env ## Show the local URLs and credentials: Postgres, pgAdmin and Keycloak
	@echo "Postgres   localhost:$$(grep '^POSTGRES_PORT=' .env | cut -d= -f2)   (inside the network: postgres:5432)"
	@grep -E '^POSTGRES_(DB|USER|PASSWORD)=' .env | sed 's/^/           /'
	@echo "pgAdmin    http://localhost:$$(grep '^PGADMIN_PORT=' .env | cut -d= -f2)"
	@grep -E '^PGADMIN_ADMIN_(EMAIL|PASSWORD)=' .env | sed 's/^/           /'
	@echo "Keycloak   http://localhost:8080/admin"
	@grep -E '^KEYCLOAK_ADMIN(_PASSWORD)?=' .env | sed 's/^/           /'

# --------------------------------------------------------------- Database ---
migrate: env ## Apply the pending database migrations
	$(COMPOSE) run --rm --build -w /app/api api alembic upgrade head

# Autogenerate is deliberately not used (see docs/code-conventions.md): this creates an
# empty revision to fill in by hand, in SQL.
migration: env ## Create an empty migration to write in SQL: make migration m="description"
	@test -n "$(m)" || { echo 'Usage: make migration m="description"'; exit 1; }
	$(COMPOSE) run --rm --build -w /app/api api alembic revision -m "$(m)"

# --------------------------------------------------------------- Operator ---
invite: env ## Create a team and invite its first admin: make invite team="Atlas" email=a@b.com name="Ana Gil" [lang=es] [role=admin]
	@test -n "$(email)" -a -n "$(name)" -a \( -n "$(team)" -o -n "$(team_id)" \) || { \
		echo 'Usage: make invite team="Atlas" email=a@b.com name="Ana Gil" [lang=es] [role=admin]'; \
		echo '       make invite team_id=<uuid> email=a@b.com name="Ana Gil"   (an existing team)'; exit 1; }
	$(COMPOSE) run --rm --build api python -m agilina_api.bootstrap.invite \
		--email "$(email)" --name "$(name)" \
		$(if $(team),--team "$(team)",--team-id "$(team_id)") \
		$(if $(lang),--lang "$(lang)",) $(if $(role),--role "$(role)",)

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

format: env ## Format the Python code and the web (Prettier)
	$(TOOLS) sh -c "ruff format . && ruff check --fix ."
	$(WEB_RW) npm run format

typecheck: env ## Strict type checking of the Python packages
	$(TOOLS) mypy $(PYPACKAGES)

arch: env ## Check the architecture rules (layers and context boundaries)
	$(TOOLS) lint-imports

test: test-python test-integration test-web ## Run all the tests

test-python: env ## Tests of the Python packages
	$(TOOLS) pytest

test-integration: env ## Integration tests against a real PostgreSQL (starts it)
	$(COMPOSE) --profile tools run --rm --build tools pytest -m integration

test-keycloak: env ## Tests against the real Keycloak (starts it and waits for it)
	$(COMPOSE) up -d --wait keycloak
	$(COMPOSE) --profile tools run --rm --build tools pytest -m keycloak

test-web: env ## Tests of the Angular application (headless Chromium)
	$(COMPOSE) --profile tools run --rm --no-deps --build web-test

coverage: env ## Unit + integration coverage of the API and the contract; fails below 100 %
	$(COMPOSE) --profile tools run --rm --build tools sh -c "pytest --cov --cov-report= \
		&& pytest -m integration --cov --cov-append --cov-report= \
		&& coverage report --show-missing --skip-covered --fail-under=100 \
		&& coverage xml"

verify: env ## The same the pipeline runs, in containers
	$(TOOLS) sh -c "ruff format --check . && ruff check . && mypy $(PYPACKAGES) && lint-imports"
	$(MAKE) coverage
	$(WEB) sh -c "npm run format:check && npm run lint && npm run build"
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

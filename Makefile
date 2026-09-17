# ============================================================================
# Agilina — un solo punto de entrada para levantar, probar y verificar.
# `make` sin argumentos lista los objetivos disponibles.
# ============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := ayuda

COMPOSE := docker compose -f infra/docker-compose.yml --env-file .env
UV      := uv
WEB     := web

.PHONY: ayuda env instalar ganchos infra migrar migracion arriba abajo reiniciar \
        api agent stt web pruebas pruebas-python pruebas-web cobertura lint formato \
        verificar keycloak-admin logs limpiar

ayuda: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- Entorno ---
env: ## Crea el .env a partir de .env.example, con claves locales generadas
	@test -f .env || { \
		cp .env.example .env; \
		clave_bd=$$(openssl rand -hex 16); \
		clave_kc=$$(openssl rand -hex 16); \
		sed -i.bak -e "s|^POSTGRES_CLAVE=.*|POSTGRES_CLAVE=$$clave_bd|" \
		           -e "s|^KEYCLOAK_ADMIN_CLAVE=.*|KEYCLOAK_ADMIN_CLAVE=$$clave_kc|" .env; \
		rm -f .env.bak; \
		echo "Creado .env con claves locales generadas."; \
		echo "Completa las claves de LiveKit, Gemini y ElevenLabs antes de usar la voz."; \
	}

instalar: env ## Instala dependencias de Python (uv) y de la web (npm)
	$(UV) sync --all-packages
	cd $(WEB) && (test -f package-lock.json && npm ci || npm install)

ganchos: ## Instala los ganchos de pre-commit (una sola vez por clon)
	$(UV) run pre-commit install --install-hooks
	$(UV) run pre-commit install --hook-type commit-msg

# --------------------------------------------------------- Infraestructura --
infra: env ## Levanta Postgres y Keycloak en contenedores
	$(COMPOSE) up -d postgres keycloak
	@echo "Postgres en localhost:5432 · Keycloak en http://localhost:8080"

migrar: ## Aplica las migraciones pendientes a la base de datos
	cd api && $(UV) run alembic upgrade head

migracion: ## Crea una migración nueva: make migracion m="descripcion"
	cd api && $(UV) run alembic revision --autogenerate -m "$(m)"

arriba: instalar infra ## EL comando: deja el entorno completo listo para trabajar
	./infra/esperar-servicios.sh
	$(MAKE) migrar
	@echo ""
	@echo "Entorno listo. En terminales separadas:"
	@echo "  make api    → http://localhost:8000/docs"
	@echo "  make stt    → http://localhost:8001/docs"
	@echo "  make web    → http://localhost:4200"
	@echo "  make agent  → worker registrado en LiveKit"

abajo: ## Detiene los contenedores sin borrar los datos
	$(COMPOSE) down

reiniciar: abajo arriba ## Reinicia el entorno completo

logs: ## Sigue los logs de la infraestructura
	$(COMPOSE) logs -f

keycloak-admin: ## Abre la consola de administración de Keycloak
	@echo "http://localhost:8080/admin — usuario y clave en tu .env"

# ------------------------------------------------------------ Ejecutables ---
api: env ## Ejecuta la API con recarga automática
	@set -a; . ./.env; set +a; \
	$(UV) run uvicorn agilina_api.main:app --reload \
		--host $${AGILINA_API_HOST:-127.0.0.1} --port $${AGILINA_API_PUERTO:-8000}

agent: env ## Ejecuta el worker del agente y lo registra en LiveKit
	@set -a; . ./.env; set +a; $(UV) run python -m agilina_agent.main dev

stt: env ## Ejecuta el servicio de transcripción
	@set -a; . ./.env; set +a; \
	$(UV) run uvicorn agilina_stt.main:app --reload --host 127.0.0.1 --port 8001

web: ## Ejecuta la aplicación Angular
	cd $(WEB) && npm start

# --------------------------------------------------------------- Calidad ----
lint: ## Análisis estático de Python y de la web
	$(UV) run ruff check .
	cd $(WEB) && npm run lint

formato: ## Formatea el código de Python
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

pruebas: pruebas-python pruebas-web ## Ejecuta todas las pruebas

pruebas-python: ## Pruebas de los paquetes de Python
	$(UV) run pytest

pruebas-web: ## Pruebas de la aplicación Angular
	cd $(WEB) && npm run test:ci

cobertura: ## Pruebas de Python con reporte de cobertura
	$(UV) run pytest --cov --cov-report=term-missing --cov-report=xml

verificar: ## Lo mismo que corre el pipeline, en tu máquina
	$(UV) run ruff format --check .
	$(UV) run ruff check .
	$(UV) run pytest --cov --cov-report=term-missing
	cd $(WEB) && npm run lint && npm run build && npm run test:ci
	@echo ""
	@echo "Verificación en verde. El pull request no debería fallar por análisis ni pruebas."

limpiar: ## Borra artefactos de build, cachés y contenedores con sus datos
	$(COMPOSE) down -v
	rm -rf .venv .pytest_cache .ruff_cache htmlcov coverage.xml .coverage
	rm -rf $(WEB)/node_modules $(WEB)/dist $(WEB)/.angular $(WEB)/coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

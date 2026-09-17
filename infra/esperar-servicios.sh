#!/usr/bin/env bash
# Espera a que Postgres y Keycloak estén listos antes de seguir.
# Sin esto, `make arriba` intentaría migrar contra una base que todavía arranca.
set -euo pipefail

COMPOSE=(docker compose -f "$(dirname "$0")/docker-compose.yml" --env-file .env)
ESPERA_MAXIMA=${ESPERA_MAXIMA:-90}

esperar() {
  local nombre="$1" intentos=0
  shift
  printf 'Esperando a %s' "$nombre"
  until "$@" >/dev/null 2>&1; do
    intentos=$((intentos + 1))
    if [ "$intentos" -ge "$ESPERA_MAXIMA" ]; then
      printf '\n%s no respondió en %s segundos.\n' "$nombre" "$ESPERA_MAXIMA" >&2
      printf 'Revisa los logs con: make logs\n' >&2
      exit 1
    fi
    printf '.'
    sleep 1
  done
  printf ' listo\n'
}

esperar "Postgres" "${COMPOSE[@]}" exec -T postgres pg_isready -q
esperar "Keycloak" curl -fsS http://localhost:9000/health/ready

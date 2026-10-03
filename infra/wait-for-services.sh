#!/usr/bin/env bash
# Wait for Postgres and Keycloak to be ready before going on.
# Without this, `make up` would try to migrate against a database that is still starting.
set -euo pipefail

COMPOSE=(docker compose -f "$(dirname "$0")/docker-compose.yml" --env-file .env)
MAX_WAIT=${MAX_WAIT:-90}

wait_for() {
  local name="$1" attempts=0
  shift
  printf 'Waiting for %s' "$name"
  until "$@" >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge "$MAX_WAIT" ]; then
      printf '\n%s did not respond in %s seconds.\n' "$name" "$MAX_WAIT" >&2
      printf 'Check the logs with: make logs\n' >&2
      exit 1
    fi
    printf '.'
    sleep 1
  done
  printf ' ready\n'
}

wait_for "Postgres" "${COMPOSE[@]}" exec -T postgres pg_isready -q
wait_for "Keycloak" curl -fsS http://localhost:9000/health/ready

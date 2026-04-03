#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/automata}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "${APP_DIR}"

echo "[deploy] pull images..."
docker compose -f "${COMPOSE_FILE}" pull

echo "[deploy] restart services..."
docker compose -f "${COMPOSE_FILE}" up -d

echo "[deploy] prune dangling images..."
docker image prune -f

echo "[deploy] done"

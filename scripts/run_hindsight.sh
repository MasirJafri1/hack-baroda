#!/usr/bin/env bash
# Helper to run Hindsight using docker-compose or docker run fallback
set -euo pipefail

COMPOSE_FILE="docker-compose.hindsight.yml"

if command -v docker-compose >/dev/null 2>&1 && [ -f "$COMPOSE_FILE" ]; then
  echo "Starting Hindsight via docker-compose..."
  docker-compose -f "$COMPOSE_FILE" up -d
  echo "Hindsight should be available at http://localhost:8080"
  exit 0
fi

echo "docker-compose not available or compose file missing; falling back to docker run"
docker run --rm -p 8080:8080 hindsightai/hindsight:latest

#!/usr/bin/env bash
set -euo pipefail

docker compose down --volumes --remove-orphans
docker compose up -d

echo "Waiting for PostgreSQL initialization..."
until docker compose exec -T postgres \
    pg_isready -U telemetry -d telemetry >/dev/null 2>&1
do
    sleep 1
done

docker compose exec -T postgres \
    psql -U telemetry -d telemetry \
    -c 'SELECT id FROM phase1_environment_marker ORDER BY id;'

echo "Clean Phase 1 seed complete."

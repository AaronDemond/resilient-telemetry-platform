#!/usr/bin/env bash
set -euo pipefail

docker compose up -d

echo "Waiting for PostgreSQL..."
until docker compose exec -T postgres \
    pg_isready -U telemetry -d telemetry >/dev/null 2>&1
do
    sleep 1
done

echo "Infrastructure is ready for Phase 1."
docker compose ps

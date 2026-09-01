#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if [[ -f ".env" ]]; then
  set -a
  source .env
  set +a
fi

PGDATABASE="${POSTGRES_DB:-telemetry}"
PGUSER="${POSTGRES_USER:-telemetry}"

echo "Clearing all telemetry rows from database '${PGDATABASE}'..."

docker compose exec -T postgres psql -U "${PGUSER}" -d "${PGDATABASE}" -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE telemetry_messages RESTART IDENTITY;"

echo "Telemetry data cleared successfully."

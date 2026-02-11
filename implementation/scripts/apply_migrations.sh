#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is required"
  exit 1
fi

psql "$DATABASE_URL" -f "$ROOT_DIR/sql/migrations/001_v1_1_to_v1_2.sql"
psql "$DATABASE_URL" -f "$ROOT_DIR/sql/migrations/002_backfill_main_constraint.sql"
psql "$DATABASE_URL" -f "$ROOT_DIR/sql/migrations/003_outcome_unique_per_decision.sql"
psql "$DATABASE_URL" -f "$ROOT_DIR/sql/migrations/004_high_risk_confirmations.sql"

echo "migrations applied"

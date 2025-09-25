#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL must be set" >&2
  exit 1
fi

python - <<'PY'
from app.db import init_db
init_db()
PY

echo "Database bootstrapped"

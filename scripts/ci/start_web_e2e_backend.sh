#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DB_PATH="${KONA_E2E_DATABASE_PATH:-/tmp/kona_web_e2e.db}"

export JWT_SECRET="${JWT_SECRET:-web-e2e-secret}"
export KONA_DATABASE_PATH="$DB_PATH"
export KONA_HOST="${KONA_HOST:-127.0.0.1}"
export KONA_PORT="${KONA_PORT:-52345}"
export ENABLE_PRICE_PRELOADER="false"
export ENABLE_BACKGROUND_SNAPSHOT="false"
export ENABLE_STARTUP_SNAPSHOT="false"
export RATELIMIT_STORAGE_URL="memory://"
export REQUEST_RUNTIME_STORAGE_URL="memory://"

python3 "$ROOT_DIR/scripts/ci/seed_web_e2e_db.py" "$DB_PATH"
cd "$ROOT_DIR/kona_tool"
python3 app.py

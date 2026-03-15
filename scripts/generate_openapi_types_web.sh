#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WEB_DIR="${ROOT_DIR}/web"

cd "${WEB_DIR}"
npm run gen:api

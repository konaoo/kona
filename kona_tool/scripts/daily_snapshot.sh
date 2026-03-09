#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${APP_DIR}/archive/logs"
mkdir -p "${LOG_DIR}"

ts=$(date +%Y%m%d_%H%M%S)
curl -s -X POST "http://127.0.0.1:5003/api/snapshot/trigger" > "${LOG_DIR}/snapshot_${ts}.log"

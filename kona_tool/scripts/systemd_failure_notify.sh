#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${APP_DIR}/.venv/bin/python"
UNIT_NAME="${1:-kona.service}"
HOSTNAME="$(hostname)"

LOG_TAIL="$(journalctl -u "${UNIT_NAME}" -n 80 --no-pager 2>&1 || true)"
BODY="Systemd unit failure detected.

Host: ${HOSTNAME}
Unit: ${UNIT_NAME}

Recent logs:
${LOG_TAIL}
"

if [ ! -x "${PYTHON_BIN}" ]; then
  echo "未找到虚拟环境 Python: ${PYTHON_BIN}" >&2
  exit 1
fi

"${PYTHON_BIN}" "${APP_DIR}/scripts/alert_sender.py" \
  --subject "[Kona][ALERT] ${UNIT_NAME} failed on ${HOSTNAME}" \
  --body "${BODY}"

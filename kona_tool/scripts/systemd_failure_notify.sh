#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ec2-user/portfolio/kona_tool"
UNIT_NAME="${1:-kona.service}"
HOSTNAME="$(hostname)"

LOG_TAIL="$(journalctl -u "${UNIT_NAME}" -n 80 --no-pager 2>&1 || true)"
BODY="Systemd unit failure detected.

Host: ${HOSTNAME}
Unit: ${UNIT_NAME}

Recent logs:
${LOG_TAIL}
"

python3 "${APP_DIR}/scripts/alert_sender.py" \
  --subject "[Kona][ALERT] ${UNIT_NAME} failed on ${HOSTNAME}" \
  --body "${BODY}"

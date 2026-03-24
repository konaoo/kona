#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${APP_DIR}/.venv/bin/python"

if [ ! -x "${PYTHON_BIN}" ]; then
  echo "未找到虚拟环境 Python: ${PYTHON_BIN}"
  echo "请先在 ${APP_DIR} 下创建 .venv 并安装依赖。"
  exit 1
fi

echo "[1/6] Create alert service for kona.service failures..."
sudo tee /etc/systemd/system/kona-alert@.service >/dev/null <<'EOF'
[Unit]
Description=Kona alert for failed unit %i
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=__APP_DIR__
EnvironmentFile=__APP_DIR__/.env
ExecStart=/bin/bash __APP_DIR__/scripts/systemd_failure_notify.sh %i
EOF

sudo sed -i "s|__APP_DIR__|${APP_DIR}|g" /etc/systemd/system/kona-alert@.service

echo "[2/6] Ensure kona.service has OnFailure hook..."
if ! sudo grep -q '^OnFailure=kona-alert@%n.service$' /etc/systemd/system/kona.service; then
  sudo sed -i '/^\[Unit\]/a OnFailure=kona-alert@%n.service' /etc/systemd/system/kona.service
fi

echo "[3/6] Create periodic health-check service/timer..."
sudo tee /etc/systemd/system/kona-healthcheck.service >/dev/null <<'EOF'
[Unit]
Description=Kona health check with email alert
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=__APP_DIR__
EnvironmentFile=__APP_DIR__/.env
ExecStart=__PYTHON_BIN__ __APP_DIR__/scripts/check_kona_health.py
EOF

sudo sed -i \
  -e "s|__APP_DIR__|${APP_DIR}|g" \
  -e "s|__PYTHON_BIN__|${PYTHON_BIN}|g" \
  /etc/systemd/system/kona-healthcheck.service

sudo tee /etc/systemd/system/kona-healthcheck.timer >/dev/null <<'EOF'
[Unit]
Description=Run Kona health check every 2 minutes

[Timer]
OnCalendar=*:0/2
Persistent=true
Unit=kona-healthcheck.service

[Install]
WantedBy=timers.target
EOF

echo "[4/6] Create daily snapshot verification service/timer..."
sudo tee /etc/systemd/system/kona-snapshot-verify.service >/dev/null <<'EOF'
[Unit]
Description=Verify daily snapshot exists and alert on missing
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=__APP_DIR__
EnvironmentFile=__APP_DIR__/.env
ExecStart=__PYTHON_BIN__ __APP_DIR__/scripts/check_daily_snapshot.py
EOF

sudo sed -i \
  -e "s|__APP_DIR__|${APP_DIR}|g" \
  -e "s|__PYTHON_BIN__|${PYTHON_BIN}|g" \
  /etc/systemd/system/kona-snapshot-verify.service

sudo tee /etc/systemd/system/kona-snapshot-verify.timer >/dev/null <<'EOF'
[Unit]
Description=Verify snapshot at 07:05 Beijing every day

[Timer]
OnCalendar=*-*-* 23:05:00
Persistent=true
Unit=kona-snapshot-verify.service

[Install]
WantedBy=timers.target
EOF

echo "[5/6] Create periodic price-health alert service/timer..."
sudo tee /etc/systemd/system/kona-price-health-alert.service >/dev/null <<'EOF'
[Unit]
Description=Kona price health threshold alert
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=__APP_DIR__
EnvironmentFile=__APP_DIR__/.env
ExecStart=__PYTHON_BIN__ __APP_DIR__/scripts/check_price_health_alert.py
EOF

sudo sed -i \
  -e "s|__APP_DIR__|${APP_DIR}|g" \
  -e "s|__PYTHON_BIN__|${PYTHON_BIN}|g" \
  /etc/systemd/system/kona-price-health-alert.service

sudo tee /etc/systemd/system/kona-price-health-alert.timer >/dev/null <<'EOF'
[Unit]
Description=Run Kona price-health threshold checks every 5 minutes

[Timer]
OnCalendar=*:0/5
Persistent=true
Unit=kona-price-health-alert.service

[Install]
WantedBy=timers.target
EOF

echo "[6/6] Reload and enable timers/services..."
sudo systemctl daemon-reload
sudo systemctl restart kona
sudo systemctl enable --now kona-healthcheck.timer
sudo systemctl enable --now kona-snapshot-verify.timer
sudo systemctl enable --now kona-price-health-alert.timer

echo
echo "Done. Current timer status:"
sudo systemctl list-timers | grep -E 'kona-(healthcheck|snapshot-verify|snapshot|price-health-alert)'

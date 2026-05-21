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

echo "[1/3] Create kona-db-backup.service..."
sudo tee /etc/systemd/system/kona-db-backup.service >/dev/null <<'EOF'
[Unit]
Description=Kona SQLite backup
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=__APP_DIR__
EnvironmentFile=__APP_DIR__/.env
ExecStart=__PYTHON_BIN__ __APP_DIR__/scripts/backup_portfolio_db.py
EOF

sudo sed -i \
  -e "s|__APP_DIR__|${APP_DIR}|g" \
  -e "s|__PYTHON_BIN__|${PYTHON_BIN}|g" \
  /etc/systemd/system/kona-db-backup.service

echo "[2/3] Create kona-db-backup.timer (07:20 Beijing, daily)..."
sudo tee /etc/systemd/system/kona-db-backup.timer >/dev/null <<'EOF'
[Unit]
Description=Run Kona DB backup daily at 07:20 Beijing

[Timer]
OnCalendar=*-*-* 07:20:00
Persistent=true
Unit=kona-db-backup.service

[Install]
WantedBy=timers.target
EOF

echo "[3/3] Reload and enable timer..."
sudo systemctl daemon-reload
sudo systemctl enable --now kona-db-backup.timer

echo
echo "Done. Timer status:"
sudo systemctl list-timers | grep -E 'kona-db-backup'

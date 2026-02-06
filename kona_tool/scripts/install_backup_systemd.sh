#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] Create kona-db-backup.service..."
sudo tee /etc/systemd/system/kona-db-backup.service >/dev/null <<'EOF'
[Unit]
Description=Kona SQLite backup
After=network.target

[Service]
Type=oneshot
User=ec2-user
WorkingDirectory=/home/ec2-user/portfolio/kona_tool
EnvironmentFile=/home/ec2-user/portfolio/kona_tool/.env
ExecStart=/usr/bin/python3 /home/ec2-user/portfolio/kona_tool/scripts/backup_portfolio_db.py
EOF

echo "[2/3] Create kona-db-backup.timer (07:20 Beijing, daily)..."
sudo tee /etc/systemd/system/kona-db-backup.timer >/dev/null <<'EOF'
[Unit]
Description=Run Kona DB backup daily at 07:20 Beijing

[Timer]
OnCalendar=*-*-* 23:20:00
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

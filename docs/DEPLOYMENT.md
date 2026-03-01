# Deployment

This project deploys the **backend** (kona_tool) via GitHub Actions.

> Current production (as of 2026-03-01): **Tencent Cloud Lighthouse**
> - Public entry: `http://114.132.238.12`
> - Runtime: `Nginx(80) -> Gunicorn(127.0.0.1:5003) -> Flask`
> - Data: `SQLite + Redis(localhost)`
>
> Detailed handover: `docs/README_HANDOVER_2026_03_TENCENT_MIGRATION.md`

---

## CI + CD Pipeline

- `pull_request -> main`:
  - Run `backend-gate` (compile + unit tests, Python 3.9/3.11)
  - Run `frontend-gate` (pub get + analyze + test + debug apk build)
  - **No deploy on PR**

- `push -> main`:
  - Run both gates above
  - Only if both pass, run `deploy`

- `workflow_dispatch`:
  - Also runs both gates first
  - Deploy starts only after gates pass

---

## Current Deployment Flow (Tencent Cloud)

1. Push to GitHub `main`
2. `backend-gate` and `frontend-gate` must both pass
3. GitHub Actions connects to target server via SSH
4. Pulls latest code in server app dir (current: `/opt/kaka/portfolio/kona_tool`)
5. Installs dependencies (including `gunicorn`)
6. Writes/updates `systemd` service (`kona.service`)
7. Restarts backend via `systemctl`
8. Performs health check

Workflow file:
```
.github/workflows/deploy.yml
```

---

## GitHub Secrets Required

- `SSH_HOST`: server public IP (current: `114.132.238.12`)
- `SSH_USER`: server SSH user (current: `root`)
- `SSH_KEY`: private SSH key
- `APP_DIR`: server app path (current: `/opt/kaka/portfolio/kona_tool`)

---

## Health Check

After restart, health check target:

```
http://127.0.0.1:5003/api/rates
```

If the response code is `200`, deployment is considered successful.

---

## Runtime (Current Production)

`kona.service` starts gunicorn:

```
/opt/kaka/portfolio/kona_tool/.venv/bin/gunicorn --workers 2 --threads 4 --bind 127.0.0.1:5003 --timeout 120 wsgi:app
```

Nginx proxies public traffic from port `80` to `127.0.0.1:5003`.

---

## Production Rate Limiting (Redis)

Current code supports `Flask-Limiter` with configurable backend:

```
RATELIMIT_STORAGE_URL
```

Recommended production setup:

```bash
sudo dnf install -y redis
sudo systemctl enable --now redis
sudo systemctl status redis -l
```

Set backend `.env`:

```bash
cd /opt/kaka/portfolio/kona_tool
grep '^RATELIMIT_STORAGE_URL=' .env || echo 'RATELIMIT_STORAGE_URL=redis://127.0.0.1:6379/0' >> .env
```

Restart backend:

```bash
sudo systemctl restart kona.service
sudo systemctl status kona.service -l
```

Quick verify:

```bash
redis-cli ping
curl -s http://127.0.0.1:5003/health
```

Expected:
- `redis-cli ping` returns `PONG`
- `/health` returns `{"status":"ok",...}`

---

## Alerting (Email)

Three alert channels are supported:

- `kona.service` boot/runtime failure -> instant email
- HTTP health check failure -> email (every 2 minutes probe)
- Daily snapshot missing -> email (07:05 Beijing)
- Price metrics degradation -> email (every 5 minutes threshold probe)

Alert scripts:

```
kona_tool/scripts/alert_sender.py
kona_tool/scripts/check_kona_health.py
kona_tool/scripts/check_daily_snapshot.py
kona_tool/scripts/check_price_health_alert.py
kona_tool/scripts/systemd_failure_notify.sh
kona_tool/scripts/install_alerting_systemd.sh
```

### 1) Configure `.env`

```bash
cd /home/ec2-user/portfolio/kona_tool
grep '^ALERT_NOTIFY_TO=' .env || echo 'ALERT_NOTIFY_TO=konaeee@gmail.com' >> .env
grep '^KONA_HEALTH_URL=' .env || echo 'KONA_HEALTH_URL=http://127.0.0.1:5003/health' >> .env
grep '^PRICE_HEALTH_URL=' .env || echo 'PRICE_HEALTH_URL=http://127.0.0.1:5003/api/system/price_health' >> .env
grep '^PRICE_HEALTH_NETWORK_FAIL_DELTA_THRESHOLD=' .env || echo 'PRICE_HEALTH_NETWORK_FAIL_DELTA_THRESHOLD=20' >> .env
grep '^PRICE_HEALTH_STALE_HITS_DELTA_THRESHOLD=' .env || echo 'PRICE_HEALTH_STALE_HITS_DELTA_THRESHOLD=30' >> .env
grep '^PRICE_HEALTH_SOURCE_CONSEC_FAIL_THRESHOLD=' .env || echo 'PRICE_HEALTH_SOURCE_CONSEC_FAIL_THRESHOLD=5' >> .env
```

### 2) Install systemd alert units/timers

```bash
cd /home/ec2-user/portfolio/kona_tool
chmod +x scripts/install_alerting_systemd.sh
bash scripts/install_alerting_systemd.sh
```

### 3) Verify

```bash
sudo systemctl list-timers | grep -E 'kona-(healthcheck|snapshot-verify|snapshot)'
sudo systemctl status kona -l
```

Optional verify (price-health checker):

```bash
sudo systemctl start kona-price-health-alert.service
sudo journalctl -u kona-price-health-alert.service -n 50 --no-pager
```

### 4) Send a manual test email

```bash
cd /home/ec2-user/portfolio/kona_tool
python3 scripts/alert_sender.py \
  --subject "[Kona][Test] alert channel ok" \
  --body "If you received this email, alerting is configured correctly."
```

---

## Log Rotation

Script:
```
/home/ec2-user/portfolio/kona_tool/rotate_log.sh
```

Cron schedule (weekly, Monday 2:00 AM):
```
0 2 * * 1 /home/ec2-user/portfolio/kona_tool/rotate_log.sh
```

Logs are stored in:
```
kona_tool/archive/logs/
```

---

## DB Backup & Restore (SQLite)

Goal:
- automatic daily compressed backup
- retention cleanup
- one-command restore from latest backup

Scripts:
```
kona_tool/scripts/backup_portfolio_db.py
kona_tool/scripts/restore_portfolio_db.py
kona_tool/scripts/install_backup_systemd.sh
```

### 1) Configure backup env

```bash
cd /home/ec2-user/portfolio/kona_tool
grep '^KONA_BACKUP_DIR=' .env || echo 'KONA_BACKUP_DIR=/home/ec2-user/portfolio/kona_tool/archive/backups' >> .env
grep '^KONA_BACKUP_RETENTION_DAYS=' .env || echo 'KONA_BACKUP_RETENTION_DAYS=14' >> .env
```

### 2) Install daily backup timer

```bash
cd /home/ec2-user/portfolio/kona_tool
chmod +x scripts/install_backup_systemd.sh
bash scripts/install_backup_systemd.sh
sudo systemctl start kona-db-backup.service
sudo systemctl list-timers | grep kona-db-backup
```

Schedule:
- `kona-db-backup.timer` runs daily at `23:20 UTC` (`07:20 Beijing`)

### 3) Manual backup

```bash
cd /home/ec2-user/portfolio/kona_tool
python3 scripts/backup_portfolio_db.py
ls -lt archive/backups | head
```

### 4) Restore drill (latest backup)

```bash
cd /home/ec2-user/portfolio/kona_tool
sudo systemctl stop kona
python3 scripts/restore_portfolio_db.py
sudo systemctl start kona
curl -s http://127.0.0.1:5003/health
```

Notes:
- restore script creates a safety copy: `portfolio.db.pre_restore_<UTC timestamp>`
- restore source defaults to latest `portfolio_*.db.gz` in `KONA_BACKUP_DIR`

---

## Refresh Token Cleanup (Auth)

Goal:
- keep `auth_refresh_tokens` table compact
- retain expired token records for security troubleshooting (default 90 days)

Script:
```
kona_tool/scripts/cleanup_refresh_tokens.py
```

### 1) Configure retention env

```bash
cd /home/ec2-user/portfolio/kona_tool
grep '^AUTH_REFRESH_TOKEN_RETENTION_DAYS=' .env || echo 'AUTH_REFRESH_TOKEN_RETENTION_DAYS=90' >> .env
```

### 2) Manual cleanup

```bash
cd /home/ec2-user/portfolio/kona_tool
python3 scripts/cleanup_refresh_tokens.py
```

### 3) Daily schedule (cron example)

```bash
crontab -l > /tmp/kona.cron 2>/dev/null || true
grep -q "cleanup_refresh_tokens.py" /tmp/kona.cron || \
  echo "35 23 * * * cd /home/ec2-user/portfolio/kona_tool && /usr/bin/python3 scripts/cleanup_refresh_tokens.py >> /home/ec2-user/portfolio/kona_tool/archive/logs/refresh_cleanup.log 2>&1" >> /tmp/kona.cron
crontab /tmp/kona.cron
rm -f /tmp/kona.cron
```

Schedule:
- daily at `23:35 UTC` (`07:35 Beijing`)

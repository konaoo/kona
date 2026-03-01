# Maintenance Guide

This guide covers routine maintenance, backups, and troubleshooting.

---

## Service Status

Check services:
```
sudo systemctl status kona.service --no-pager
sudo systemctl status caddy --no-pager
sudo systemctl status redis --no-pager
```

Health check:
```
http://114.132.238.12/health
```

---

## Log Rotation

Script:
```
/opt/kaka/portfolio/kona_tool/rotate_log.sh
```

Schedule:
```
0 2 * * 1 /opt/kaka/portfolio/kona_tool/rotate_log.sh
```

Logs are stored in:
```
kona_tool/archive/logs/
```

---

## Daily Snapshot (Beijing 07:00)

Script:
```
/opt/kaka/portfolio/kona_tool/scripts/daily_snapshot.sh
```

Crontab (Beijing time):
```
CRON_TZ=Asia/Shanghai
0 7 * * * /opt/kaka/portfolio/kona_tool/scripts/daily_snapshot.sh
```

If your system does not support `CRON_TZ`, use UTC:
```
0 23 * * * /opt/kaka/portfolio/kona_tool/scripts/daily_snapshot.sh
```

---

## Database Backup

Database file:
```
kona_tool/portfolio.db
```

Recommended backup:
```
cp kona_tool/portfolio.db kona_tool/archive/db/portfolio_$(date +%Y%m%d_%H%M%S).db
```

---

## Deployment Troubleshooting

If GitHub Actions fails:
- Check `Actions` logs in GitHub
- Confirm secrets `SSH_HOST`, `SSH_KEY`, `APP_DIR`
- Verify Tencent firewall allows SSH (port 22) and HTTP (port 80)

Common deploy error (`git fetch ... Empty reply from server`):
```bash
# run on server
cd "$APP_DIR"
git -c http.version=HTTP/1.1 fetch --depth=1 origin main
curl -I https://github.com
```
If both fail, check server outbound network to `github.com:443`.

---

## API Troubleshooting

If frontend cannot reach API:
- Confirm Flutter base URL in `flutter/lib/config/api_config.dart`
- Confirm `caddy` is running and `http://114.132.238.12/health` is reachable
- Confirm `kona.service` still binds `127.0.0.1:5003` internally

---

## Safe Cleanup

Archived folders:
- `kona_tool/archive/old_files`

Do not delete without backup:
- `kona_tool/portfolio.db`

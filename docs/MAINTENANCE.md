# Maintenance Guide

This guide covers routine maintenance, backups, and troubleshooting.

---

## Service Status

Check if backend is running:
```
ps -ef | grep "python3 app.py"
```

Health check:
```
http://<server-ip>:5003/api/rates
```

---

## Log Rotation

Script:
```
/home/ec2-user/portfolio/kona_tool/rotate_log.sh
```

Schedule:
```
0 2 * * 1 /home/ec2-user/portfolio/kona_tool/rotate_log.sh
```

Logs are stored in:
```
kona_tool/archive/logs/
```

---

## Daily Snapshot (Beijing 07:00)

Script:
```
/home/ec2-user/portfolio/kona_tool/scripts/daily_snapshot.sh
```

Crontab (Beijing time):
```
CRON_TZ=Asia/Shanghai
0 7 * * * /home/ec2-user/portfolio/kona_tool/scripts/daily_snapshot.sh
```

If your system does not support `CRON_TZ`, use UTC:
```
0 23 * * * /home/ec2-user/portfolio/kona_tool/scripts/daily_snapshot.sh
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
- Confirm secrets `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `APP_DIR`
- Verify AWS security group allows SSH (port 22)

---

## API Troubleshooting

If frontend cannot reach API:
- Confirm Flutter base URL in `flutter/lib/config/api_config.dart`
- Confirm backend is running on port `5003`

---

## Safe Cleanup

Archived folders:
- `archive/HI`
- `kona_tool/archive/old_files`

Do not delete without backup:
- `kona_tool/portfolio.db`

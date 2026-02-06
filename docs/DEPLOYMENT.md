# Deployment

This project deploys the **backend** (kona_tool) to AWS using GitHub Actions.

---

## Current Deployment Flow

1. Push to GitHub `main`
2. GitHub Actions connects to AWS via SSH
3. Pulls latest code in `/home/ec2-user/portfolio/kona_tool`
4. Installs dependencies (including `gunicorn`)
5. Writes/updates `systemd` service (`kona.service`)
6. Restarts backend via `systemctl`
7. Performs health check

Workflow file:
```
.github/workflows/deploy.yml
```

---

## GitHub Secrets Required

- `SSH_HOST`: AWS public IP
- `SSH_USER`: `ec2-user`
- `SSH_KEY`: private SSH key
- `APP_DIR`: `/home/ec2-user/portfolio/kona_tool`

---

## Health Check

After restart, the workflow checks:

```
http://127.0.0.1:5003/api/rates
```

If the response code is `200`, deployment is considered successful.

---

## AWS Runtime

The backend is started by `systemd` using `gunicorn`:

```
/home/ec2-user/.local/bin/gunicorn --workers 1 --threads 4 --bind 0.0.0.0:5003 --timeout 120 wsgi:app
```

Service name:
```
kona.service
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

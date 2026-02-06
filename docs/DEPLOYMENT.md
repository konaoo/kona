# Deployment

This project deploys the **backend** (kona_tool) to AWS using GitHub Actions.

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

## Current Deployment Flow

1. Push to GitHub `main`
2. `backend-gate` and `frontend-gate` must both pass
3. GitHub Actions connects to AWS via SSH
4. Pulls latest code in `/home/ec2-user/portfolio/kona_tool`
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

# Deployment

This project deploys the **backend** (kona_tool) to AWS using GitHub Actions.

---

## Current Deployment Flow

1. Push to GitHub `main`
2. GitHub Actions connects to AWS via SSH
3. Pulls latest code in `/home/ec2-user/portfolio/kona_tool`
4. Installs dependencies
5. Restarts backend and performs health check

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

The backend is started with:

```
python3 app.py
```

The workflow writes the PID to `app.pid` and uses it for safe restarts.

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

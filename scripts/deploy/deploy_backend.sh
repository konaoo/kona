#!/usr/bin/env bash

set -euo pipefail

APP_DIR="${APP_DIR:-}"
TARGET_SHA="${TARGET_SHA:-}"
DEPLOY_BUNDLE="${DEPLOY_BUNDLE:-}"

if [ -z "$APP_DIR" ] || [ ! -d "$APP_DIR" ]; then
  echo "Invalid APP_DIR: $APP_DIR"
  exit 1
fi
if [ -z "$TARGET_SHA" ]; then
  echo "Missing TARGET_SHA."
  exit 1
fi

cd "$APP_DIR"
echo "Deploy dir: $(pwd)"
echo "Deploy target sha: $TARGET_SHA"
git config --global --add safe.directory "$APP_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $APP_DIR is not a git repository."
  exit 1
fi

CURRENT_SHA="$(git rev-parse HEAD)"
echo "Server current sha: $CURRENT_SHA"

fetch_main_with_timeout() {
  attempt="$1"
  fetch_log="/tmp/kona_deploy_git_fetch_${attempt}.log"
  rm -f "$fetch_log"
  echo "git fetch attempt $attempt ..."
  if timeout 300 git -c http.version=HTTP/1.1 fetch origin main >"$fetch_log" 2>&1; then
    cat "$fetch_log" || true
    rm -f "$fetch_log"
    return 0
  fi
  status="$?"
  echo "git fetch attempt $attempt failed with exit code: $status"
  cat "$fetch_log" || true
  rm -f "$fetch_log"
  return 1
}

FETCH_OK=0
if [ "$CURRENT_SHA" = "$TARGET_SHA" ]; then
  FETCH_OK=1
  echo "Server already at target sha, skip git fetch."
else
  if [ -n "$DEPLOY_BUNDLE" ] && [ -f "$DEPLOY_BUNDLE" ]; then
    echo "Using deploy bundle: $DEPLOY_BUNDLE"
    if git fetch "$DEPLOY_BUNDLE" HEAD:refs/remotes/bundle/main; then
      BUNDLE_SHA="$(git rev-parse refs/remotes/bundle/main)"
      echo "Fetched bundle/main sha: $BUNDLE_SHA"
      if git cat-file -e "$TARGET_SHA^{commit}"; then
        FETCH_OK=1
      else
        echo "Bundle does not contain target sha."
      fi
    fi
  fi

  if [ "$FETCH_OK" -ne 1 ]; then
    for attempt in 1 2 3; do
      if fetch_main_with_timeout "$attempt"; then
        REMOTE_SHA="$(git rev-parse origin/main)"
        echo "Fetched origin/main sha: $REMOTE_SHA"
        if [ "$REMOTE_SHA" = "$TARGET_SHA" ]; then
          FETCH_OK=1
          break
        fi
        echo "Fetched sha does not match target sha yet, wait and retry."
      fi
      sleep $((attempt * 2))
    done
  fi
fi

if [ "$FETCH_OK" -ne 1 ]; then
  echo "ERROR: git fetch origin main failed or target sha not reached."
  git remote -v || true
  git branch -vv || true
  git status --short --branch --untracked-files=no || true
  timeout 15 git ls-remote origin refs/heads/main || true
  timeout 15 curl -I https://github.com || true
  exit 1
fi

if [ "$CURRENT_SHA" != "$TARGET_SHA" ]; then
  if ! git reset --hard "$TARGET_SHA"; then
    echo "Target sha not present locally, reset to origin/main."
    git reset --hard origin/main
  fi
fi

echo "Server git status after reset:"
git log -1 --oneline

PYTHON_BIN="python3"
IS_VENV=0
if [ -f "kona_tool/.venv/bin/python3" ]; then
  PYTHON_BIN="kona_tool/.venv/bin/python3"
  IS_VENV=1
fi

if [ "$IS_VENV" -eq 1 ]; then
  "$PYTHON_BIN" -m pip install -r kona_tool/requirements.txt
else
  "$PYTHON_BIN" -m pip install -r kona_tool/requirements.txt --user
fi

sudo systemctl restart kona
echo "Systemd service kona restarted."

i=1
while [ "$i" -le 60 ]; do
  status=$(curl -sS -o /tmp/kona_health.json -w "%{http_code}" --max-time 2 http://127.0.0.1:5003/health || true)
  echo "health attempt $i -> $status"
  if [ "$status" = "200" ]; then
    cat /tmp/kona_health.json || true
    echo
    echo "Health check passed."
    break
  fi
  i=$((i + 1))
  sleep 1
done

if [ "$i" -gt 60 ]; then
  echo "Health check failed after restart."
  sudo systemctl status kona -l --no-pager || true
  sudo journalctl -u kona -n 120 --no-pager || true
  exit 1
fi

echo "Running backend deploy smoke checks..."
web_root=$(curl -sS -o /tmp/kona_web_root.html -w "%{http_code}" --max-time 3 http://127.0.0.1:5003/ || true)
app_login=$(curl -sS -o /tmp/kona_app_login.html -w "%{http_code}" --max-time 3 http://127.0.0.1:5003/app/login || true)
admin_login=$(curl -sS -o /tmp/kona_admin_login.html -w "%{http_code}" --max-time 3 http://127.0.0.1:5003/admin/login || true)
market_status=$(curl -sS -o /tmp/kona_market_status.json -w "%{http_code}" --max-time 5 http://127.0.0.1:5003/api/market/status || true)
login_status=$(curl -sS -o /tmp/kona_login_probe.json -w "%{http_code}" --max-time 3 \
  -H 'Content-Type: application/json' \
  -X POST 'http://127.0.0.1:5003/api/auth/login' \
  --data '{"username":"ci_probe_user","password":"ci_probe_bad_password"}' || true)

echo "web root -> $web_root"
echo "app login -> $app_login"
echo "admin login -> $admin_login"
echo "market status -> $market_status"
echo "login probe -> $login_status"

if [ "$web_root" != "200" ] || [ "$app_login" != "200" ] || [ "$admin_login" != "200" ]; then
  echo "ERROR: backend deploy smoke failed."
  exit 1
fi
if [ "$market_status" != "200" ]; then
  echo "ERROR: /api/market/status unexpected status: $market_status"
  cat /tmp/kona_market_status.json || true
  exit 1
fi
if [ "$login_status" != "401" ]; then
  echo "ERROR: /api/auth/login probe unexpected status: $login_status"
  cat /tmp/kona_login_probe.json || true
  exit 1
fi

python3 -c "import json; data=json.load(open('/tmp/kona_market_status.json','r',encoding='utf-8')); required=['server_time_utc','markets','all_closed']; missing=[k for k in required if k not in data]; assert not missing, f'missing keys in /api/market/status: {missing}'; print('market status payload OK')"
python3 -c "import json; data=json.load(open('/tmp/kona_login_probe.json','r',encoding='utf-8')); assert 'error' in data, 'missing error field in /api/auth/login probe response'; print('login probe payload OK')"
echo "Backend deploy smoke checks passed."

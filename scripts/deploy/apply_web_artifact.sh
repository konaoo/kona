#!/usr/bin/env bash

set -euo pipefail

APP_DIR="${APP_DIR:-}"
REMOTE_WEB_ARCHIVE="${REMOTE_WEB_ARCHIVE:-}"

if [ -z "$APP_DIR" ] || [ ! -d "$APP_DIR" ]; then
  echo "Invalid APP_DIR: $APP_DIR"
  exit 1
fi
if [ -z "$REMOTE_WEB_ARCHIVE" ]; then
  echo "Missing REMOTE_WEB_ARCHIVE."
  exit 1
fi

WEB_DIR="$APP_DIR/kona_tool/static/web"
if [ ! -d "$APP_DIR/kona_tool" ]; then
  WEB_DIR="$APP_DIR/static/web"
fi
echo "Static web target: $WEB_DIR"

if [ ! -f "$REMOTE_WEB_ARCHIVE" ]; then
  echo "Missing $REMOTE_WEB_ARCHIVE"
  exit 1
fi
if ! gzip -t "$REMOTE_WEB_ARCHIVE"; then
  echo "Invalid gzip archive: $REMOTE_WEB_ARCHIVE"
  exit 1
fi

TMP_WEB_DIR="$(mktemp -d)"
tar -xzf "$REMOTE_WEB_ARCHIVE" -C "$TMP_WEB_DIR"
rm -f "$REMOTE_WEB_ARCHIVE"

BACKUP_WEB_DIR="${WEB_DIR}.bak.$(date +%s)"
if [ -d "$WEB_DIR" ]; then
  cp -a "$WEB_DIR" "$BACKUP_WEB_DIR"
fi

rollback_web() {
  if [ -d "$BACKUP_WEB_DIR" ]; then
    echo "Rolling back web artifact from $BACKUP_WEB_DIR ..."
    rm -rf "$WEB_DIR"
    cp -a "$BACKUP_WEB_DIR" "$WEB_DIR"
  else
    echo "No web backup directory found, skip rollback."
  fi
}

rm -rf "$WEB_DIR"
mkdir -p "$WEB_DIR"
cp -a "$TMP_WEB_DIR"/. "$WEB_DIR"/
rm -rf "$TMP_WEB_DIR"
echo "Frontend assets updated in $WEB_DIR"

web_root=$(curl -sS -o /tmp/kona_web_root.html -w "%{http_code}" --max-time 3 http://127.0.0.1:5003/ || true)
app_login=$(curl -sS -o /tmp/kona_app_login.html -w "%{http_code}" --max-time 3 http://127.0.0.1:5003/app/login || true)
admin_login=$(curl -sS -o /tmp/kona_admin_login.html -w "%{http_code}" --max-time 3 http://127.0.0.1:5003/admin/login || true)
echo "web root -> $web_root"
echo "app login -> $app_login"
echo "admin login -> $admin_login"

if [ "$web_root" != "200" ] || [ "$app_login" != "200" ] || [ "$admin_login" != "200" ]; then
  echo "ERROR: web deploy smoke failed."
  rollback_web
  exit 1
fi

echo "Web deploy smoke checks passed."

#!/usr/bin/env bash

set -euo pipefail

SSH_HOST="${SSH_HOST:-}"
SSH_PRIVATE_KEY="${SSH_PRIVATE_KEY:-}"
REMOTE_WEB_ARCHIVE="${REMOTE_WEB_ARCHIVE:-}"
WEB_ARCHIVE="${WEB_ARCHIVE:-/tmp/kona-web-artifact/web-dist.tar.gz}"

if [ -z "$SSH_HOST" ] || [ -z "$SSH_PRIVATE_KEY" ]; then
  echo "Missing SSH_HOST or SSH_KEY secret."
  exit 1
fi
if [ -z "$REMOTE_WEB_ARCHIVE" ]; then
  echo "Missing REMOTE_WEB_ARCHIVE."
  exit 1
fi
if [ ! -f "$WEB_ARCHIVE" ]; then
  echo "Missing downloaded web archive: $WEB_ARCHIVE"
  exit 1
fi

KEY_FILE="$RUNNER_TEMP/deploy_key"
printf '%s\n' "$SSH_PRIVATE_KEY" > "$KEY_FILE"
chmod 600 "$KEY_FILE"

SSH_OPTS="-i $KEY_FILE -o BatchMode=yes -o PreferredAuthentications=publickey -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 -o ConnectionAttempts=2 -o ServerAliveInterval=15 -o ServerAliveCountMax=3"

run_ssh() {
  timeout 25 ssh $SSH_OPTS root@"$SSH_HOST" "$@"
}

WARMUP_OK=0
for attempt in 1 2; do
  echo "SSH warmup attempt $attempt ..."
  if run_ssh "echo warmup-ok" >/dev/null 2>&1; then
    WARMUP_OK=1
    break
  fi
  sleep 2
done
if [ "$WARMUP_OK" -ne 1 ]; then
  echo "SSH warmup failed after retries."
  exit 1
fi

SCP_OK=0
LOCAL_SHA="$(sha256sum "$WEB_ARCHIVE" | awk '{print $1}')"
REMOTE_TMP_ARCHIVE="${REMOTE_WEB_ARCHIVE}.part"
for attempt in 1 2 3; do
  echo "SCP attempt $attempt ..."
  run_ssh "rm -f '$REMOTE_TMP_ARCHIVE' '$REMOTE_WEB_ARCHIVE'" >/dev/null 2>&1 || true
  if timeout 90 scp $SSH_OPTS "$WEB_ARCHIVE" root@"$SSH_HOST":"$REMOTE_TMP_ARCHIVE" && \
    run_ssh "set -eu
      actual_sha=\$(sha256sum '$REMOTE_TMP_ARCHIVE' | awk '{print \$1}')
      [ \"\$actual_sha\" = '$LOCAL_SHA' ]
      gzip -t '$REMOTE_TMP_ARCHIVE'
      mv '$REMOTE_TMP_ARCHIVE' '$REMOTE_WEB_ARCHIVE'
    "; then
    echo "Remote artifact verified: $REMOTE_WEB_ARCHIVE"
    SCP_OK=1
    break
  fi
  run_ssh "rm -f '$REMOTE_TMP_ARCHIVE'" >/dev/null 2>&1 || true
  sleep $((attempt * 2))
done
if [ "$SCP_OK" -ne 1 ]; then
  echo "SCP upload or remote artifact verification failed after retries."
  exit 1
fi

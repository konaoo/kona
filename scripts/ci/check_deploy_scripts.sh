#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

for script in scripts/deploy/*.sh; do
  bash -n "$script"
done

expect_failure() {
  label="$1"
  shift

  set +e
  "$@" >/tmp/kona_deploy_script_check.out 2>&1
  status="$?"
  set -e

  if [ "$status" -eq 0 ]; then
    echo "Expected failure but command succeeded: $label"
    cat /tmp/kona_deploy_script_check.out || true
    exit 1
  fi
}

expect_failure "deploy_backend requires APP_DIR" env -i bash scripts/deploy/deploy_backend.sh
expect_failure "upload_web_artifact requires SSH settings" env -i RUNNER_TEMP=/tmp bash scripts/deploy/upload_web_artifact.sh
expect_failure "apply_web_artifact requires APP_DIR" env -i bash scripts/deploy/apply_web_artifact.sh

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir" /tmp/kona_deploy_script_check.out' EXIT

app_dir="$tmp_dir/app"
web_dir="$app_dir/kona_tool/static/web"
archive_dir="$tmp_dir/archive"
artifact_src="$tmp_dir/artifact-src"
fake_bin="$tmp_dir/bin"

mkdir -p "$web_dir" "$archive_dir" "$artifact_src" "$fake_bin"
printf 'old web\n' > "$web_dir/index.html"
printf 'new web\n' > "$artifact_src/index.html"
tar -C "$artifact_src" -czf "$tmp_dir/web-dist.tar.gz" .

for idx in 1 2 3 4 5 6 7; do
  backup_dir="$app_dir/kona_tool/static/web.bak.$idx"
  mkdir -p "$backup_dir"
  printf 'backup %s\n' "$idx" > "$backup_dir/index.html"
  touch -t "20260501010${idx}.00" "$backup_dir"
done

cat > "$fake_bin/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

output_file=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o)
      output_file="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [ -n "$output_file" ]; then
  printf 'ok\n' > "$output_file"
fi
printf '200'
EOF
chmod +x "$fake_bin/curl"

APP_DIR="$app_dir" \
REMOTE_WEB_ARCHIVE="$tmp_dir/web-dist.tar.gz" \
WEB_BACKUP_ARCHIVE_ROOT="$archive_dir" \
WEB_BACKUP_KEEP=5 \
PATH="$fake_bin:$PATH" \
  bash scripts/deploy/apply_web_artifact.sh

remaining_count="$(find "$app_dir/kona_tool/static" -maxdepth 1 -type d -name 'web.bak.*' | wc -l | tr -d ' ')"
archived_count="$(find "$archive_dir" -mindepth 2 -maxdepth 2 -type d -name 'web.bak.*' | wc -l | tr -d ' ')"

if [ "$remaining_count" != "5" ]; then
  echo "Expected 5 retained web backups, got $remaining_count"
  find "$app_dir/kona_tool/static" -maxdepth 1 -type d -name 'web.bak.*' | sort
  exit 1
fi

if [ "$archived_count" != "3" ]; then
  echo "Expected 3 archived web backups, got $archived_count"
  find "$archive_dir" -type d | sort
  exit 1
fi

if ! grep -q 'new web' "$web_dir/index.html"; then
  echo "Expected deployed web artifact to replace old index.html"
  exit 1
fi

echo "部署脚本检查通过：语法、缺参失败和 Web 备份归档行为正常。"

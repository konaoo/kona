#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

base_ref="${1:-${CI_BASE_SHA:-}}"
head_ref="${2:-${CI_HEAD_SHA:-HEAD}}"

if [ -z "$base_ref" ]; then
  if git rev-parse --verify HEAD^ >/dev/null 2>&1; then
    base_ref="HEAD^"
  else
    echo "未提供比较基线，且当前仓库没有上一个提交，跳过 CHANGELOG 守门。"
    exit 0
  fi
fi

if [ "$base_ref" = "0000000000000000000000000000000000000000" ]; then
  if git rev-parse --verify HEAD^ >/dev/null 2>&1; then
    base_ref="HEAD^"
  else
    echo "基线是空提交，当前无法可靠比较，跳过 CHANGELOG 守门。"
    exit 0
  fi
fi

changed_files="$(git diff --name-only "$base_ref" "$head_ref" || true)"

if [ -z "$changed_files" ]; then
  echo "这次没有检测到文件改动，跳过 CHANGELOG 守门。"
  exit 0
fi

if printf '%s\n' "$changed_files" | grep -Eq '^CHANGELOG\.md$'; then
  echo "CHANGELOG 守门通过：本次改动已包含 CHANGELOG.md。"
  exit 0
fi

impactful_files="$(
  printf '%s\n' "$changed_files" \
    | grep -E '^(web/|flutter/|kona_tool/|\.github/workflows/|scripts/ci/|\.gitignore$)' \
    | grep -Ev '(^web/tests/|^kona_tool/tests/|^flutter/test/|(^|/)(README[^/]*\.md)$|^docs/)' \
    || true
)"

if [ -n "$impactful_files" ]; then
  echo "检测到重要工程或业务改动，但这次没有更新 CHANGELOG.md："
  echo "$impactful_files"
  echo
  echo "请补一条版本记录，说明改了什么、影响哪里、验收看什么。"
  exit 1
fi

echo "CHANGELOG 守门通过：本次改动仅涉及文档、测试或说明文件。"

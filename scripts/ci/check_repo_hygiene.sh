#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

forbidden_regex='(^|/)(__pycache__/|\.pytest_cache/|\.dart_tool/|node_modules(\.old\.[^/]+)?/|test-results/)|^web/dist/|^web/dev\.log$|^flutter/build/|^flutter/android/build/|^kona_tool/portfolio\.db$'

matches="$(git ls-files | grep -E "$forbidden_regex" || true)"

if [ -n "$matches" ]; then
  echo "发现不该被 Git 跟踪的生成物、缓存或本地数据文件："
  echo "$matches"
  echo
  echo "请把这些文件移出版本控制，或补充忽略规则后再提交。"
  exit 1
fi

echo "仓库卫生检查通过：未发现被 Git 跟踪的构建产物、缓存或本地数据库。"

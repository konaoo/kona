#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "清理构建产物与本地临时文件..."

rm -rf "$ROOT_DIR/web/dist"
rm -rf "$ROOT_DIR/web/test-results"
rm -rf "$ROOT_DIR/kona_tool/static/web"
rm -rf "$ROOT_DIR/flutter/build"
rm -rf "$ROOT_DIR/flutter/.dart_tool"

echo "完成。"

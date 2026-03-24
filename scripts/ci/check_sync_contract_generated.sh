#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/generate_sync_contracts.py

if ! git diff --exit-code -- \
  web/src/stores/generated_sync_contract.ts \
  flutter/lib/providers/generated_sync_contract.dart
then
  echo
  echo "sync 协议生成文件不是最新。"
  echo "请先执行：python3 scripts/generate_sync_contracts.py"
  exit 1
fi

echo "sync 协议生成检查通过。"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCHEMA_FILE="${ROOT_DIR}/docs/openapi.yaml"
OUT_DIR="${ROOT_DIR}/flutter/lib/generated/openapi"

if ! command -v npx >/dev/null 2>&1; then
  echo "未找到 npx，请先安装 Node.js 环境。"
  exit 1
fi

if ! java -version >/dev/null 2>&1; then
  echo "未找到 Java 运行环境，Flutter OpenAPI 类型暂时无法生成。"
  echo "请先安装 Java，再执行 scripts/generate_openapi_types_flutter.sh"
  exit 1
fi

echo "使用 openapi-generator 生成 Flutter API 类型（需要 Java 环境）。"
echo "输出目录：${OUT_DIR}"

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

npx --yes @openapitools/openapi-generator-cli generate \
  -i "${SCHEMA_FILE}" \
  -g dart \
  -o "${OUT_DIR}" \
  --additional-properties=pubName=kaka_openapi,pubVersion=0.0.0,nullableFields=true

#!/usr/bin/env python3
"""
从 kona_tool.sync_contract 生成 Web / Flutter 使用的同步协议常量文件。
"""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "kona_tool") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "kona_tool"))

from sync_contract import (  # noqa: E402
    AUTH_BOOTSTRAP_TIMEOUT_MS,
    QUOTE_POLICY_DEFAULT,
    SYNC_BOOTSTRAP_DOMAINS,
    SYNC_BOOTSTRAP_QUOTE_INCLUDE,
    WEB_CACHE_TTL_MS,
)


WEB_TARGET = REPO_ROOT / "web/src/stores/generated_sync_contract.ts"
FLUTTER_TARGET = REPO_ROOT / "flutter/lib/providers/generated_sync_contract.dart"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_web_contract() -> str:
    domains = ", ".join(f"'{item}'" for item in SYNC_BOOTSTRAP_DOMAINS)
    quote_include = ", ".join(f"'{item}'" for item in SYNC_BOOTSTRAP_QUOTE_INCLUDE)
    return f"""// 由 scripts/generate_sync_contracts.py 自动生成，不要手改。

export const GENERATED_SYNC_BOOTSTRAP_DOMAINS = [{domains}] as const

export type GeneratedSyncDomain = typeof GENERATED_SYNC_BOOTSTRAP_DOMAINS[number]

export const GENERATED_SYNC_BOOTSTRAP_QUOTE_INCLUDE = [{quote_include}] as const

export const GENERATED_QUOTE_POLICY_DEFAULT = {{
  interval_open_sec: {QUOTE_POLICY_DEFAULT['interval_open_sec']},
  interval_closed_sec: {QUOTE_POLICY_DEFAULT['interval_closed_sec']},
  interval_us_extended_sec: {QUOTE_POLICY_DEFAULT['interval_us_extended_sec']},
}} as const

export const GENERATED_WEB_CACHE_TTL_MS = {{
  STATIC: {WEB_CACHE_TTL_MS['static']},
  QUOTES: {WEB_CACHE_TTL_MS['quotes']},
}} as const

export const GENERATED_AUTH_BOOTSTRAP_TIMEOUT_MS = {AUTH_BOOTSTRAP_TIMEOUT_MS}
"""


def build_flutter_contract() -> str:
    domains = ",\n  ".join(f"'{item}'" for item in SYNC_BOOTSTRAP_DOMAINS)
    quote_include = ",\n  ".join(f"'{item}'" for item in SYNC_BOOTSTRAP_QUOTE_INCLUDE)
    return f"""// 由 scripts/generate_sync_contracts.py 自动生成，不要手改。

const List<String> generatedSyncBootstrapDomains = <String>[
  {domains},
];

const List<String> generatedSyncBootstrapQuoteInclude = <String>[
  {quote_include},
];

const Map<String, int> generatedQuotePolicyDefault = <String, int>{{
  'interval_open_sec': {QUOTE_POLICY_DEFAULT['interval_open_sec']},
  'interval_closed_sec': {QUOTE_POLICY_DEFAULT['interval_closed_sec']},
  'interval_us_extended_sec': {QUOTE_POLICY_DEFAULT['interval_us_extended_sec']},
}};

const int generatedAuthBootstrapTimeoutMs = {AUTH_BOOTSTRAP_TIMEOUT_MS};
"""


def main() -> None:
    _write(WEB_TARGET, build_web_contract())
    _write(FLUTTER_TARGET, build_flutter_contract())


if __name__ == "__main__":
    main()

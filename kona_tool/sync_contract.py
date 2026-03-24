"""
同步协议单一来源。

规则：
- 后端是真实来源；
- Web / Flutter 的常量文件由脚本生成；
- 以后改同步域、缓存 TTL、默认 quote policy，不要再三端各改一遍。
"""

from __future__ import annotations

SYNC_BOOTSTRAP_DOMAINS: tuple[str, ...] = (
    "portfolio",
    "cash_assets",
    "other_assets",
    "liabilities",
    "history",
    "overview_all",
    "rates",
)

SYNC_BOOTSTRAP_QUOTE_INCLUDE: tuple[str, ...] = (
    "portfolio",
    "rates",
)

QUOTE_POLICY_DEFAULT: dict[str, int] = {
    "interval_open_sec": 5,
    "interval_closed_sec": 120,
    "interval_us_extended_sec": 10,
}

WEB_CACHE_TTL_MS: dict[str, int] = {
    "static": 5 * 60_000,
    "quotes": 60_000,
}

AUTH_BOOTSTRAP_TIMEOUT_MS = 2500

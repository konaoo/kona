"""
日收益归属日工具。

统一解决两类问题：
1. 美股夜盘在北京时间跨日后，收益仍应归到美股本地交易日。
2. 场外基金拿到 T+1 净值后，收益应归到净值对应日，而不是发布日。
"""

from datetime import date, datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

try:
    from .market_calendar import get_previous_trading_day, is_trading_day
except ImportError:  # pragma: no cover
    from core.market_calendar import get_previous_trading_day, is_trading_day

MARKET_TIMEZONES = {
    "a": "Asia/Shanghai",
    "hk": "Asia/Hong_Kong",
    "us": "America/New_York",
    "fund": "Asia/Shanghai",
}

SERVER_TIMEZONE = ZoneInfo("Asia/Shanghai")


def normalize_date_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    return raw[:10]


def market_local_date(market: str, now_utc: datetime) -> date:
    tz_name = MARKET_TIMEZONES.get(str(market or "").lower(), "UTC")
    return now_utc.astimezone(ZoneInfo(tz_name)).date()


def parse_server_local_datetime(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=SERVER_TIMEZONE)
    except Exception:
        return None


def effective_date_from_transaction_time(raw_time: Any, market: str) -> Optional[str]:
    dt = parse_server_local_datetime(raw_time)
    if dt is None:
        return None
    try:
        local_date = dt.astimezone(ZoneInfo(MARKET_TIMEZONES.get(str(market or "").lower(), "UTC"))).date()
    except Exception:
        return None
    return local_date.strftime("%Y-%m-%d")


def resolve_exchange_effective_date(
    *,
    market: str,
    now_utc: datetime,
    current_price: float,
    yclose: float,
    market_trading_day: bool,
    epsilon: float = 1e-9,
) -> Optional[str]:
    """
    给交易所资产计算“这笔日收益该归到哪一天”。

    规则：
    - 当前还是本地交易日：归到本地日期
    - 当前不是本地交易日，但价格里仍带着上一交易日的日变化：归到前一个交易日
    - 没有有效日变化：不归属
    """
    if current_price <= 0 or yclose <= 0:
        return None
    if abs(current_price - yclose) / yclose < epsilon:
        return None

    local_date = market_local_date(market, now_utc)
    if market_trading_day:
        return local_date.strftime("%Y-%m-%d")

    previous_day = get_previous_trading_day(market, local_date)
    if previous_day is None:
        return None
    return previous_day.strftime("%Y-%m-%d")


def resolve_fund_nav_effective_date(latest_nav_date: Any) -> Optional[str]:
    return normalize_date_str(latest_nav_date)


def is_effective_trading_date(market: str, date_str: Any) -> bool:
    normalized = normalize_date_str(date_str)
    if not normalized:
        return False
    try:
        return bool(is_trading_day(market, normalized))
    except Exception:
        return False

"""
市场交易日历模块。
统一提供 A/HK/US/Fund 开休市判断，并支持本地覆盖文件修正。
"""
import json
import logging
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from zoneinfo import ZoneInfo

import config

try:
    import exchange_calendars as xcals
except Exception:  # pragma: no cover - fallback path
    xcals = None

try:
    import pandas as pd
except Exception:  # pragma: no cover - fallback path
    pd = None

logger = logging.getLogger(__name__)

MARKET_KEYS = ("a", "hk", "us", "fund")

_CALENDAR_CODES = {
    "a": "XSHG",
    "hk": "XHKG",
    "us": "XNYS",
    "fund": "XSHG",
}

_MARKET_TZ = {
    "a": "Asia/Shanghai",
    "hk": "Asia/Hong_Kong",
    "us": "America/New_York",
    "fund": "Asia/Shanghai",
}

# minutes in local time, [start, end)
_MARKET_SESSIONS = {
    "a": [(9 * 60 + 30, 11 * 60 + 30), (13 * 60, 15 * 60)],
    "hk": [(9 * 60 + 30, 12 * 60), (13 * 60, 16 * 60)],
    "us": [(9 * 60 + 30, 16 * 60)],
    "fund": [(9 * 60 + 30, 15 * 60)],
}

_calendar_cache: Dict[str, Any] = {}
_override_cache: Dict[str, Any] = {
    "path": None,
    "mtime": None,
    "data": {"force_closed": {}, "force_open": {}},
}


def _normalize_market(market: str) -> str:
    m = str(market or "").strip().lower()
    return m if m in MARKET_KEYS else "a"


def _normalize_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
    # 兜底：exchange_calendars / pandas / numpy 可能返回非标准类型（如 numpy.datetime64）。
    # 只要 pandas 可用，就尝试用 Timestamp 解析成 date。
    if pd is not None:
        try:
            return pd.Timestamp(value).date()
        except Exception:
            pass
    raise ValueError(f"Unsupported date value: {value!r}")


def _normalize_datetime(value: Optional[datetime]) -> datetime:
    if value is None:
        now = datetime.now(timezone.utc)
    elif isinstance(value, datetime):
        now = value
    else:
        raise ValueError(f"Unsupported datetime value: {value!r}")
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now


def _clean_date_values(values: Any) -> set[str]:
    result: set[str] = set()
    if not isinstance(values, list):
        return result
    for raw in values:
        try:
            d = _normalize_date(raw)
            result.add(d.strftime("%Y-%m-%d"))
        except Exception:
            continue
    return result


def _load_overrides() -> Dict[str, Dict[str, set[str]]]:
    path = Path(config.MARKET_HOLIDAY_OVERRIDES_PATH)
    mtime = None
    if path.exists():
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = None

    if _override_cache["path"] == str(path) and _override_cache["mtime"] == mtime:
        return _override_cache["data"]

    data: Dict[str, Dict[str, set[str]]] = {"force_closed": {}, "force_open": {}}
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            for key in ("force_closed", "force_open"):
                scoped = raw.get(key, {})
                if not isinstance(scoped, dict):
                    continue
                for market, values in scoped.items():
                    m = _normalize_market(market)
                    data[key][m] = _clean_date_values(values)
        except Exception as exc:
            logger.warning("Failed to load market holiday overrides %s: %s", path, exc)

    _override_cache["path"] = str(path)
    _override_cache["mtime"] = mtime
    _override_cache["data"] = data
    return data


def _override_state(market: str, target_date: date) -> Optional[str]:
    date_str = target_date.strftime("%Y-%m-%d")
    data = _load_overrides()
    m = _normalize_market(market)
    if date_str in data.get("force_closed", {}).get(m, set()):
        return "force_closed"
    if date_str in data.get("force_open", {}).get(m, set()):
        return "force_open"
    return None


def _get_calendar(market: str):
    m = _normalize_market(market)
    code = _CALENDAR_CODES.get(m)
    if not code or xcals is None:
        return None
    if code in _calendar_cache:
        return _calendar_cache[code]
    try:
        cal = xcals.get_calendar(code)
    except Exception as exc:
        logger.warning("Failed to init exchange calendar %s: %s", code, exc)
        cal = None
    _calendar_cache[code] = cal
    return cal


def _is_trading_day_from_calendar(market: str, target_date: Any) -> bool:
    """
    主交易日来源：exchange_calendars。
    若运行环境缺失依赖/初始化失败，降级为“仅周末休市”。
    """
    d = _normalize_date(target_date)
    fallback = d.weekday() < 5
    if xcals is None or pd is None:
        logger.warning(
            "exchange_calendars unavailable, market=%s date=%s fallback weekday=%s",
            market,
            d,
            fallback,
        )
        return fallback

    cal = _get_calendar(market)
    if cal is None:
        logger.warning(
            "exchange_calendars init failed, market=%s date=%s fallback weekday=%s",
            market,
            d,
            fallback,
        )
        return fallback

    def _resolve_session_date(raw: Any) -> Optional[date]:
        if raw is None:
            return None
        # 某些版本可能暴露为方法而不是属性
        if callable(raw):
            try:
                raw = raw()
            except Exception:
                return None
        try:
            return _normalize_date(raw)
        except Exception:
            if pd is None:
                return None
            try:
                return pd.Timestamp(raw).date()
            except Exception:
                return None

    # exchange_calendars 在“超出数据覆盖范围”的日期上，部分版本会直接返回 False，
    # 而不是抛异常。这里显式检测范围，超界就回退到 weekday 逻辑，避免把未来工作日误判为休市。
    try:
        first_raw = getattr(cal, "first_session", None)
        last_raw = getattr(cal, "last_session", None)
        first_date = _resolve_session_date(first_raw)
        last_date = _resolve_session_date(last_raw)

        # 再兜底一次：从 sessions 列表取首尾（避免 first/last API 变动）
        if (first_date is None or last_date is None) and hasattr(cal, "sessions"):
            try:
                sessions = getattr(cal, "sessions", None)
                if sessions is not None and len(sessions) > 0:
                    if first_date is None:
                        first_date = _resolve_session_date(sessions[0])
                    if last_date is None:
                        last_date = _resolve_session_date(sessions[-1])
            except Exception:
                pass

        if first_date is not None and last_date is not None:
            if d < first_date or d > last_date:
                logger.warning(
                    "exchange_calendars data coverage insufficient for market=%s date=%s range=%s..%s fallback weekday=%s",
                    market,
                    d,
                    first_date,
                    last_date,
                    fallback,
                )
                return fallback
    except Exception as exc:
        logger.warning(
            "exchange_calendars range check failed for market=%s date=%s: %s",
            market,
            d,
            exc,
        )

    try:
        ts = pd.Timestamp(d.isoformat())
        if hasattr(cal, "is_session"):
            return bool(cal.is_session(ts))
        if hasattr(cal, "sessions_in_range"):
            return len(cal.sessions_in_range(ts, ts)) > 0
    except Exception as exc:
        logger.warning("Calendar session check failed for market=%s date=%s: %s", market, d, exc)
        return fallback
    return fallback


def is_trading_day(market: str, target_date: Any) -> bool:
    d = _normalize_date(target_date)
    state = _override_state(market, d)
    if state == "force_closed":
        return False
    if state == "force_open":
        return True
    return _is_trading_day_from_calendar(market, d)


def _is_open_in_session(market: str, now_local: datetime) -> bool:
    m = _normalize_market(market)
    sessions = _MARKET_SESSIONS.get(m, [])
    minute = now_local.hour * 60 + now_local.minute
    for start, end in sessions:
        if start <= minute < end:
            return True
    return False


def _is_open_from_calendar(market: str, now_utc: datetime) -> Optional[bool]:
    """
    优先使用 exchange_calendars 按分钟判断开市状态。
    - 能识别半日市、午休、夏令时等特殊时段；
    - 依赖不可用时返回 None，由静态时段兜底。
    """
    if xcals is None or pd is None:
        return None

    cal = _get_calendar(market)
    if cal is None:
        return None

    try:
        ts = pd.Timestamp(now_utc)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        if hasattr(cal, "is_open_on_minute"):
            return bool(cal.is_open_on_minute(ts, ignore_breaks=False))
    except Exception as exc:
        logger.warning(
            "Calendar open-minute check failed for market=%s now=%s: %s",
            market,
            now_utc,
            exc,
        )
        return None
    return None


def get_market_status(market: str, now: Optional[datetime] = None) -> Dict[str, Any]:
    try:
        m = _normalize_market(market)
        utc_now = _normalize_datetime(now)
        tz = ZoneInfo(_MARKET_TZ[m])
        local_now = utc_now.astimezone(tz)
        d = local_now.date()
        state = _override_state(m, d)

        trading_day = is_trading_day(m, d)
        if not trading_day:
            return {
                "open": False,
                "trading_day": False,
                "reason": "override" if state == "force_closed" else "holiday_or_weekend",
            }

        open_now = _is_open_from_calendar(m, utc_now)
        if open_now is None:
            open_now = _is_open_in_session(m, local_now)
        if open_now:
            return {
                "open": True,
                "trading_day": True,
                "reason": "override" if state == "force_open" else "open_session",
            }
        return {
            "open": False,
            "trading_day": True,
            "reason": "override" if state == "force_open" else "off_hours",
        }
    except Exception as exc:
        logger.warning(
            "Failed to get market status, market=%s now=%r fallback closed: %s",
            market,
            now,
            exc,
        )
        return {"open": False, "trading_day": False, "reason": "holiday_or_weekend"}


def is_market_open_now(market: str, now: Optional[datetime] = None) -> bool:
    return bool(get_market_status(market, now=now).get("open"))


def get_market_statuses(
    markets: Optional[Iterable[str]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Dict[str, Any]]:
    source = markets or MARKET_KEYS
    result: Dict[str, Dict[str, Any]] = {}
    for market in source:
        m = _normalize_market(market)
        result[m] = get_market_status(m, now=now)
    return result


def all_markets_closed(
    markets: Optional[Iterable[str]] = None,
    now: Optional[Any] = None,
) -> bool:
    ms = [(_normalize_market(m)) for m in (markets or MARKET_KEYS)]
    if now is not None and not isinstance(now, datetime):
        try:
            return is_markets_closed_on_date(ms, now)
        except Exception as exc:
            logger.warning(
                "Failed to resolve all_markets_closed by date=%r markets=%s: %s",
                now,
                ms,
                exc,
            )
            return True

    try:
        statuses = get_market_statuses(markets=ms, now=now)
    except Exception as exc:
        logger.warning(
            "Failed to resolve market statuses, fallback all_closed=True: %s",
            exc,
        )
        return True
    if not statuses:
        return True
    return all(not bool(item.get("open")) for item in statuses.values())


def is_markets_closed_on_date(markets: Optional[Iterable[str]], target_date: Any) -> bool:
    ms = [(_normalize_market(m)) for m in (markets or MARKET_KEYS)]
    if not ms:
        return True
    d = _normalize_date(target_date)
    for m in ms:
        if is_trading_day(m, d):
            return False
    return True


def get_previous_trading_day(market: str, target_date: Any) -> Optional[date]:
    """
    返回 target_date 之前最近一个交易日（不包含当天）。

    这里主要给“美股夜盘归前一交易日”和“周末展示仍需归到上个交易日”使用。
    """
    d = _normalize_date(target_date)
    for offset in range(1, 15):
        candidate = d.fromordinal(d.toordinal() - offset)
        try:
            if is_trading_day(market, candidate):
                return candidate
        except Exception:
            continue
    return None


def market_from_asset(asset: Any) -> str:
    if isinstance(asset, str):
        code = asset
        asset_type = ""
    else:
        code = str((asset or {}).get("code", "")).strip()
        asset_type = str((asset or {}).get("asset_type", "")).strip().lower()

    # 场内 ETF（asset_type=fund 但代码不以 f_/ft_ 开头）按 A 股市场处理：
    # 它们在 A 股交易所交易，共享交易时段和结算周期。
    # 如果归入 "fund" 市场，late settlement 回填时场外基金 NAV 会覆写
    # 场内 ETF 的 day_pnl，导致日历收益数据丢失。
    if asset_type == "fund":
        c = code.lower()
        if not c.startswith(("f_", "ft_")):
            return "a"
        return "fund"

    if asset_type in MARKET_KEYS:
        return asset_type

    c = code.lower()
    if c.startswith(("f_", "ft_")):
        return "fund"
    if c.startswith("hk") or ".hk" in c:
        return "hk"
    if c.startswith("gb_") or re.fullmatch(r"[a-z]+(?:\.[a-z]+)?", c):
        return "us"
    if c.startswith(("sh", "sz", "bj")):
        return "a"
    return "a"

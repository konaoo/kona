"""
资产趋势数据模块
统一提供股票/场内 ETF/基金的近期估值趋势。
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List

import config
from .asset_type import infer_asset_type
from .fund import get_fund_overseas_history_points
from .market_calendar import get_previous_trading_day
from .price import _map_fund_code_to_exchange_if_tradable
from .utils import monitored_http_get, safe_float

logger = logging.getLogger(__name__)

_RECENT_HISTORY_MAX_GAP_DAYS = 20


def _normalize_code(code: Any) -> str:
    return str(code or "").strip()


def _parse_history_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _dedupe_history_points(points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[str, float] = {}
    for item in points or []:
        dt = str((item or {}).get("date") or "").strip()[:10]
        value = safe_float((item or {}).get("value"))
        if not dt or value <= 0:
            continue
        deduped[dt] = value
    return [{"date": dt, "value": deduped[dt]} for dt in sorted(deduped.keys())]


def _trim_recent_history_cluster(
    points: List[Dict[str, Any]],
    *,
    max_gap_days: int = _RECENT_HISTORY_MAX_GAP_DAYS,
) -> List[Dict[str, Any]]:
    normalized = _dedupe_history_points(points)
    if len(normalized) <= 1:
        return normalized

    recent_cluster = [normalized[-1]]
    prev_date = _parse_history_date(normalized[-1]["date"])
    if prev_date is None:
        return normalized[-1:]

    for item in reversed(normalized[:-1]):
        current_date = _parse_history_date(item["date"])
        if current_date is None:
            continue
        gap_days = (prev_date - current_date).days
        if gap_days <= 0:
            continue
        if gap_days > max_gap_days:
            break
        recent_cluster.append(item)
        prev_date = current_date

    return list(reversed(recent_cluster))


def _extract_tencent_prev_close(
    payload: Dict[str, Any],
    *,
    symbol: str,
) -> float:
    data = (payload.get("data") or {}).get(symbol) or {}
    qt = (data.get("qt") or {}).get(symbol) or []
    if not isinstance(qt, list) or len(qt) < 5:
        return 0.0
    return safe_float(qt[4])


def _complete_latest_tencent_us_history(
    points: List[Dict[str, Any]],
    *,
    prev_close: float,
) -> List[Dict[str, Any]]:
    recent = _trim_recent_history_cluster(points)
    if not recent:
        return []
    if len(recent) >= 2 or prev_close <= 0:
        return recent

    last_date = _parse_history_date(recent[-1]["date"])
    if last_date is None:
        return recent
    previous_date = get_previous_trading_day("us", last_date)
    if previous_date is None:
        return recent

    previous_date_str = previous_date.strftime("%Y-%m-%d")
    if previous_date_str == recent[-1]["date"]:
        return recent
    return [
        {"date": previous_date_str, "value": prev_close},
        recent[-1],
    ]


def _is_exchange_fund_digits(digits: str) -> bool:
    if not re.fullmatch(r"\d{6}", digits or ""):
        return False
    if digits.startswith(("15", "16", "18")):
        return True
    if digits.startswith(("50", "51", "52", "56", "58", "511")):
        return True
    return False


def _resolve_stock_secids(code: str, market_hint: str = "") -> List[str]:
    s = _normalize_code(code).lower()
    hint = _normalize_code(market_hint).lower()
    if not s:
        return []

    if s.startswith("sh") and len(s) >= 8:
        return [f"1.{s[2:8]}"]
    if s.startswith("sz") and len(s) >= 8:
        return [f"0.{s[2:8]}"]
    if s.startswith("bj") and len(s) >= 8:
        return [f"0.{s[2:8]}"]
    if s.startswith("hk"):
        digits = re.sub(r"\D", "", s)
        return [f"116.{digits.zfill(5)}"] if digits else []

    digits = re.sub(r"\D", "", s)
    if re.fullmatch(r"\d{5}", digits):
        if hint == "hk":
            return [f"116.{digits}"]
        return [f"116.{digits}"]

    if re.fullmatch(r"\d{6}", digits):
        if hint == "a":
            if digits.startswith(("5", "6", "9")):
                return [f"1.{digits}"]
            return [f"0.{digits}"]
        if hint == "fund" and _is_exchange_fund_digits(digits):
            if digits.startswith(("50", "51", "52", "56", "58", "511")):
                return [f"1.{digits}"]
            return [f"0.{digits}"]
        if hint == "bj":
            return [f"0.{digits}"]

    upper = s.upper().replace("GB_", "").replace("US.", "")
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]*", upper):
        return [f"105.{upper}", f"106.{upper}"]

    return []


def _resolve_tencent_symbol(code: str, market_hint: str = "") -> tuple[str, str] | tuple[None, None]:
    s = _normalize_code(code).strip()
    lower = s.lower()
    hint = _normalize_code(market_hint).lower()
    digits = re.sub(r"\D", "", lower)

    if lower.startswith("sh") and re.fullmatch(r"sh\d{6}", lower):
        return "a", lower
    if lower.startswith("sz") and re.fullmatch(r"sz\d{6}", lower):
        return "a", lower
    if lower.startswith("bj") and re.fullmatch(r"bj\d{6}", lower):
        return "a", lower
    if re.fullmatch(r"\d{6}\.(sh|ss)", lower):
        return "a", f"sh{digits}"
    if re.fullmatch(r"\d{6}\.(sz)", lower):
        return "a", f"sz{digits}"
    if re.fullmatch(r"\d{6}\.(bj)", lower):
        return "a", f"bj{digits}"

    if lower.startswith("hk") and digits:
        return "hk", f"hk{digits.zfill(5)}"
    if re.fullmatch(r"\d{5}\.hk", lower):
        return "hk", f"hk{digits}"
    if re.fullmatch(r"\d{5}", digits):
        if hint == "hk":
            return "hk", f"hk{digits}"
        return "hk", f"hk{digits}"

    upper = s.upper().replace("GB_", "").replace("US.", "").replace(".US", "")
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]*", upper):
        return "us", f"us{upper}"

    if re.fullmatch(r"\d{6}", digits):
        if hint == "bj":
            return "a", f"bj{digits}"
        if hint == "fund" and _is_exchange_fund_digits(digits):
            if digits.startswith(("50", "51", "52", "56", "58", "511")):
                return "a", f"sh{digits}"
            return "a", f"sz{digits}"
        if hint == "a" or digits.startswith(("0", "3", "5", "6", "8", "9")):
            if digits.startswith(("5", "6", "9")):
                return "a", f"sh{digits}"
            return "a", f"sz{digits}"

    return None, None


def _fetch_tencent_stock_history_points(code: str, limit: int, market_hint: str = "") -> List[Dict[str, Any]]:
    market, symbol = _resolve_tencent_symbol(code, market_hint)
    if not market or not symbol:
        return []

    if market == "hk":
        url = "https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get"
    elif market == "us":
        url = "https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get"
    else:
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

    try:
        r = monitored_http_get(
            "tencent_stock_history",
            url,
            params={"param": f"{symbol},day,,,{max(2, int(limit))},qfq"},
            headers={
                "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
                "Referer": "https://stockapp.finance.qq.com/",
            },
            timeout=config.API_TIMEOUT,
        )
        if r.status_code != 200:
            return []

        payload = r.json() or {}
        data = (payload.get("data") or {}).get(symbol) or {}
        klines = data.get("qfqday") or data.get("day") or []
        points: List[Dict[str, Any]] = []
        for item in klines:
            if not isinstance(item, list) or len(item) < 3:
                continue
            date = str(item[0] or "").strip()
            close = safe_float(item[2])
            if not date or close <= 0:
                continue
            points.append({"date": date, "value": close})
        if not points:
            return []
        if market == "us":
            points = _complete_latest_tencent_us_history(
                points,
                prev_close=_extract_tencent_prev_close(payload, symbol=symbol),
            )
        else:
            points = _trim_recent_history_cluster(points)
        return points[-limit:] if points else []
    except Exception as exc:
        logger.debug("tencent stock trend fetch failed code=%s symbol=%s error=%s", code, symbol, exc)
        return []


def _resolve_yahoo_us_symbol(code: str) -> str:
    normalized = _normalize_code(code).strip().upper()
    if not normalized:
        return ""
    if normalized.startswith("GB_"):
        normalized = normalized[3:]
    if normalized.startswith("US."):
        normalized = normalized[3:]
    if normalized.endswith(".US"):
        normalized = normalized[:-3]
    return normalized if re.fullmatch(r"[A-Z][A-Z0-9.\-]*", normalized) else ""


def _fetch_yahoo_us_history_points(code: str, limit: int) -> List[Dict[str, Any]]:
    symbol = _resolve_yahoo_us_symbol(code)
    if not symbol:
        return []

    try:
        response = monitored_http_get(
            "yahoo_us_history",
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={
                "range": "6mo",
                "interval": "1d",
                "includePrePost": "false",
            },
            headers={
                "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
                "Referer": "https://finance.yahoo.com/",
            },
            timeout=config.API_TIMEOUT,
        )
        if response.status_code != 200:
            return []

        payload = response.json() or {}
        result = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
        timestamps = result.get("timestamp") or []
        quote = (((result.get("indicators") or {}).get("quote") or [None])[0] or {})
        closes = quote.get("close") or []

        points: List[Dict[str, Any]] = []
        for raw_ts, raw_close in zip(timestamps, closes):
            close = safe_float(raw_close)
            if close <= 0:
                continue
            try:
                date = datetime.fromtimestamp(int(raw_ts), timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                continue
            points.append({"date": date, "value": close})
        return points[-limit:] if points else []
    except Exception as exc:
        logger.debug("yahoo us trend fetch failed code=%s symbol=%s error=%s", code, symbol, exc)
        return []


def _fetch_stooq_us_history_points(code: str, limit: int) -> List[Dict[str, Any]]:
    symbol = _resolve_yahoo_us_symbol(code)
    if not symbol:
        return []

    try:
        response = monitored_http_get(
            "stooq_us_history",
            "https://stooq.com/q/d/l/",
            params={
                "s": f"{symbol.lower()}.us",
                "i": "d",
            },
            headers={
                "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
                "Referer": "https://stooq.com/",
            },
            timeout=config.API_TIMEOUT,
        )
        if response.status_code != 200:
            return []

        text = str(response.text or "").strip()
        if not text or text.lower().startswith("no data"):
            return []

        points: List[Dict[str, Any]] = []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) < 5:
                continue
            date = str(parts[0] or "").strip()
            close = safe_float(parts[4])
            if not date or close <= 0:
                continue
            points.append({"date": date, "value": close})
        return points[-limit:] if points else []
    except Exception as exc:
        logger.debug("stooq us trend fetch failed code=%s symbol=%s error=%s", code, symbol, exc)
        return []


def _fetch_stock_history_points(code: str, limit: int, market_hint: str = "") -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
        "Referer": "https://quote.eastmoney.com/",
    }
    normalized_hint = _normalize_code(market_hint).lower()

    for secid in _resolve_stock_secids(code, market_hint):
        try:
            r = monitored_http_get(
                "eastmoney_stock_history",
                "https://push2his.eastmoney.com/api/qt/stock/kline/get",
                params={
                    "secid": secid,
                    "klt": "101",
                    "fqt": "1",
                    "lmt": max(2, int(limit)),
                    "end": "20500000",
                    "fields1": "f1,f2,f3,f4,f5,f6",
                    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
                },
                headers=headers,
                timeout=config.API_TIMEOUT,
            )
            payload = r.json() if r.status_code == 200 else {}
            klines = ((payload or {}).get("data") or {}).get("klines") or []
            points: List[Dict[str, Any]] = []
            for item in klines:
                parts = str(item or "").split(",")
                if len(parts) < 3:
                    continue
                date = str(parts[0]).strip()
                close = safe_float(parts[2])
                if not date or close <= 0:
                    continue
                points.append({"date": date, "value": close})
            if points:
                is_us_history = normalized_hint == "us" or str(secid).startswith(("105.", "106."))
                if is_us_history and len(points) < min(max(5, int(limit)), 5):
                    yahoo_points = _fetch_yahoo_us_history_points(code, limit)
                    if len(yahoo_points) >= 2:
                        return yahoo_points
                    stooq_points = _fetch_stooq_us_history_points(code, limit)
                    if len(stooq_points) >= 2:
                        return stooq_points
                    logger.debug(
                        "eastmoney us trend points too sparse, fallback to tencent: code=%s secid=%s points=%s",
                        code,
                        secid,
                        len(points),
                    )
                    break
                return points[-limit:]
        except Exception as exc:
            logger.debug("stock trend fetch failed code=%s secid=%s error=%s", code, secid, exc)
    if normalized_hint == "us":
        yahoo_points = _fetch_yahoo_us_history_points(code, limit)
        if len(yahoo_points) >= 2:
            return yahoo_points
        stooq_points = _fetch_stooq_us_history_points(code, limit)
        if len(stooq_points) >= 2:
            return stooq_points
    return _fetch_tencent_stock_history_points(code, limit, market_hint)


def _fetch_fund_history_points(code: str, limit: int) -> List[Dict[str, Any]]:
    raw = _normalize_code(code).strip()
    normalized = raw.lower()
    if normalized.startswith("ft_"):
        overseas_code = raw[3:].strip()
        if not overseas_code:
            return []
        overseas_points = get_fund_overseas_history_points(overseas_code, limit)
        return overseas_points[-limit:] if overseas_points else []

    if not normalized.startswith("f_"):
        return []

    clean_code = normalized[2:].strip()
    if not re.fullmatch(r"\d{6}", clean_code):
        return []

    try:
        r = monitored_http_get(
            "eastmoney_fund_f10",
            "https://api.fund.eastmoney.com/f10/lsjz",
            params={
                "fundCode": clean_code,
                "pageIndex": 1,
                "pageSize": max(2, int(limit)),
            },
            headers={
                "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
                "Referer": "https://fundf10.eastmoney.com/",
            },
            timeout=config.API_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        payload = r.json() or {}
        lsjz = ((payload.get("Data") or {}).get("LSJZList")) or []
        points: List[Dict[str, Any]] = []
        for item in reversed(lsjz):
            date = str((item or {}).get("FSRQ") or "").strip()
            value = safe_float((item or {}).get("DWJZ"))
            if not date or value <= 0:
                continue
            points.append({"date": date, "value": value})
        if points:
            return points[-limit:]

        overseas_points = get_fund_overseas_history_points(clean_code, limit)
        if overseas_points:
            return overseas_points[-limit:]
        return []
    except Exception as exc:
        logger.debug("fund trend fetch failed code=%s error=%s", code, exc)
        overseas_points = get_fund_overseas_history_points(clean_code, limit)
        return overseas_points[-limit:] if overseas_points else []


def get_asset_trend(code: str, name: str = "", points: int = 20, market_hint: str = "") -> Dict[str, Any]:
    normalized = _normalize_code(code)
    limit = max(2, min(int(points or 20), 60))
    if not normalized:
        return {
            "code": normalized,
            "kind": "unknown",
            "label": "近期估值趋势",
            "points": [],
        }

    inferred = infer_asset_type(normalized, name)
    mapped_code = normalized
    trend_kind = "stock"
    normalized_market_hint = _normalize_code(market_hint).lower()

    if normalized.lower().startswith("f_"):
        mapped = _map_fund_code_to_exchange_if_tradable(normalized)
        if mapped != normalized:
            mapped_code = mapped
            trend_kind = "stock"
        else:
            trend_kind = "fund"
    elif inferred == "fund":
        trend_kind = "fund"

    if trend_kind == "fund":
        trend_points = _fetch_fund_history_points(normalized, limit)
    else:
        trend_points = _fetch_stock_history_points(mapped_code, limit, normalized_market_hint)

    return {
        "code": normalized,
        "resolved_code": mapped_code,
        "kind": trend_kind,
        "label": "近期估值趋势",
        "points": trend_points,
    }


def batch_get_asset_trends(items: List[Dict[str, Any]], points: int = 20) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    seen: set[str] = set()
    for item in items or []:
        code = _normalize_code((item or {}).get("code"))
        if not code or code in seen:
            continue
        seen.add(code)
        result[code] = get_asset_trend(
            code,
            str((item or {}).get("name") or ""),
            points,
            str((item or {}).get("market") or ""),
        )
    return result

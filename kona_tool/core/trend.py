"""
资产趋势数据模块
统一提供股票/场内 ETF/基金的近期估值趋势。
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

import config
from .asset_type import infer_asset_type
from .fund import get_fund_overseas_history_points
from .price import _map_fund_code_to_exchange_if_tradable
from .utils import monitored_http_get, safe_float

logger = logging.getLogger(__name__)


def _normalize_code(code: Any) -> str:
    return str(code or "").strip()


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
        if hint == "bj":
            return [f"0.{digits}"]

    upper = s.upper().replace("GB_", "").replace("US.", "")
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]*", upper):
        return [f"105.{upper}", f"106.{upper}"]

    return []


def _fetch_stock_history_points(code: str, limit: int, market_hint: str = "") -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
        "Referer": "https://quote.eastmoney.com/",
    }

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
                return points[-limit:]
        except Exception as exc:
            logger.debug("stock trend fetch failed code=%s secid=%s error=%s", code, secid, exc)
    return []


def _fetch_fund_history_points(code: str, limit: int) -> List[Dict[str, Any]]:
    normalized = _normalize_code(code).lower()
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

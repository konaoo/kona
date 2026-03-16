"""
管理后台巡检、价格告警与 provider test。
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from flask import current_app

from core.admin.constants import (
    API_TEST_CASES_FUND,
    API_TEST_CASES_MARKET,
    API_TEST_PROVIDER_ALERT_LABELS,
    API_TEST_PROVIDER_LABELS,
    PRICE_ALERT_DELTA_PCT_CRITICAL,
    PRICE_ALERT_DELTA_PCT_WARNING,
    PRICE_ALERT_REPORT_TIMEZONE,
    PROVIDER_TEST_REPORT_TIMEZONE,
)
from core.asset_type import asset_type_label, infer_asset_type
from core.fund import (
    get_fund_eastmoney_f10,
    get_fund_eastmoney_mobile,
    get_fund_overseas_html,
    get_fund_tencent_jj,
    get_fund_tiantian_price,
)
from core.price import get_forex_rates, get_price, get_price_runtime_metrics, get_price_source_health
from core.stock import (
    get_blackrock_fund_price,
    get_boursorama_fund_price,
    get_eastmoney_stock_price,
    get_ft_fund_price,
    get_marketscreener_fund_price,
    get_sina_direct_stock_price,
    get_stock_price,
    get_tencent_stock_price,
    get_us_stock_price,
)
from core.system import system_manager
from core.utils import monitored_http_get, safe_float
import config


_ADMIN_DB = None
_ADMIN_LOGGER = logging.getLogger(__name__)


def set_admin_db(db) -> None:
    global _ADMIN_DB
    _ADMIN_DB = db


def price_alert_exchange_candidates(code: str) -> List[str]:
    lower = str(code or "").strip().lower()
    if not lower.startswith("f_"):
        return []
    suffix = lower[2:].strip()
    if not suffix.isdigit() or len(suffix) != 6:
        return []
    if suffix.startswith("11") and not suffix.startswith(("511",)):
        return []
    if suffix.startswith(("15", "18")):
        return [f"sz{suffix}"]
    if suffix.startswith(("50", "51", "52", "56", "58", "511")):
        return [f"sh{suffix}"]
    return []


def price_alert_abs_delta_pct(current: float, baseline: float) -> float:
    if current <= 0 or baseline <= 0:
        return 0.0
    return abs(current - baseline) / baseline * 100


def price_alert_severity(delta_pct: float) -> str:
    if delta_pct >= PRICE_ALERT_DELTA_PCT_CRITICAL:
        return "critical"
    if delta_pct >= PRICE_ALERT_DELTA_PCT_WARNING:
        return "warning"
    return "info"


def load_price_alert_holdings() -> List[Dict[str, Any]]:
    if _ADMIN_DB is None:
        raise RuntimeError("admin database is not initialized")
    conn = _ADMIN_DB.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT p.code, p.name, p.curr, p.user_id, u.username
            FROM portfolio p
            LEFT JOIN users u ON u.id = p.user_id
            WHERE ABS(COALESCE(p.qty, 0)) > 1e-9
            ORDER BY p.code ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        code = str(row["code"] or "").strip()
        if not code:
            continue
        item = grouped.setdefault(
            code,
            {
                "code": code,
                "name": str(row["name"] or "").strip() or code,
                "curr": str(row["curr"] or "").strip().upper() or "CNY",
                "usernames": [],
                "user_count": 0,
            },
        )
        username = str(row["username"] or "").strip() or "本地资产"
        if username not in item["usernames"]:
            item["usernames"].append(username)
    for item in grouped.values():
        item["user_count"] = len(item["usernames"])
    return list(grouped.values())


def probe_price_alert_sources(code: str) -> Tuple[Tuple[float, float, float, float], List[Dict[str, Any]]]:
    current = get_price(code, use_cache=False)
    sources: List[Dict[str, Any]] = []
    lower = str(code or "").strip().lower()

    def add_source(source_key: str, source_label: str, quote: Tuple[float, float, float, float]) -> None:
        price, yclose, amt, chg = quote
        sources.append(
            {
                "source_key": source_key,
                "source_label": source_label,
                "price": float(price or 0.0),
                "yclose": float(yclose or 0.0),
                "amt": float(amt or 0.0),
                "chg": float(chg or 0.0),
            }
        )

    if lower.startswith("ft_"):
        isin = lower.replace("ft_", "").upper()
        add_source("blackrock_official", "贝莱德官方", get_blackrock_fund_price(isin))
        add_source("marketscreener", "MarketScreener", get_marketscreener_fund_price(isin))
        add_source("boursorama", "Boursorama", get_boursorama_fund_price(isin))
        add_source("financial_times", "Financial Times", get_ft_fund_price(isin))
        return current, sources

    if lower.startswith("f_"):
        clean_code = lower.replace("f_", "")
        exchange_candidates = price_alert_exchange_candidates(lower)
        if exchange_candidates:
            for candidate in exchange_candidates:
                add_source(f"exchange:{candidate}", f"交易所 {candidate}", get_stock_price(candidate))
            return current, sources
        add_source("eastmoney_f10", "东财 F10", get_fund_eastmoney_f10(clean_code))
        if clean_code.startswith("968"):
            add_source("overseas_1234567", "海外基金页", get_fund_overseas_html(clean_code))
        add_source("eastmoney_mobile", "东财手机端", get_fund_eastmoney_mobile(clean_code))
        add_source("tiantian", "天天基金", get_fund_tiantian_price(lower))
        add_source("tencent_jj", "腾讯基金", get_fund_tencent_jj(clean_code))
        return current, sources

    asset_type = infer_asset_type(code)
    if asset_type in {"a", "hk"}:
        add_source("tencent_quote", "腾讯财经", get_tencent_stock_price(code))
        add_source("sina_quote", "新浪财经", get_sina_direct_stock_price(code))
        add_source("eastmoney_quote", "东方财富", get_eastmoney_stock_price(code))
        return current, sources

    if asset_type == "us":
        add_source("sina_us_quote", "新浪美股", get_sina_direct_stock_price(code))
        add_source("eastmoney_us_quote", "东方财富美股", get_eastmoney_stock_price(code))
        add_source("us_primary", "美股主链路", get_us_stock_price(code))
        return current, sources

    return current, sources


def guess_probe_primary_source(current_price: float, source_rows: List[Dict[str, Any]]) -> str:
    for row in source_rows:
        price = float(row.get("price") or 0.0)
        if price <= 0:
            continue
        if price_alert_abs_delta_pct(current_price, price) <= 0.001:
            return str(row.get("source_label") or row.get("source_key") or "")
    return ""


def build_price_probe_payload(code: str) -> Dict[str, Any]:
    raw_code = str(code or "").strip()
    if not raw_code:
        raise ValueError("缺少资产代码")

    current, source_rows = probe_price_alert_sources(raw_code)
    current_price = float(current[0] or 0.0)
    current_yclose = float(current[1] or 0.0)
    current_amt = float(current[2] or 0.0)
    current_chg = float(current[3] or 0.0)
    asset_type = infer_asset_type(raw_code)
    primary_source = guess_probe_primary_source(current_price, source_rows)

    normalized_sources: List[Dict[str, Any]] = []
    valid_deltas: List[float] = []
    for row in source_rows:
        price = float(row.get("price") or 0.0)
        delta_pct = price_alert_abs_delta_pct(current_price, price)
        if current_price > 0 and price > 0:
            valid_deltas.append(delta_pct)
        normalized_sources.append(
            {
                **row,
                "ok": price > 0,
                "delta_pct": round(delta_pct, 4),
            }
        )

    diagnosis_status = "ok"
    diagnosis_summary = "主价与各源基本一致。"
    if current_price <= 0:
        diagnosis_status = "critical"
        diagnosis_summary = "系统当前主价为空，这条资产需要优先排查。"
    elif not any(float(item.get("price") or 0.0) > 0 for item in normalized_sources):
        diagnosis_status = "warning"
        diagnosis_summary = "主价拿到了，但当前没有可用的多源对比结果。"
    elif valid_deltas:
        max_delta = max(valid_deltas)
        if max_delta >= PRICE_ALERT_DELTA_PCT_CRITICAL:
            diagnosis_status = "critical"
            diagnosis_summary = f"主价和备选源最大偏差 {max_delta:.2f}%，建议核对主链路。"
        elif max_delta >= PRICE_ALERT_DELTA_PCT_WARNING:
            diagnosis_status = "warning"
            diagnosis_summary = f"主价和备选源有轻微偏差，最大 {max_delta:.2f}%。"

    return {
        "code": raw_code,
        "asset_type": asset_type,
        "asset_type_label": asset_type_label(asset_type),
        "current": {
            "price": current_price,
            "yclose": current_yclose,
            "amt": current_amt,
            "chg": current_chg,
            "source_hint": primary_source,
        },
        "sources": normalized_sources,
        "diagnosis": {
            "status": diagnosis_status,
            "summary": diagnosis_summary,
        },
    }


def build_price_alert_for_holding(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    code = str(item.get("code") or "").strip()
    if not code:
        return []
    lower = code.lower()
    exchange_candidates = price_alert_exchange_candidates(lower)
    if lower.startswith("ft_"):
        pass
    elif lower.startswith("f_"):
        clean_code = lower.replace("f_", "")
        if not clean_code.startswith("968") and not exchange_candidates:
            return []
    else:
        return []

    current, source_rows = probe_price_alert_sources(code)
    current_price = float(current[0] or 0.0)
    available = [row for row in source_rows if float(row.get("price") or 0.0) > 0]
    alerts: List[Dict[str, Any]] = []

    def append_alert(*, alert_type: str, reason: str, baseline: Dict[str, Any], suggestion: str) -> None:
        baseline_price = float(baseline.get("price") or 0.0)
        delta_pct = price_alert_abs_delta_pct(current_price, baseline_price)
        alerts.append(
            {
                "code": code,
                "name": item.get("name") or code,
                "curr": item.get("curr") or "CNY",
                "user_count": int(item.get("user_count") or 0),
                "usernames": list(item.get("usernames") or []),
                "current_price": current_price,
                "current_yclose": float(current[1] or 0.0),
                "baseline_price": baseline_price,
                "baseline_yclose": float(baseline.get("yclose") or 0.0),
                "baseline_source": baseline.get("source_label") or baseline.get("source_key") or "",
                "baseline_source_key": baseline.get("source_key") or "",
                "delta_pct": round(delta_pct, 4),
                "severity": price_alert_severity(delta_pct),
                "alert_type": alert_type,
                "reason": reason,
                "suggestion": suggestion,
                "sources": available,
            }
        )

    exchange_rows = [row for row in available if str(row.get("source_key") or "").startswith("exchange:")]
    if code.lower().startswith("f_") and exchange_rows:
        baseline = exchange_rows[0]
        exchange_code = str(baseline.get("source_key") or "").split("exchange:", 1)[-1]
        if exchange_code and exchange_code != code:
            append_alert(
                alert_type="normalization",
                reason=f"当前资产疑似场内基金误存为 {code}，应改走 {exchange_code} 场内行情。",
                baseline=baseline,
                suggestion=f"将资产代码标准化为 {exchange_code}，并优先使用交易所价格链路。",
            )
            return alerts

    trusted: Dict[str, Any] | None = None
    if lower.startswith("ft_"):
        for source_key in ("blackrock_official", "marketscreener", "boursorama", "financial_times"):
            trusted = next((row for row in available if row.get("source_key") == source_key), None)
            if trusted:
                break
    elif lower.startswith("f_"):
        clean_code = lower.replace("f_", "")
        if exchange_rows:
            trusted = exchange_rows[0]
        if trusted is None:
            order = ["eastmoney_f10", "eastmoney_mobile", "tiantian", "tencent_jj"]
            if clean_code.startswith("968"):
                order = ["overseas_1234567", *order]
            for source_key in order:
                trusted = next((row for row in available if row.get("source_key") == source_key), None)
                if trusted:
                    break

    if trusted and current_price > 0:
        delta_pct = price_alert_abs_delta_pct(current_price, float(trusted.get("price") or 0.0))
        if delta_pct >= PRICE_ALERT_DELTA_PCT_WARNING:
            append_alert(
                alert_type="price_mismatch",
                reason=f"当前主价格与可信基准源 {trusted.get('source_label')} 偏差过大。",
                baseline=trusted,
                suggestion=f"检查 {trusted.get('source_label')} 是否应提升优先级，或将当前价格回退到该源。",
            )
    elif current_price <= 0 and trusted:
        append_alert(
            alert_type="missing_price",
            reason="当前主价格无返回，但存在可用备源。",
            baseline=trusted,
            suggestion=f"回退到 {trusted.get('source_label')}，避免前端显示空价。",
        )

    return alerts


def load_price_alerts_payload() -> Dict[str, Any]:
    holdings = load_price_alert_holdings()
    items: List[Dict[str, Any]] = []
    for holding in holdings:
        items.extend(build_price_alert_for_holding(holding))

    items.sort(
        key=lambda row: (
            {"critical": 0, "warning": 1, "info": 2}.get(str(row.get("severity") or "info"), 9),
            -float(row.get("delta_pct") or 0.0),
            str(row.get("code") or ""),
        )
    )
    summary = {"critical": 0, "warning": 0, "info": 0}
    for row in items:
        severity = str(row.get("severity") or "info")
        summary[severity] = int(summary.get(severity, 0)) + 1

    return {
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_assets": len(holdings),
        "alert_count": len(items),
        "summary": summary,
        "items": items,
    }


def save_price_alert_report_snapshot(payload: Dict[str, Any]) -> None:
    if _ADMIN_DB is None:
        return
    tested_at_utc = str(payload.get("tested_at_utc") or "").strip()
    if not tested_at_utc:
        return
    try:
        report_date = datetime.now(PRICE_ALERT_REPORT_TIMEZONE).date().isoformat()
        _ADMIN_DB.save_price_alert_report(
            report_date=report_date,
            tested_at_utc=tested_at_utc,
            total_assets=int(payload.get("total_assets") or 0),
            alert_count=int(payload.get("alert_count") or 0),
            summary=dict(payload.get("summary") or {}),
            items=list(payload.get("items") or []),
        )
    except Exception:
        current_app.logger.exception("save_price_alert_report failed")


def provider_test_summary(providers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    degraded_keys = [
        provider_key
        for provider_key, payload in providers.items()
        if str((payload or {}).get("status") or "").lower() != "ok"
    ]
    if not degraded_keys:
        return {"status": "ok", "label": "正常", "alert_keys": []}
    if len(degraded_keys) == 1:
        provider_key = degraded_keys[0]
        return {
            "status": "alert",
            "label": API_TEST_PROVIDER_ALERT_LABELS.get(provider_key, "行情告警"),
            "alert_keys": degraded_keys,
        }
    return {"status": "alert", "label": "多源告警", "alert_keys": degraded_keys}


def normalize_provider_report(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    raw = dict(payload or {})
    summary = raw.get("summary")
    providers = raw.get("providers")
    tested_at_utc = str(raw.get("tested_at_utc") or "").strip()
    report_slot = str(raw.get("report_slot") or "").strip()
    updated_at = str(raw.get("updated_at") or "").strip()
    if not isinstance(summary, dict):
        summary = {}
    if not isinstance(providers, dict):
        providers = {}
    return {
        "report_slot": report_slot,
        "tested_at_utc": tested_at_utc,
        "updated_at": updated_at,
        "summary": summary,
        "providers": providers,
    }


def save_provider_test_report_snapshot(payload: Dict[str, Any]) -> None:
    if _ADMIN_DB is None:
        return
    tested_at_utc = str(payload.get("tested_at_utc") or "").strip()
    if not tested_at_utc:
        return
    try:
        report_slot = datetime.now(PROVIDER_TEST_REPORT_TIMEZONE).strftime("%Y-%m-%dT%H")
        _ADMIN_DB.save_provider_test_report(
            report_slot=report_slot,
            tested_at_utc=tested_at_utc,
            summary=dict(payload.get("summary") or {}),
            providers=dict(payload.get("providers") or {}),
        )
    except Exception:
        _ADMIN_LOGGER.exception("save_provider_test_report failed")


def get_latest_provider_test_report() -> Dict[str, Any] | None:
    if _ADMIN_DB is None:
        return None
    try:
        report = _ADMIN_DB.get_latest_provider_test_report()
    except Exception:
        _ADMIN_LOGGER.exception("get_latest_provider_test_report failed")
        return None
    if not report:
        return None
    return normalize_provider_report(report)


def list_price_alert_report_history(limit: int = 7) -> List[Dict[str, Any]]:
    if _ADMIN_DB is None:
        return []
    try:
        return _ADMIN_DB.list_price_alert_reports(limit=limit)
    except Exception:
        current_app.logger.exception("list_price_alert_reports failed")
        return []


def get_latest_price_alert_report() -> Dict[str, Any] | None:
    if _ADMIN_DB is None:
        return None
    try:
        return _ADMIN_DB.get_latest_price_alert_report()
    except Exception:
        current_app.logger.exception("get_latest_price_alert_report failed")
        return None


def format_api_test_item(
    *,
    case: Dict[str, str],
    ok: bool,
    latency_ms: int,
    detail: str = "",
    status: str = "",
    price: float = 0.0,
    yclose: float = 0.0,
) -> Dict[str, Any]:
    change = price - yclose if yclose > 0 else 0.0
    change_pct = (change / yclose * 100) if yclose > 0 else 0.0
    item_status = str(status or ("ok" if ok else "error")).strip().lower() or "error"
    return {
        "name": str(case.get("name", "")),
        "code": str(case.get("code", "")),
        "asset_type": str(case.get("asset_type", "")),
        "ok": bool(ok),
        "status": item_status,
        "price": round(float(price or 0.0), 4),
        "yclose": round(float(yclose or 0.0), 4),
        "change": round(change, 4),
        "change_pct": round(change_pct, 4),
        "latency_ms": int(latency_ms),
        "detail": detail,
    }


def to_sina_quote_code(raw_code: str) -> str:
    code = str(raw_code or "").strip().lower()
    if code.startswith("f_"):
        return code
    if code.startswith(("sh", "sz", "bj", "hk", "gb_", "s_")):
        return code
    if code.isdigit() and len(code) == 6:
        return ("sh" if code[0] in {"5", "6", "9"} else "sz") + code
    if code.isdigit() and len(code) == 5:
        return "hk" + code
    if ".hk" in code:
        return "hk" + code.replace(".hk", "")
    if code:
        return "gb_" + code
    return code


def to_tencent_quote_code(raw_code: str) -> str:
    code = str(raw_code or "").strip()
    lower = code.lower()
    if lower.startswith("f_"):
        return lower
    if lower.startswith("gb_"):
        return f"us{lower.replace('gb_', '').upper()}"
    if lower.startswith("us."):
        return f"us{lower.replace('us.', '').upper()}"
    if lower.startswith(("sh", "sz", "bj", "hk", "s_")):
        return lower
    if lower.isdigit() and len(lower) == 6:
        return ("sh" if lower[0] in {"5", "6", "9"} else "sz") + lower
    if lower.isdigit() and len(lower) == 5:
        return "hk" + lower
    if ".hk" in lower:
        return "hk" + lower.replace(".hk", "")
    return f"us{code.upper()}" if code else lower


def eastmoney_secid_candidates(raw_code: str) -> List[str]:
    code = str(raw_code or "").strip().lower()
    if code.startswith("f_"):
        return []
    if code.startswith("gb_"):
        symbol = code.replace("gb_", "").upper()
        return [f"105.{symbol}", f"106.{symbol}"]
    if code.startswith("hk"):
        digits = "".join(ch for ch in code[2:] if ch.isdigit())
        if digits:
            return [f"116.{digits.zfill(5)}"]
    if code.startswith("sh") and len(code) >= 8:
        return [f"1.{code[2:8]}"]
    if code.startswith(("sz", "bj")) and len(code) >= 8:
        return [f"0.{code[2:8]}"]
    if code.isdigit() and len(code) == 6:
        market = "1" if code[0] in {"5", "6", "9"} else "0"
        return [f"{market}.{code}"]
    return []


def parse_sina_quote(raw_code: str, text: str) -> Tuple[float, float]:
    if '="' not in text:
        return 0.0, 0.0
    payload = text.split('="', 1)[1].split('"', 1)[0]
    data = payload.split(",")
    code = to_sina_quote_code(raw_code)
    curr = 0.0
    yclose = 0.0
    if code.startswith("gb_"):
        curr = safe_float(data[1] if len(data) > 1 else 0)
        yclose = safe_float(data[26] if len(data) > 26 else 0)
        if curr <= 0:
            curr = safe_float(data[21] if len(data) > 21 else 0)
    elif code.startswith("hk"):
        curr = safe_float(data[6] if len(data) > 6 else 0)
        yclose = safe_float(data[3] if len(data) > 3 else 0)
    else:
        curr = safe_float(data[3] if len(data) > 3 else 0)
        yclose = safe_float(data[2] if len(data) > 2 else 0)
    if curr <= 0 and yclose > 0:
        curr = yclose
    return curr, yclose


def test_sina_quote(code: str) -> Tuple[float, float]:
    sina_code = to_sina_quote_code(code)
    if sina_code.startswith("f_"):
        raise ValueError("新浪行情暂不支持场外基金代码")
    url = config.API_ENDPOINTS["sina_stock"].format(code=sina_code)
    headers = dict(config.HEADERS or {})
    headers["Referer"] = "https://finance.sina.com.cn"
    resp = monitored_http_get(
        "admin_sina_quote_test",
        url,
        headers=headers,
        timeout=min(3.0, float(getattr(config, "API_TIMEOUT", 3))),
    )
    price, yclose = parse_sina_quote(code, resp.text)
    if price <= 0:
        raise RuntimeError("新浪返回为空或解析失败")
    return price, yclose


def test_tencent_quote(code: str) -> Tuple[float, float]:
    tencent_code = to_tencent_quote_code(code)
    if tencent_code.startswith("f_"):
        raise ValueError("腾讯行情暂不支持场外基金代码")
    url = config.API_ENDPOINTS["tencent_stock"].format(code=tencent_code)
    resp = monitored_http_get(
        "admin_tencent_quote_test",
        url,
        timeout=min(3.0, float(getattr(config, "API_TIMEOUT", 3))),
    )
    text = resp.text
    if '="' not in text:
        raise RuntimeError("腾讯返回格式异常")
    payload = text.split('="', 1)[1].split('"', 1)[0]
    parts = payload.split("~")
    curr = safe_float(parts[3] if len(parts) > 3 else 0)
    yclose = safe_float(parts[4] if len(parts) > 4 else 0)
    if curr <= 0 and yclose > 0:
        curr = yclose
    if curr <= 0:
        raise RuntimeError("腾讯返回为空或解析失败")
    return curr, yclose


def test_eastmoney_quote(code: str) -> Tuple[float, float]:
    lower = str(code or "").strip().lower()
    if lower.startswith("f_"):
        price, yclose, _, _ = get_fund_eastmoney_f10(lower.replace("f_", ""))
        if price <= 0:
            raise RuntimeError("东方财富基金净值接口无返回")
        return float(price), float(yclose)

    secids = eastmoney_secid_candidates(lower)
    if not secids:
        raise ValueError("东方财富不支持该代码格式")

    base_url = str(config.API_ENDPOINTS.get("eastmoney_stock") or "").strip()
    if not base_url:
        base_url = "https://push2.eastmoney.com/api/qt/stock/get"

    for secid in secids:
        resp = monitored_http_get(
            "admin_eastmoney_quote_test",
            base_url,
            params={"invt": 2, "fltt": 2, "fields": "f43,f60", "secid": secid},
            headers={"User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0")},
            timeout=min(3.0, float(getattr(config, "API_TIMEOUT", 3))),
        )
        body = resp.json() if resp.status_code == 200 else {}
        data = body.get("data") if isinstance(body, dict) else {}
        if not isinstance(data, dict):
            continue
        curr = safe_float(data.get("f43"))
        yclose = safe_float(data.get("f60"))
        if curr > 10000 and yclose > 10000:
            curr = curr / 100.0
            yclose = yclose / 100.0
        if curr <= 0 and yclose > 0:
            curr = yclose
        if curr > 0:
            return curr, yclose
    raise RuntimeError("东方财富返回为空或解析失败")


def run_market_provider_test(provider_key: str) -> Dict[str, Any]:
    tester_map = {
        "sina_quote": test_sina_quote,
        "tencent_quote": test_tencent_quote,
        "eastmoney_quote": test_eastmoney_quote,
    }
    tester = tester_map.get(provider_key)
    if tester is None:
        raise ValueError("Unsupported provider_key")

    cases = list(API_TEST_CASES_MARKET)
    if provider_key == "eastmoney_quote":
        cases.extend(API_TEST_CASES_FUND)

    items: List[Dict[str, Any]] = []
    for case in cases:
        started = time.perf_counter()
        try:
            price, yclose = tester(str(case.get("code", "")))
            latency_ms = int((time.perf_counter() - started) * 1000)
            items.append(
                format_api_test_item(
                    case=case,
                    ok=True,
                    status="ok",
                    latency_ms=latency_ms,
                    detail="ok",
                    price=price,
                    yclose=yclose,
                )
            )
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            detail = str(exc)
            is_unsupported = isinstance(exc, ValueError) and "暂不支持" in detail
            items.append(
                format_api_test_item(
                    case=case,
                    ok=False,
                    status="unsupported" if is_unsupported else "error",
                    latency_ms=latency_ms,
                    detail=detail,
                )
            )

    status_values = {str(item.get("status") or "") for item in items}
    status = "ok" if status_values <= {"ok", "unsupported"} else "degraded"
    return {
        "provider_key": provider_key,
        "provider_label": API_TEST_PROVIDER_LABELS.get(provider_key, provider_key),
        "status": status,
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }


def run_forex_provider_test() -> Dict[str, Any]:
    started = time.perf_counter()
    rates = get_forex_rates()
    latency_ms = int((time.perf_counter() - started) * 1000)
    usd = safe_float((rates or {}).get("USD", 0))
    hkd = safe_float((rates or {}).get("HKD", 0))
    items = [
        {
            "name": "美元兑人民币",
            "code": "USD/CNY",
            "ok": usd > 0,
            "rate": round(usd, 6),
            "latency_ms": latency_ms,
            "detail": "ok" if usd > 0 else "无有效汇率",
        },
        {
            "name": "港币兑人民币",
            "code": "HKD/CNY",
            "ok": hkd > 0,
            "rate": round(hkd, 6),
            "latency_ms": latency_ms,
            "detail": "ok" if hkd > 0 else "无有效汇率",
        },
    ]
    return {
        "provider_key": "forex_rate",
        "provider_label": API_TEST_PROVIDER_LABELS["forex_rate"],
        "status": "ok" if all(bool(item.get("ok")) for item in items) else "degraded",
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }


def run_provider_test_report() -> Dict[str, Any]:
    providers_payload: Dict[str, Dict[str, Any]] = {}
    tested_times: List[datetime] = []
    for provider_key in ("sina_quote", "eastmoney_quote", "tencent_quote", "forex_rate"):
        payload = run_forex_provider_test() if provider_key == "forex_rate" else run_market_provider_test(provider_key)
        providers_payload[provider_key] = payload
        raw_tested_at = str(payload.get("tested_at_utc") or "").strip()
        if not raw_tested_at:
            continue
        try:
            tested_times.append(datetime.fromisoformat(raw_tested_at))
        except Exception:
            continue

    latest_tested_at = max(tested_times).isoformat() if tested_times else datetime.now(timezone.utc).isoformat()
    return {
        "tested_at_utc": latest_tested_at,
        "summary": provider_test_summary(providers_payload),
        "providers": providers_payload,
    }


def run_provider_test_report_job() -> Dict[str, Any]:
    payload = run_provider_test_report()
    save_provider_test_report_snapshot(payload)
    return payload

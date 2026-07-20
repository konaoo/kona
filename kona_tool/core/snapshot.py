"""
资产快照管理模块
负责在后台计算并保存每日资产快照
"""
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from zoneinfo import ZoneInfo

from .day_pnl_attribution import (
    resolve_fund_nav_effective_date,
)
from .db import db
from .fund import get_fund_latest_nav_date
from .market_calendar import (
    all_markets_closed,
    get_market_statuses,
    get_previous_trading_day,
    is_markets_closed_on_date,
    is_trading_day,
    market_from_asset,
)
from .price import batch_get_prices, get_forex_rates, is_exchange_fund_code

logger = logging.getLogger(__name__)
DEFAULT_MARKETS = ["a", "hk", "us", "fund"]
LATE_SETTLEMENT_MARKETS = ("a", "hk", "us", "fund")
MARKET_TIMEZONES = {
    "a": "Asia/Shanghai",
    "hk": "Asia/Hong_Kong",
    "us": "America/New_York",
    "fund": "Asia/Shanghai",
}
MARKET_FIRST_SESSION_START = {
    "a": 9 * 60 + 30,
    "hk": 9 * 60 + 30,
    "us": 9 * 60 + 30,
    "fund": 9 * 60 + 30,
}


def is_market_closed() -> bool:
    """
    判断当前是否全市场休市。
    """
    return all_markets_closed(DEFAULT_MARKETS)


def _market_local_date(market: str, now_utc: datetime):
    tz_name = MARKET_TIMEZONES.get(str(market or "").lower(), "UTC")
    try:
        return now_utc.astimezone(ZoneInfo(tz_name)).date()
    except Exception:
        return now_utc.date()


def _market_trading_day_now(
    market: str,
    now_utc: datetime,
    market_statuses: Dict[str, Dict[str, str]],
) -> bool:
    m = str(market or "a").lower()
    local_date = _market_local_date(m, now_utc)
    try:
        return bool(is_trading_day(m, local_date))
    except Exception:
        status = market_statuses.get(m) or {}
        if bool(status.get("open")):
            return True
        return str(status.get("reason") or "").lower() in {"off_hours", "open_session"}


def _is_preopen_off_hours_market(
    market: str,
    now_utc: datetime,
    market_statuses: Dict[str, Dict[str, str]],
) -> bool:
    m = str(market or "a").lower()
    status = market_statuses.get(m) or {}
    if bool(status.get("open")):
        return False
    if not bool(status.get("trading_day")):
        return False
    if str(status.get("reason") or "").lower() != "off_hours":
        return False
    local_now = now_utc.astimezone(ZoneInfo(MARKET_TIMEZONES.get(m, "UTC")))
    minutes = local_now.hour * 60 + local_now.minute
    first_start = MARKET_FIRST_SESSION_START.get(m)
    if first_start is None:
        return False
    return minutes < first_start


def _adjust_snapshot_breakdowns_for_preopen(
    *,
    day_pnl_breakdowns_by_date: Dict[str, Dict[str, float]],
    snapshot_date: str,
    now_utc: datetime,
    market_statuses: Dict[str, Dict[str, str]],
) -> Dict[str, Dict[str, float]]:
    adjusted: Dict[str, Dict[str, float]] = {
        date_str: _round_market_breakdown(market_map)
        for date_str, market_map in (day_pnl_breakdowns_by_date or {}).items()
    }
    snapshot_bucket = adjusted.setdefault(snapshot_date, _empty_market_breakdown())
    for market in ("a", "hk", "fund"):
        if not _is_preopen_off_hours_market(market, now_utc, market_statuses):
            continue
        amount = float(snapshot_bucket.get(market) or 0.0)
        if abs(amount) < 1e-9:
            continue
        previous_day = get_previous_trading_day(market, snapshot_date)
        if previous_day is None:
            continue
        previous_key = previous_day.strftime("%Y-%m-%d")
        previous_bucket = adjusted.setdefault(previous_key, _empty_market_breakdown())
        previous_bucket[market] = round(float(previous_bucket.get(market) or 0.0) + amount, 2)
        snapshot_bucket[market] = 0.0
    return adjusted


def _adjust_asset_breakdowns_for_preopen(
    *,
    asset_day_breakdowns_by_date: Dict[str, List[Dict[str, Any]]],
    snapshot_date: str,
    now_utc: datetime,
    market_statuses: Dict[str, Dict[str, str]],
) -> Dict[str, List[Dict[str, Any]]]:
    """盘前把 snapshot_date 中属于 a/hk/fund 市场的 asset items 挪到上一个交易日。"""
    adjusted: Dict[str, List[Dict[str, Any]]] = {
        date_str: [dict(it) for it in items]
        for date_str, items in (asset_day_breakdowns_by_date or {}).items()
    }
    snapshot_items = adjusted.get(snapshot_date)
    if not snapshot_items:
        return adjusted
    preopen_markets: set[str] = set()
    previous_keys: Dict[str, str] = {}
    for market in ("a", "hk", "fund"):
        if not _is_preopen_off_hours_market(market, now_utc, market_statuses):
            continue
        previous_day = get_previous_trading_day(market, snapshot_date)
        if previous_day is None:
            continue
        preopen_markets.add(market)
        previous_keys[market] = previous_day.strftime("%Y-%m-%d")
    if not preopen_markets:
        return adjusted
    keep: List[Dict[str, Any]] = []
    move: Dict[str, List[Dict[str, Any]]] = {}
    for item in snapshot_items:
        m = str(item.get("market") or "a").strip().lower()
        if m in preopen_markets:
            move.setdefault(previous_keys[m], []).append(item)
        else:
            keep.append(item)
    adjusted[snapshot_date] = keep
    for target_date, items_to_move in move.items():
        existing = adjusted.setdefault(target_date, [])
        existing_by_code: Dict[str, Dict[str, Any]] = {
            str(it.get("code") or ""): it for it in existing
        }
        for item in items_to_move:
            code = str(item.get("code") or "")
            if code in existing_by_code:
                existing_by_code[code]["day_pnl"] = float(existing_by_code[code].get("day_pnl") or 0.0) + float(item.get("day_pnl") or 0.0)
                existing_by_code[code]["day_base"] = float(existing_by_code[code].get("day_base") or 0.0) + float(item.get("day_base") or 0.0)
            else:
                existing.append(dict(item))
                existing_by_code[code] = existing[-1]
    return adjusted


def _resolve_snapshot_exchange_effective_date(
    *,
    market: str,
    now_utc: datetime,
    current_price: float,
    yclose: float,
    market_statuses: Dict[str, Dict[str, str]],
    epsilon: float = 1e-9,
) -> str | None:
    if current_price <= 0 or yclose <= 0:
        return None
    if abs(current_price - yclose) / yclose < epsilon:
        return None

    local_date = _market_local_date(market, now_utc)
    status = market_statuses.get(str(market or "").lower()) or {}
    if bool(status.get("open")):
        return local_date.strftime("%Y-%m-%d")

    if _is_preopen_off_hours_market(market, now_utc, market_statuses):
        previous_day = get_previous_trading_day(market, local_date)
        return previous_day.strftime("%Y-%m-%d") if previous_day is not None else None

    if bool(status.get("trading_day")):
        return local_date.strftime("%Y-%m-%d")

    previous_day = get_previous_trading_day(market, local_date)
    return previous_day.strftime("%Y-%m-%d") if previous_day is not None else None


def _resolve_display_exchange_effective_date(
    *,
    market: str,
    now_utc: datetime,
    market_statuses: Dict[str, Dict[str, str]],
) -> str | None:
    """给“当日展示”选归属日。

    规则：
    - 开盘中：显示本地交易日
    - 盘前：显示 0，不沿用前一交易日
    - 当天交易已结束但仍属本地交易日：继续显示这一天
    - 非交易日：显示 0
    """
    local_date = _market_local_date(market, now_utc)
    status = market_statuses.get(str(market or "").lower()) or {}
    if not bool(status.get("trading_day")):
        return None
    if bool(status.get("open")):
        return local_date.strftime("%Y-%m-%d")
    if _is_preopen_off_hours_market(market, now_utc, market_statuses):
        return None
    return local_date.strftime("%Y-%m-%d")


def _resolve_display_fund_effective_date(
    *,
    now_utc: datetime,
    market_statuses: Dict[str, Dict[str, str]],
    nav_effective_date: str | None,
) -> str | None:
    """给场外基金的“当日展示”选归属日。

    只展示“今天已经拿到并归属到今天”的净值变化：
    - 盘前不展示
    - 不是今天的净值，不拿来冒充今天
    """
    effective_date = str(nav_effective_date or "").strip()[:10]
    if not effective_date:
        return None
    local_today = _market_local_date("fund", now_utc).strftime("%Y-%m-%d")
    if effective_date != local_today:
        return None
    if _is_preopen_off_hours_market("fund", now_utc, market_statuses):
        return None
    status = market_statuses.get("fund") or {}
    if bool(status.get("trading_day")):
        return local_today
    return None


def _rate_to_cny(curr: Any, rates: Dict[str, Any]) -> float:
    code = str(curr or "CNY").strip().upper()
    if code == "CNY":
        return 1.0
    try:
        rate = float((rates or {}).get(code, 0.0) or 0.0)
    except Exception:
        rate = 0.0
    if rate > 0:
        return rate
    logger.warning("_rate_to_cny: 汇率缺失或为零 curr=%s, fallback 1.0, 外币资产金额可能严重失真", code)
    return 1.0


def _asset_amount_to_cny(asset: Dict[str, Any], rates: Dict[str, Any], use_abs: bool = False) -> float:
    amount = float(asset.get("amount") or 0.0)
    if use_abs:
        amount = abs(amount)
    return amount * _rate_to_cny(asset.get("curr"), rates)


def _empty_market_breakdown() -> Dict[str, float]:
    return {market: 0.0 for market in DEFAULT_MARKETS}


def _add_market_breakdown(
    day_pnl_breakdowns_by_date: Dict[str, Dict[str, float]],
    effective_date: str | None,
    market: str,
    amount: float,
) -> None:
    if not effective_date:
        return
    normalized_market = market if market in DEFAULT_MARKETS else "a"
    bucket = day_pnl_breakdowns_by_date.setdefault(effective_date, _empty_market_breakdown())
    bucket[normalized_market] += float(amount or 0.0)


def _add_day_pnl_base(
    day_pnl_bases_by_date: Dict[str, float],
    effective_date: str | None,
    amount: float,
) -> None:
    if not effective_date:
        return
    day_pnl_bases_by_date[effective_date] = float(day_pnl_bases_by_date.get(effective_date, 0.0) or 0.0) + float(amount or 0.0)


def _add_asset_day_breakdown(
    asset_day_breakdowns_by_date: Dict[str, Dict[str, Dict[str, Any]]],
    *,
    effective_date: str | None,
    code: str,
    name: str,
    market: str,
    curr: str,
    day_pnl: float,
    day_base: float,
) -> None:
    if not effective_date or not code:
        return
    bucket = asset_day_breakdowns_by_date.setdefault(str(effective_date), {})
    item = bucket.setdefault(
        str(code),
        {
            "code": str(code),
            "name": str(name or code),
            "market": str(market or "a"),
            "curr": str(curr or "CNY").upper(),
            "day_pnl": 0.0,
            "day_base": 0.0,
        },
    )
    item["day_pnl"] = float(item.get("day_pnl") or 0.0) + float(day_pnl or 0.0)
    item["day_base"] = float(item.get("day_base") or 0.0) + float(day_base or 0.0)


def _normalize_asset_breakdowns_by_date(
    asset_day_breakdowns_by_date: Dict[str, Dict[str, Dict[str, Any]]],
) -> Dict[str, List[Dict[str, Any]]]:
    normalized: Dict[str, List[Dict[str, Any]]] = {}
    for date_str, code_map in (asset_day_breakdowns_by_date or {}).items():
        items: List[Dict[str, Any]] = []
        for code in sorted((code_map or {}).keys()):
            raw = code_map[code] or {}
            items.append(
                {
                    "code": str(raw.get("code") or code),
                    "name": str(raw.get("name") or code),
                    "market": str(raw.get("market") or "a"),
                    "curr": str(raw.get("curr") or "CNY").upper(),
                    "day_pnl": round(float(raw.get("day_pnl") or 0.0), 2),
                    "day_base": round(float(raw.get("day_base") or 0.0), 2),
                }
            )
        # 尾差分摊：确保 sum(rounded items) == round(raw total, 2)
        if items:
            total_rounded = sum(it["day_pnl"] for it in items)
            total_raw = round(sum(float((code_map.get(c) or {}).get("day_pnl") or 0.0) for c in code_map), 2)
            penny = round(total_raw - total_rounded, 2)
            if abs(penny) > 0:
                idx = max(range(len(items)), key=lambda i: abs(items[i]["day_pnl"]))
                items[idx]["day_pnl"] = round(items[idx]["day_pnl"] + penny, 2)
        normalized[str(date_str)] = items
    return normalized


def _ensure_snapshot_date_asset_breakdowns(
    asset_day_breakdowns_by_date: Dict[str, List[Dict[str, Any]]],
    *,
    portfolio: List[Dict[str, Any]],
    snapshot_date: str,
    unresolved_nav_codes: set[str] | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    if not snapshot_date:
        return asset_day_breakdowns_by_date

    normalized: Dict[str, List[Dict[str, Any]]] = {
        str(date_str): [dict(item or {}) for item in items or []]
        for date_str, items in (asset_day_breakdowns_by_date or {}).items()
    }
    snapshot_items = normalized.setdefault(str(snapshot_date), [])
    existing_codes = {
        str((item or {}).get("code") or "").strip()
        for item in snapshot_items
        if str((item or {}).get("code") or "").strip()
    }

    unresolved_codes = {str(code or "").strip() for code in (unresolved_nav_codes or set())}
    missing_items: List[Dict[str, Any]] = []
    for asset in portfolio or []:
        code = str((asset or {}).get("code") or "").strip()
        qty = float((asset or {}).get("qty") or 0.0)
        if not code or qty <= 0 or code in existing_codes or code in unresolved_codes:
            continue
        market = market_from_asset(asset)
        if market not in DEFAULT_MARKETS:
            market = "a"
        missing_items.append(
            {
                "code": code,
                "name": str((asset or {}).get("name") or code),
                "market": market,
                "curr": str((asset or {}).get("curr") or "CNY").upper(),
                "day_pnl": 0.0,
                "day_base": 0.0,
            }
        )
        existing_codes.add(code)

    if missing_items:
        snapshot_items.extend(sorted(missing_items, key=lambda item: str(item.get("code") or "")))
        normalized[str(snapshot_date)] = sorted(
            snapshot_items,
            key=lambda item: str((item or {}).get("code") or ""),
        )
    return normalized


def _round_market_breakdown(data: Dict[str, float] | None) -> Dict[str, float]:
    normalized = _empty_market_breakdown()
    for market in DEFAULT_MARKETS:
        normalized[market] = round(float((data or {}).get(market, 0.0) or 0.0), 2)
    return normalized


def _pick_latest_prior_effective_date(
    day_pnl_breakdowns_by_date: Dict[str, Dict[str, float]],
    *,
    snapshot_date: str,
    market: str,
) -> str | None:
    candidates = []
    for effective_date, market_map in (day_pnl_breakdowns_by_date or {}).items():
        if not effective_date or effective_date >= snapshot_date:
            continue
        value = float((market_map or {}).get(market, 0.0) or 0.0)
        if abs(value) < 0.005:
            continue
        candidates.append(str(effective_date))
    return max(candidates) if candidates else None


def _has_ledger_daily_snapshot(
    db_obj,
    *,
    date_str: str,
    user_id: str | None,
    ledger_id: int,
) -> bool:
    conn = db_obj.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM ledger_daily_snapshots
            WHERE date = ? AND user_id = ? AND ledger_id = ?
            LIMIT 1
            """,
            (str(date_str or ""), str(user_id or ""), int(ledger_id)),
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def _persist_late_effective_date_settlements(
    db_obj,
    logger_obj,
    stats: Dict[str, Any],
    user_id: str | None,
    *,
    ledger_id: int | None = None,
) -> set[str]:
    """把晚到收益按 effective_date 整天覆盖回填到对应日期。"""
    snapshot_date = str(stats.get("snapshot_date") or "").strip()
    day_pnl_breakdowns_by_date = stats.get("day_pnl_breakdowns_by_date") or {}
    asset_day_breakdowns_by_date = stats.get("asset_day_breakdowns_by_date") or {}
    if not snapshot_date or not day_pnl_breakdowns_by_date:
        return set()

    latest_prior_dates = {
        market: _pick_latest_prior_effective_date(
            day_pnl_breakdowns_by_date,
            snapshot_date=snapshot_date,
            market=market,
        )
        for market in LATE_SETTLEMENT_MARKETS
    }

    candidate_dates = sorted({
        str(effective_date)
        for effective_date in latest_prior_dates.values()
        if effective_date
    })

    handled_dates: set[str] = set()
    for effective_date in candidate_dates:
        if not effective_date:
            continue
        impacted_markets = {
            market
            for market, market_effective_date in latest_prior_dates.items()
            if market_effective_date == effective_date
        }
        if not impacted_markets:
            continue
        if ledger_id is None:
            if not db_obj.has_daily_snapshot(effective_date, user_id=user_id):
                continue
        else:
            if not _has_ledger_daily_snapshot(
                db_obj,
                date_str=effective_date,
                user_id=user_id,
                ledger_id=ledger_id,
            ):
                continue

        existing_market_map = db_obj.get_daily_snapshot_market_breakdown_map(
            effective_date,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        market_map = _round_market_breakdown(existing_market_map)
        late_market_map = _round_market_breakdown(day_pnl_breakdowns_by_date.get(effective_date))
        for market in impacted_markets:
            market_map[market] = round(float(late_market_map.get(market, 0.0) or 0.0), 2)
        existing_asset_items = db_obj.get_daily_snapshot_asset_breakdown_rows(
            date_str=effective_date,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        late_asset_items = [
            item
            for item in (asset_day_breakdowns_by_date.get(effective_date) or [])
            if str(item.get("market") or "").strip().lower() in impacted_markets
        ]
        late_asset_codes = {
            str(item.get("code") or "").strip()
            for item in late_asset_items
            if str(item.get("code") or "").strip()
        }
        asset_items = [
            item
            for item in existing_asset_items
            if (
                str(item.get("market") or "").strip().lower() not in impacted_markets
                # 晚到净值只会带回实际发生变化的基金。保留当天原有的
                # 零收益行，避免回填时把仍在持有、但净值未变的基金删掉。
                or (
                    str(item.get("code") or "").strip() not in late_asset_codes
                    and abs(float(item.get("day_pnl") or 0.0)) < 0.005
                    and abs(float(item.get("day_base") or 0.0)) < 0.005
                )
            )
        ]
        asset_items.extend(late_asset_items)
        total_day_pnl = round(sum(float(v or 0.0) for v in market_map.values()), 2)
        if abs(total_day_pnl) < 0.005:
            continue

        if ledger_id is None:
            ok = db_obj.save_daily_snapshot_market_breakdown(
                date_str=effective_date,
                day_pnl_by_market=market_map,
                total_day_pnl=total_day_pnl,
                user_id=user_id,
                snapshot_date=snapshot_date,
                source="backfill",
                confidence=1.0,
            )
        else:
            ok = db_obj.save_ledger_daily_snapshot_market_breakdown(
                user_id=str(user_id or ""),
                ledger_id=int(ledger_id),
                date_str=effective_date,
                day_pnl_by_market=market_map,
                total_day_pnl=total_day_pnl,
                snapshot_date=snapshot_date,
                source="backfill",
                confidence=1.0,
            )
        if not ok:
            logger_obj.warning(
                "Late settlement full-date save failed: user=%s ledger_id=%s date=%s",
                user_id,
                ledger_id,
                effective_date,
            )
            continue
        if ledger_id is None:
            asset_ok = db_obj.save_daily_snapshot_asset_breakdowns(
                date_str=effective_date,
                items=asset_items,
                user_id=user_id,
                snapshot_date=snapshot_date,
                source="exact",
                confidence=1.0,
                replace_existing=True,
            )
        else:
            asset_ok = db_obj.save_daily_snapshot_asset_breakdowns(
                date_str=effective_date,
                items=asset_items,
                user_id=str(user_id or ""),
                ledger_id=int(ledger_id),
                snapshot_date=snapshot_date,
                source="exact",
                confidence=1.0,
                replace_existing=True,
            )
        if not asset_ok:
            logger_obj.warning(
                "Late settlement asset breakdown save failed: user=%s ledger_id=%s date=%s",
                user_id,
                ledger_id,
                effective_date,
            )
        handled_dates.add(effective_date)

    for effective_date in sorted(handled_dates):
        if ledger_id is None:
            ok = db_obj.sync_daily_snapshot_day_pnl_from_breakdown(effective_date, user_id=user_id)
        else:
            ok = db_obj.sync_ledger_daily_snapshot_day_pnl_from_breakdown(
                date_str=effective_date,
                user_id=str(user_id or ""),
                ledger_id=int(ledger_id),
            )
        if not ok:
            logger_obj.warning(
                "Late settlement sync failed: user=%s ledger_id=%s date=%s",
                user_id,
                ledger_id,
                effective_date,
            )
    return handled_dates


def persist_snapshot_stats(db_obj, logger_obj, stats: Dict[str, Any], user_id: str | None = None) -> bool:
    """保存当天快照，并把晚到收益按 effective_date 整天覆盖回填。"""
    now_utc = stats.get("now_utc")
    if not isinstance(now_utc, datetime):
        now_utc = datetime.now(timezone.utc)
    snapshot_date = str(stats.get("snapshot_date") or datetime.now().strftime("%Y-%m-%d"))
    market_statuses = get_market_statuses(DEFAULT_MARKETS, now=now_utc)
    persist_breakdowns_by_date = _adjust_snapshot_breakdowns_for_preopen(
        day_pnl_breakdowns_by_date=stats.get("day_pnl_breakdowns_by_date") or {},
        snapshot_date=snapshot_date,
        now_utc=now_utc,
        market_statuses=market_statuses,
    )
    snapshot_market_map = _round_market_breakdown(persist_breakdowns_by_date.get(snapshot_date))
    snapshot_payload = {
        **stats,
        "day_pnl": round(sum(float(v or 0.0) for v in snapshot_market_map.values()), 2),
    }
    success = db_obj.save_daily_snapshot(snapshot_payload, user_id, snapshot_date=snapshot_date)
    if not success:
        return False

    breakdown_ok = db_obj.save_daily_snapshot_market_breakdown(
        date_str=snapshot_date,
        day_pnl_by_market=snapshot_market_map,
        total_day_pnl=sum(float(v or 0.0) for v in snapshot_market_map.values()),
        user_id=user_id,
        source="exact",
        confidence=1.0,
    )
    if not breakdown_ok:
        logger_obj.warning("Market breakdown save failed: user=%s date=%s", user_id, snapshot_date)
    persist_asset_breakdowns_by_date = _adjust_asset_breakdowns_for_preopen(
        asset_day_breakdowns_by_date=stats.get("asset_day_breakdowns_by_date") or {},
        snapshot_date=snapshot_date,
        now_utc=now_utc,
        market_statuses=market_statuses,
    )
    asset_breakdown_ok = db_obj.save_daily_snapshot_asset_breakdowns(
        date_str=snapshot_date,
        items=persist_asset_breakdowns_by_date.get(snapshot_date, []),
        user_id=user_id,
        snapshot_date=snapshot_date,
        source="exact",
        confidence=1.0,
        replace_existing=True,
    )
    if not asset_breakdown_ok:
        logger_obj.warning("Asset breakdown save failed: user=%s date=%s", user_id, snapshot_date)

    persist_stats = {
        **stats,
        "snapshot_day_pnl": snapshot_payload["day_pnl"],
        "snapshot_day_pnl_by_market": snapshot_market_map,
        "day_pnl_breakdowns_by_date": persist_breakdowns_by_date,
        "asset_day_breakdowns_by_date": persist_asset_breakdowns_by_date,
    }
    _persist_late_effective_date_settlements(db_obj, logger_obj, persist_stats, user_id)
    return True

def _persist_ledger_snapshot_stats(
    db_obj,
    logger_obj,
    stats: Dict[str, Any],
    *,
    user_id: str,
    ledger_id: int,
) -> tuple[bool, set[str]]:
    snapshot_date = str(stats.get("snapshot_date") or "").strip()
    if not snapshot_date:
        return False, set()

    now_utc = stats.get("now_utc")
    if not isinstance(now_utc, datetime):
        now_utc = datetime.now(timezone.utc)
    market_statuses = get_market_statuses(DEFAULT_MARKETS, now=now_utc)
    persist_breakdowns_by_date = _adjust_snapshot_breakdowns_for_preopen(
        day_pnl_breakdowns_by_date=stats.get("day_pnl_breakdowns_by_date") or {},
        snapshot_date=snapshot_date,
        now_utc=now_utc,
        market_statuses=market_statuses,
    )
    snapshot_market_map = _round_market_breakdown(persist_breakdowns_by_date.get(snapshot_date))
    snapshot_day_pnl = round(sum(float(v or 0.0) for v in snapshot_market_map.values()), 2)
    total_cost = round(float(stats.get("total_cost") or 0.0), 2)
    total_pnl = round(float(stats.get("total_pnl") or 0.0), 2)
    total_market_value = round(float(stats.get("total_invest") or 0.0), 2)
    total_pnl_rate = round(total_pnl / total_cost * 100, 2) if total_cost > 0 else 0.0
    holdings_count = int(stats.get("holdings_count") or 0)

    success = db_obj.save_ledger_daily_snapshot(
        user_id=str(user_id or ""),
        ledger_id=int(ledger_id),
        date_str=snapshot_date,
        total_market_value=total_market_value,
        total_cost=total_cost,
        total_pnl=total_pnl,
        total_pnl_rate=total_pnl_rate,
        day_pnl=snapshot_day_pnl,
        snapshot_date=snapshot_date,
        source="recalculated",
        holdings_count=holdings_count,
    )
    if not success:
        return False, set()

    breakdown_ok = db_obj.save_ledger_daily_snapshot_market_breakdown(
        user_id=str(user_id or ""),
        ledger_id=int(ledger_id),
        date_str=snapshot_date,
        day_pnl_by_market=snapshot_market_map,
        total_day_pnl=snapshot_day_pnl,
        snapshot_date=snapshot_date,
        source="recalculated",
        confidence=1.0,
    )
    if not breakdown_ok:
        logger_obj.warning(
            "Ledger market breakdown save failed: user=%s ledger_id=%s date=%s",
            user_id,
            ledger_id,
            snapshot_date,
        )
    persist_asset_breakdowns_by_date = _adjust_asset_breakdowns_for_preopen(
        asset_day_breakdowns_by_date=stats.get("asset_day_breakdowns_by_date") or {},
        snapshot_date=snapshot_date,
        now_utc=now_utc,
        market_statuses=market_statuses,
    )
    asset_breakdown_ok = db_obj.save_daily_snapshot_asset_breakdowns(
        date_str=snapshot_date,
        items=persist_asset_breakdowns_by_date.get(snapshot_date, []),
        user_id=str(user_id or ""),
        ledger_id=int(ledger_id),
        snapshot_date=snapshot_date,
        source="exact",
        confidence=1.0,
        replace_existing=True,
    )
    if not asset_breakdown_ok:
        logger_obj.warning(
            "Ledger asset breakdown save failed: user=%s ledger_id=%s date=%s",
            user_id,
            ledger_id,
            snapshot_date,
        )

    persist_stats = {
        **stats,
        "snapshot_day_pnl": snapshot_day_pnl,
        "snapshot_day_pnl_by_market": snapshot_market_map,
        "day_pnl_breakdowns_by_date": persist_breakdowns_by_date,
        "asset_day_breakdowns_by_date": persist_asset_breakdowns_by_date,
    }
    handled_dates = _persist_late_effective_date_settlements(
        db_obj,
        logger_obj,
        persist_stats,
        user_id,
        ledger_id=ledger_id,
    )
    handled_dates.add(snapshot_date)
    return True, handled_dates


def _sum_market_breakdowns_by_date(
    stats_list: Iterable[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    combined: Dict[str, Dict[str, float]] = {}
    for stats in stats_list:
        for date_str, market_map in (stats.get("day_pnl_breakdowns_by_date") or {}).items():
            bucket = combined.setdefault(str(date_str), _empty_market_breakdown())
            for market in DEFAULT_MARKETS:
                bucket[market] = round(
                    float(bucket.get(market, 0.0) or 0.0) + float((market_map or {}).get(market, 0.0) or 0.0),
                    2,
                )
    return {date_str: _round_market_breakdown(market_map) for date_str, market_map in combined.items()}


def _sum_day_pnl_bases_by_date(stats_list: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    combined: Dict[str, float] = {}
    for stats in stats_list:
        for date_str, value in (stats.get("day_pnl_bases_by_date") or {}).items():
            combined[str(date_str)] = round(
                float(combined.get(str(date_str), 0.0) or 0.0) + float(value or 0.0),
                2,
            )
    return combined


def _sum_asset_breakdowns_by_date(stats_list: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    combined: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for stats in stats_list:
        for date_str, items in (stats.get("asset_day_breakdowns_by_date") or {}).items():
            day_bucket = combined.setdefault(str(date_str), {})
            for raw in items or []:
                code = str((raw or {}).get("code") or "").strip()
                if not code:
                    continue
                item = day_bucket.setdefault(
                    code,
                    {
                        "code": code,
                        "name": str((raw or {}).get("name") or code),
                        "market": str((raw or {}).get("market") or "a"),
                        "curr": str((raw or {}).get("curr") or "CNY").upper(),
                        "day_pnl": 0.0,
                        "day_base": 0.0,
                    },
                )
                item["day_pnl"] = float(item.get("day_pnl") or 0.0) + float((raw or {}).get("day_pnl") or 0.0)
                item["day_base"] = float(item.get("day_base") or 0.0) + float((raw or {}).get("day_base") or 0.0)
    return _normalize_asset_breakdowns_by_date(combined)


def _list_user_ledgers(user_id: str | None) -> list[Dict[str, Any]]:
    if not user_id:
        return []
    try:
        ledgers = db.get_ledgers(user_id)
    except Exception:
        return []
    result: list[Dict[str, Any]] = []
    for ledger in ledgers or []:
        try:
            ledger_id = int(ledger.get("id"))
        except Exception:
            continue
        result.append({**ledger, "id": ledger_id})
    return result


def _calculate_portfolio_stats_direct(
    user_id: str | None = None,
    *,
    now_utc: datetime | None = None,
    ledger_id: int | None = None,
    include_non_invest_assets: bool = True,
) -> Dict[str, Any]:
    """
    计算当前时刻的投资组合统计数据
    
    Returns:
        {
            'total_invest': float, # 投资总市值
            'total_cash': float,   # 现金总额
            'total_other': float,  # 其他资产
            'total_liability': float, # 负债
            'total_asset': float,  # 总净资产
            'total_pnl': float,    # 累计盈亏
            'day_pnl': float       # 今日盈亏
        }
    """
    # 1. 获取所有基础数据
    portfolio = db.get_portfolio(user_id=user_id, include_closed=True, ledger_id=ledger_id)
    cash_assets = db.get_cash_assets(user_id=user_id) if include_non_invest_assets else []
    other_assets = db.get_other_assets(user_id=user_id) if include_non_invest_assets else []
    liabilities = db.get_liabilities(user_id=user_id) if include_non_invest_assets else []
    
    # 2. 获取实时价格和汇率
    codes = [p['code'] for p in portfolio]
    prices = batch_get_prices(codes)
    rates = get_forex_rates()
    
    # 3. 计算投资资产 stats
    invest_mv = 0.0
    total_pnl = 0.0
    day_pnl_breakdowns_by_date: Dict[str, Dict[str, float]] = {}
    day_pnl_bases_by_date: Dict[str, float] = {}
    asset_day_breakdowns_by_date: Dict[str, Dict[str, Dict[str, Any]]] = {}
    display_day_pnl_breakdowns_by_date: Dict[str, Dict[str, float]] = {}
    display_day_pnl_bases_by_date: Dict[str, float] = {}
    now_utc = now_utc or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    market_statuses = get_market_statuses(DEFAULT_MARKETS, now=now_utc)
    market_trading_days = {
        market: _market_trading_day_now(market, now_utc, market_statuses)
        for market in DEFAULT_MARKETS
    }
    snapshot_date = now_utc.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    today_buys_by_effective_date = db.get_buy_transactions_grouped_by_effective_date(
        user_id=user_id,
        ledger_id=ledger_id,
    )
    today_sells_by_effective_date = db.get_sell_transactions_grouped_by_effective_date(
        user_id=user_id,
        ledger_id=ledger_id,
    )
    otc_fund_codes = [
        code for code in codes
        if str(code or "").lower().startswith(("f_", "ft_")) and not is_exchange_fund_code(code)
    ]
    latest_nav_dates = {
        code: get_fund_latest_nav_date(code)
        for code in otc_fund_codes
    } if otc_fund_codes else {}
    unresolved_nav_codes: set[str] = set()
    for asset in portfolio:
        code = asset['code']
        qty = float(asset['qty'])
        cost = float(asset['price'])
        curr = asset['curr']
        adj = float(asset['adjustment'] or 0)
        
        # 汇率
        rate = _rate_to_cny(curr, rates)
        
        # 价格数据
        price_data = prices.get(code, (0, 0, 0, 0))
        cur_price = price_data[0]
        yclose = price_data[1]
        
        # 如果获取失败或为0，优先昨收，其次仅允许正成本价兜底，避免负成本导致负行情
        if cur_price <= 0:
            if yclose > 0:
                cur_price = yclose
            elif cost > 0:
                cur_price = cost
            else:
                cur_price = 0.0

        if yclose > 0:
            yclose_ref = yclose
        elif cost > 0:
            yclose_ref = cost
        else:
            yclose_ref = 0.0
        
        # 计算单项指标 (转换为CNY)
        item_mv = cur_price * qty * rate
        market = market_from_asset(asset)
        if market not in DEFAULT_MARKETS:
            market = "a"
        # 场外基金（f_/ft_ 开头且非场内 ETF）白天净值尚未更新，
        # 价格源返回的是昨日净值，算出来是昨天的涨跌而非今天的，必须跳过
        nav_update_pending = code.lower().startswith(("f_", "ft_")) and not is_exchange_fund_code(code)
        item_float_pnl = (cur_price - cost) * qty * rate
        item_total_pnl = item_float_pnl + (adj * rate)

        if nav_update_pending:
            nav_date = latest_nav_dates.get(code)
            if not nav_date and len(price_data) >= 5:
                nav_date = str(price_data[4] or "").strip() or None
            effective_date = resolve_fund_nav_effective_date(nav_date)
            has_confirmed_nav = price_data[0] > 0 and price_data[1] > 0
            display_effective_date = _resolve_display_fund_effective_date(
                now_utc=now_utc,
                market_statuses=market_statuses,
                nav_effective_date=effective_date,
            )
            effective_qty = (
                    db.get_position_qty_as_of_effective_date(
                        code,
                        effective_date,
                        user_id=user_id,
                        ledger_id=ledger_id,
                    )
                if effective_date else 0.0
            )
            if not effective_date or not has_confirmed_nav:
                # 取价失败时不能伪造“净值不变”的 0，后续历史源恢复后再回填。
                unresolved_nav_codes.add(code)
            elif effective_qty > 0 and abs(cur_price - yclose_ref) / yclose_ref >= 1e-9:
                item_day_pnl = (cur_price - yclose_ref) * effective_qty * rate
                item_day_base = yclose_ref * effective_qty * rate
                _add_market_breakdown(day_pnl_breakdowns_by_date, effective_date, market, item_day_pnl)
                _add_day_pnl_base(
                    day_pnl_bases_by_date,
                    effective_date,
                    item_day_base,
                )
                _add_asset_day_breakdown(
                    asset_day_breakdowns_by_date,
                    effective_date=effective_date,
                    code=code,
                    name=str(asset.get("name") or code),
                    market=market,
                    curr=curr,
                    day_pnl=item_day_pnl,
                    day_base=item_day_base,
                )
                if display_effective_date == effective_date:
                    _add_market_breakdown(
                        display_day_pnl_breakdowns_by_date,
                        display_effective_date,
                        market,
                        item_day_pnl,
                    )
                    _add_day_pnl_base(
                        display_day_pnl_bases_by_date,
                        display_effective_date,
                        yclose_ref * effective_qty * rate,
                    )
            elif effective_qty > 0:
                # 已确认的两日净值相同也要留下资产明细，供收益日历显示为 0。
                _add_asset_day_breakdown(
                    asset_day_breakdowns_by_date,
                    effective_date=effective_date,
                    code=code,
                    name=str(asset.get("name") or code),
                    market=market,
                    curr=curr,
                    day_pnl=0.0,
                    day_base=0.0,
                )
        else:
            effective_date = _resolve_snapshot_exchange_effective_date(
                market=market,
                now_utc=now_utc,
                current_price=cur_price,
                yclose=yclose_ref,
                market_statuses=market_statuses,
            )
            if not effective_date and yclose > 0:
                market_date = _market_local_date(market, now_utc).strftime("%Y-%m-%d")
                if (today_sells_by_effective_date.get(market_date) or {}).get(code):
                    effective_date = market_date
            display_effective_date = _resolve_display_exchange_effective_date(
                market=market,
                now_utc=now_utc,
                market_statuses=market_statuses,
            )
            if effective_date:
                buy_info = (today_buys_by_effective_date.get(effective_date) or {}).get(code)
                sell_info = (today_sells_by_effective_date.get(effective_date) or {}).get(code)

                sold_qty = 0.0
                sold_amount = 0.0
                if sell_info and sell_info.get("qty", 0) > 0:
                    sold_qty = float(sell_info["qty"])
                    sold_amount = float(sell_info["amount"])

                # 已清仓且当日无买卖，跳过日内收益计算和明细写入
                has_buy = buy_info and buy_info.get("qty", 0) > 0
                has_sell = sold_qty > 0
                if qty == 0 and not has_buy and not has_sell:
                    pass  # 跳过，不写 breakdown / asset / display
                elif has_buy:
                    buy_qty_total = float(buy_info["qty"])
                    effective_buy_qty = min(buy_qty_total, qty)
                    effective_avg_price = (float(buy_info["amount"]) / buy_qty_total) if buy_qty_total > 0 else yclose_ref
                    pre_trade_qty = max(0.0, qty - effective_buy_qty)
                    item_day_pnl = (
                        (cur_price - yclose_ref) * pre_trade_qty
                        + (cur_price - effective_avg_price) * effective_buy_qty
                        + (sold_amount - yclose_ref * sold_qty)
                    ) * rate
                    item_day_base = (yclose_ref * (pre_trade_qty + sold_qty) + effective_avg_price * effective_buy_qty) * rate
                    _add_market_breakdown(day_pnl_breakdowns_by_date, effective_date, market, item_day_pnl)
                    _add_day_pnl_base(day_pnl_bases_by_date, effective_date, item_day_base)
                    _add_asset_day_breakdown(
                        asset_day_breakdowns_by_date,
                        effective_date=effective_date,
                        code=code,
                        name=str(asset.get("name") or code),
                        market=market,
                        curr=curr,
                        day_pnl=item_day_pnl,
                        day_base=item_day_base,
                    )
                    if display_effective_date == effective_date:
                        _add_market_breakdown(
                            display_day_pnl_breakdowns_by_date,
                            display_effective_date,
                            market,
                            item_day_pnl,
                        )
                        _add_day_pnl_base(
                            display_day_pnl_bases_by_date,
                            display_effective_date,
                            item_day_base,
                        )
                else:
                    item_day_pnl = ((cur_price - yclose_ref) * qty + (sold_amount - yclose_ref * sold_qty)) * rate
                    item_day_base = yclose_ref * (qty + sold_qty) * rate
                    _add_market_breakdown(day_pnl_breakdowns_by_date, effective_date, market, item_day_pnl)
                    _add_day_pnl_base(day_pnl_bases_by_date, effective_date, item_day_base)
                    _add_asset_day_breakdown(
                        asset_day_breakdowns_by_date,
                        effective_date=effective_date,
                        code=code,
                        name=str(asset.get("name") or code),
                        market=market,
                        curr=curr,
                        day_pnl=item_day_pnl,
                        day_base=item_day_base,
                    )
                    if display_effective_date == effective_date:
                        _add_market_breakdown(
                            display_day_pnl_breakdowns_by_date,
                            display_effective_date,
                            market,
                            item_day_pnl,
                        )
                        _add_day_pnl_base(
                            display_day_pnl_bases_by_date,
                            display_effective_date,
                            item_day_base,
                        )

        # 累加
        invest_mv += item_mv
        total_pnl += item_total_pnl
        
    # 4. 计算非投资资产 stats
    total_cash = sum(_asset_amount_to_cny(a, rates) for a in cash_assets)
    total_other = sum(_asset_amount_to_cny(a, rates) for a in other_assets)
    total_liability = sum(_asset_amount_to_cny(a, rates, use_abs=True) for a in liabilities)
    
    # 5. 今日已实现盈亏（卖出或日内回转差价）已在上方遍历 portfolio 过程的 sold_day_pnl 完全计算并入
    # 至于 total_pnl 在上面计算的是 (当前持仓市值 - 当前持仓成本 + adjustment)。
    # 这里的 adjustment 已经是“旧 portfolio.adjustment + 流水表汇总”的总历史调整值。
    # 所以 total_pnl 已经天然包含所有长期的已实现历史盈亏(realized_pnl) / 分红 / 手工补差。
    
    # 6. 汇总
    total_asset = total_cash + invest_mv + total_other - total_liability
    # today 展示只能认“当前自然日”这一天。
    # 盘前或今日尚无有效收益时直接显示 0，不允许再把上一有效收益日顶到今天。
    active_effective_date = snapshot_date
    realtime_day_pnl_by_market = _round_market_breakdown(display_day_pnl_breakdowns_by_date.get(snapshot_date))
    realtime_day_pnl = round(sum(realtime_day_pnl_by_market.values()), 2)
    realtime_day_pnl_base = round(float(display_day_pnl_bases_by_date.get(snapshot_date) or 0.0), 2)
    snapshot_day_pnl_by_market = _round_market_breakdown(day_pnl_breakdowns_by_date.get(snapshot_date))
    snapshot_day_pnl = round(sum(snapshot_day_pnl_by_market.values()), 2)
    snapshot_day_pnl_base = round(float(day_pnl_bases_by_date.get(snapshot_date) or 0.0), 2)
    rounded_breakdowns_by_date = {
        date_str: _round_market_breakdown(market_map)
        for date_str, market_map in sorted(day_pnl_breakdowns_by_date.items())
    }
    rounded_bases_by_date = {
        date_str: round(float(base or 0.0), 2)
        for date_str, base in sorted(day_pnl_bases_by_date.items())
    }
    
    normalized_asset_breakdowns = _normalize_asset_breakdowns_by_date(asset_day_breakdowns_by_date)
    normalized_asset_breakdowns = _ensure_snapshot_date_asset_breakdowns(
        normalized_asset_breakdowns,
        portfolio=portfolio,
        snapshot_date=snapshot_date,
        unresolved_nav_codes=unresolved_nav_codes,
    )

    return {
        'total_invest': round(invest_mv, 2),
        'total_cost': round(sum(float(asset.get("price") or 0.0) * float(asset.get("qty") or 0.0) * _rate_to_cny(asset.get("curr"), rates) for asset in portfolio), 2),
        'total_cash': round(total_cash, 2),
        'total_other': round(total_other, 2),
        'total_liability': round(total_liability, 2),
        'total_asset': round(total_asset, 2),
        'total_pnl': round(total_pnl, 2),
        'day_pnl': realtime_day_pnl,
        'day_pnl_base': realtime_day_pnl_base,
        'day_pnl_effective_date': active_effective_date,
        'day_pnl_by_market': realtime_day_pnl_by_market,
        'display_day_pnl': realtime_day_pnl,
        'display_day_pnl_base': realtime_day_pnl_base,
        'display_day_pnl_effective_date': active_effective_date,
        'display_day_pnl_by_market': realtime_day_pnl_by_market,
        'snapshot_day_pnl': snapshot_day_pnl,
        'snapshot_day_pnl_base': snapshot_day_pnl_base,
        'snapshot_day_pnl_by_market': snapshot_day_pnl_by_market,
        'day_pnl_breakdowns_by_date': rounded_breakdowns_by_date,
        'day_pnl_bases_by_date': rounded_bases_by_date,
        'asset_day_breakdowns_by_date': normalized_asset_breakdowns,
        'snapshot_date': snapshot_date,
        'now_utc': now_utc,
        'holdings_count': len(portfolio),
        'scope': {
            'ledger_id': ledger_id,
            'mode': 'ledger' if ledger_id is not None else 'global',
        },
    }

def calculate_portfolio_stats(
    user_id: str | None = None,
    now_utc: datetime | None = None,
    ledger_id: int | None = None,
) -> Dict[str, Any]:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)

    if ledger_id is not None:
        return _calculate_portfolio_stats_direct(
            user_id,
            now_utc=now_utc,
            ledger_id=ledger_id,
            include_non_invest_assets=False,
        )

    ledgers = _list_user_ledgers(user_id)
    if not ledgers:
        return _calculate_portfolio_stats_direct(
            user_id,
            now_utc=now_utc,
            ledger_id=None,
            include_non_invest_assets=True,
        )

    ledger_stats_list = [
        _calculate_portfolio_stats_direct(
            user_id,
            now_utc=now_utc,
            ledger_id=int(ledger["id"]),
            include_non_invest_assets=False,
        )
        for ledger in ledgers
    ]
    aggregated_breakdowns = _sum_market_breakdowns_by_date(ledger_stats_list)
    aggregated_bases = _sum_day_pnl_bases_by_date(ledger_stats_list)
    aggregated_asset_breakdowns = _sum_asset_breakdowns_by_date(ledger_stats_list)
    snapshot_date = now_utc.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    effective_date = snapshot_date

    total_invest = round(sum(float(stats.get("total_invest") or 0.0) for stats in ledger_stats_list), 2)
    total_cost = round(sum(float(stats.get("total_cost") or 0.0) for stats in ledger_stats_list), 2)
    total_pnl = round(sum(float(stats.get("total_pnl") or 0.0) for stats in ledger_stats_list), 2)
    total_cash = sum(_asset_amount_to_cny(a, get_forex_rates()) for a in db.get_cash_assets(user_id=user_id))
    total_other = sum(_asset_amount_to_cny(a, get_forex_rates()) for a in db.get_other_assets(user_id=user_id))
    total_liability = sum(_asset_amount_to_cny(a, get_forex_rates(), use_abs=True) for a in db.get_liabilities(user_id=user_id))
    total_asset = round(total_cash + total_invest + total_other - total_liability, 2)
    # display 口径：从各 ledger 的 display_day_pnl_by_market 聚合（盘前归零）
    display_by_market: Dict[str, float] = {m: 0.0 for m in DEFAULT_MARKETS}
    display_base = 0.0
    for stats in ledger_stats_list:
        for m in DEFAULT_MARKETS:
            display_by_market[m] = round(
                display_by_market[m] + float((stats.get("display_day_pnl_by_market") or {}).get(m, 0.0) or 0.0), 2
            )
        display_base += float(stats.get("display_day_pnl_base") or 0.0)
    realtime_day_pnl_by_market = _round_market_breakdown(display_by_market)
    realtime_day_pnl = round(sum(realtime_day_pnl_by_market.values()), 2)
    realtime_day_pnl_base = round(display_base, 2)
    # snapshot 口径：从 aggregated_breakdowns 取（保留前一交易日归属）
    snapshot_day_pnl_by_market = _round_market_breakdown(aggregated_breakdowns.get(snapshot_date))
    snapshot_day_pnl = round(sum(snapshot_day_pnl_by_market.values()), 2)
    snapshot_day_pnl_base = round(float(aggregated_bases.get(snapshot_date) or 0.0), 2)

    return {
        'total_invest': total_invest,
        'total_cost': total_cost,
        'total_cash': round(total_cash, 2),
        'total_other': round(total_other, 2),
        'total_liability': round(total_liability, 2),
        'total_asset': total_asset,
        'total_pnl': total_pnl,
        'day_pnl': realtime_day_pnl,
        'day_pnl_base': realtime_day_pnl_base,
        'day_pnl_effective_date': effective_date,
        'day_pnl_by_market': realtime_day_pnl_by_market,
        'display_day_pnl': realtime_day_pnl,
        'display_day_pnl_base': realtime_day_pnl_base,
        'display_day_pnl_effective_date': effective_date,
        'display_day_pnl_by_market': realtime_day_pnl_by_market,
        'snapshot_day_pnl': snapshot_day_pnl,
        'snapshot_day_pnl_base': snapshot_day_pnl_base,
        'snapshot_day_pnl_by_market': snapshot_day_pnl_by_market,
        'day_pnl_breakdowns_by_date': aggregated_breakdowns,
        'day_pnl_bases_by_date': aggregated_bases,
        'asset_day_breakdowns_by_date': aggregated_asset_breakdowns,
        'snapshot_date': snapshot_date,
        'now_utc': now_utc,
        'holdings_count': sum(int(stats.get("holdings_count") or 0) for stats in ledger_stats_list),
        'scope': {
            'ledger_id': None,
            'mode': 'global',
        },
    }


def is_weekend() -> bool:
    """判断是否周末"""
    return datetime.now().weekday() >= 5


def take_snapshot(user_id: str = None) -> bool:
    """
    执行快照保存

    注意：day_pnl 基于交易日口径计算，非交易日自动为 0
    - 若 user_id 为空，默认对所有用户写快照
    """
    try:
        logger.info("Starting background snapshot task...")

        user_ids = [user_id] if user_id else db.get_user_ids()
        if not user_ids:
            user_ids = [None]

        success_any = False
        for uid in user_ids:
            now_utc = datetime.now(timezone.utc)
            ledgers = _list_user_ledgers(uid)
            if ledgers:
                handled_dates: set[str] = set()
                snapshot_date = now_utc.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
                ledger_stats_list: list[Dict[str, Any]] = []
                for ledger in ledgers:
                    ledger_id = int(ledger["id"])
                    ledger_stats = calculate_portfolio_stats(uid, now_utc=now_utc, ledger_id=ledger_id)
                    ledger_stats_list.append(ledger_stats)
                    ledger_success, ledger_dates = _persist_ledger_snapshot_stats(
                        db,
                        logger,
                        ledger_stats,
                        user_id=str(uid or ""),
                        ledger_id=ledger_id,
                    )
                    success_any = success_any or ledger_success
                    handled_dates.update(ledger_dates)

                # 从已有 ledger_stats 聚合全局数据，避免重复计算
                rates = get_forex_rates()
                total_invest = round(sum(float(s.get("total_invest") or 0.0) for s in ledger_stats_list), 2)
                total_cost = round(sum(float(s.get("total_cost") or 0.0) for s in ledger_stats_list), 2)
                total_pnl = round(sum(float(s.get("total_pnl") or 0.0) for s in ledger_stats_list), 2)
                total_cash = round(sum(_asset_amount_to_cny(a, rates) for a in db.get_cash_assets(user_id=uid)), 2)
                total_other = round(sum(_asset_amount_to_cny(a, rates) for a in db.get_other_assets(user_id=uid)), 2)
                total_liability = round(sum(_asset_amount_to_cny(a, rates, use_abs=True) for a in db.get_liabilities(user_id=uid)), 2)
                total_asset = round(total_cash + total_invest + total_other - total_liability, 2)

                global_success = db.aggregate_daily_snapshot_from_ledgers(
                    user_id=str(uid or ""),
                    date_str=snapshot_date,
                    total_asset=total_asset,
                    total_invest=total_invest,
                    total_cash=total_cash,
                    total_other=total_other,
                    total_liability=total_liability,
                    total_pnl=total_pnl,
                    source="recalculated",
                    snapshot_date=snapshot_date,
                )
                breakdown_success = db.aggregate_daily_snapshot_market_breakdown_from_ledgers(
                    user_id=str(uid or ""),
                    date_str=snapshot_date,
                    snapshot_date=snapshot_date,
                    source="recalculated",
                )
                db.aggregate_daily_snapshot_asset_breakdown_from_ledgers(
                    user_id=str(uid or ""),
                    date_str=snapshot_date,
                    snapshot_date=snapshot_date,
                    source="recalculated",
                )
                db.sync_daily_snapshot_day_pnl_from_breakdown(snapshot_date, user_id=uid)
                for effective_date in sorted(date_str for date_str in handled_dates if date_str != snapshot_date):
                    db.aggregate_daily_snapshot_market_breakdown_from_ledgers(
                        user_id=str(uid or ""),
                        date_str=effective_date,
                        snapshot_date=snapshot_date,
                        source="backfill",
                    )
                    db.aggregate_daily_snapshot_asset_breakdown_from_ledgers(
                        user_id=str(uid or ""),
                        date_str=effective_date,
                        snapshot_date=snapshot_date,
                        source="backfill",
                    )
                    db.sync_daily_snapshot_day_pnl_from_breakdown(effective_date, user_id=uid)

                success_any = success_any or global_success or breakdown_success
                if global_success:
                    logger.info(
                        "Snapshot saved successfully: user=%s total=%s day_pnl(aggregated)",
                        uid,
                        total_asset,
                    )
                else:
                    logger.error("Failed to aggregate global snapshot: user=%s", uid)
            else:
                stats = calculate_portfolio_stats(uid, now_utc=now_utc)
                success = persist_snapshot_stats(db, logger, stats, uid)
                success_any = success_any or success
                if success:
                    logger.info(
                        "Snapshot saved successfully: user=%s total=%s day_pnl=%s",
                        uid,
                        stats["total_asset"],
                        stats["day_pnl"],
                    )
                else:
                    logger.error("Failed to save snapshot to database: user=%s", uid)

        return success_any
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        return False

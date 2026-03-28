"""收益日历点击下钻的逐资产明细读侧。"""

from __future__ import annotations

import bisect
import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Callable, Dict, Iterable, List

from .day_pnl_attribution import resolve_fund_nav_effective_date
from .fund import get_fund_latest_nav_date
from .market_calendar import get_previous_trading_day
from .market_calendar import get_market_statuses, market_from_asset
from .price import is_exchange_fund_code
from .snapshot import _market_trading_day_now, _resolve_snapshot_exchange_effective_date
from .trend import _fetch_fund_history_points, _fetch_stock_history_points

logger = logging.getLogger(__name__)

_HISTORY_YCLOSE_MAX_GAP_DAYS = 20

DEFAULT_MARKETS = ("a", "hk", "us", "fund")
UNALLOCATED_DETAIL_CODE = "__unallocated__"
UNALLOCATED_DETAIL_NAME = "未归因收益"


def _round_amount(value: Any) -> float:
    try:
        return round(float(value or 0.0), 2)
    except Exception:
        return 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return default


def _parse_iso_date(value: str) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _history_gap_is_reasonable(
    *,
    market: str,
    current_date: date,
    previous_date: date,
    max_gap_days: int = _HISTORY_YCLOSE_MAX_GAP_DAYS,
) -> bool:
    if previous_date >= current_date:
        return False
    previous_trading_day = get_previous_trading_day(market, current_date)
    if previous_trading_day is not None and previous_date == previous_trading_day:
        return True
    return (current_date - previous_date).days <= max_gap_days


def _format_scope_title(scope: str, target: date) -> str:
    if scope == "day":
        return f"{target.year}年{target.month:02d}月{target.day:02d}日明细"
    if scope == "month":
        return f"{target.year}年{target.month:02d}月明细"
    return f"{target.year}年明细"


def _sort_detail_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            1 if str(item.get("code") or "") == UNALLOCATED_DETAIL_CODE else 0,
            -abs(float(item.get("pnl") or 0.0)),
            str(item.get("name") or item.get("code") or ""),
            str(item.get("code") or ""),
        ),
    )


class AnalysisAssetBreakdownService:
    """收益日历逐资产明细服务。"""

    def __init__(
        self,
        *,
        db: Any,
        price_batch_getter: Callable[[list[str]], Dict[str, Any]],
        realtime_today_service: Any | None = None,
        rates_getter: Callable[[], Dict[str, float]] | None = None,
        convert_amount: Callable[[float, str, str, Dict[str, float]], float] | None = None,
    ) -> None:
        self.db = db
        self.price_batch_getter = price_batch_getter
        self.realtime_today_service = realtime_today_service
        self.rates_getter = rates_getter
        self.convert_amount = convert_amount

    def build_payload(
        self,
        *,
        scope: str,
        raw_date: str,
        user_id: str | None,
        ledger_id: int | None = None,
    ) -> Dict[str, Any]:
        target = _parse_iso_date(raw_date)
        if scope not in {"day", "month", "year"} or target is None:
            return {"error": "Invalid scope or date", "code": "INVALID_CALENDAR_DETAIL"}

        if scope == "day":
            result = self._build_day_payload(target, user_id=user_id, ledger_id=ledger_id)
        elif scope == "month":
            result = self._build_period_payload("month", target, user_id=user_id, ledger_id=ledger_id)
        else:
            result = self._build_period_payload("year", target, user_id=user_id, ledger_id=ledger_id)

        return {
            "scope": scope,
            "date": target.strftime("%Y-%m-%d"),
            "title": _format_scope_title(scope, target),
            "total_pnl": _round_amount(result.get("total_pnl")),
            "total_rate": result.get("total_rate"),
            "items": _sort_detail_items(result.get("items") or []),
        }

    def _build_day_payload(
        self,
        target: date,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any]:
        realtime = self._load_realtime_payload(user_id=user_id, ledger_id=ledger_id)
        realtime_effective_date = _parse_iso_date(str(realtime.get("effective_date") or ""))
        if realtime_effective_date == target:
            result = self._build_realtime_day_payload(
                target,
                realtime_payload=realtime,
                user_id=user_id,
                ledger_id=ledger_id,
            )
            if result is not None:
                return result
        return self._build_historical_day_payload(
            target,
            user_id=user_id,
            ledger_id=ledger_id,
        )

    def _build_period_payload(
        self,
        scope: str,
        target: date,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any]:
        start_date, end_date = self._resolve_period_bounds(scope, target)
        snapshot_rows = self._fetch_snapshot_rows(
            start_date,
            end_date,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        if not snapshot_rows:
            return {"total_pnl": 0.0, "total_rate": 0.0, "items": []}
        persisted_by_date = self.db.get_daily_snapshot_asset_breakdown_rows_by_period(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            user_id=user_id,
            ledger_id=ledger_id,
        )

        needs_history_fallback = any(not persisted_by_date.get(str(row.get("date") or "")) for row in snapshot_rows)
        context = (
            self._build_period_context(
                start_date,
                end_date,
                user_id=user_id,
                ledger_id=ledger_id,
            )
            if needs_history_fallback
            else None
        )
        aggregated: Dict[str, Dict[str, Any]] = {}
        for row in snapshot_rows:
            row_date = str(row.get("date") or "")
            persisted_items = self._build_persisted_day_items(
                persisted_by_date.get(row_date) or [],
            )
            if persisted_items:
                one_day = persisted_items
            elif context is not None:
                one_day = self._build_historical_day_items(
                    _parse_iso_date(row_date),
                    context=context,
                )
            else:
                one_day = []
            for item in one_day:
                bucket = aggregated.setdefault(
                    str(item["code"]),
                    {
                        "code": item["code"],
                        "name": item["name"],
                        "market": item["market"],
                        "curr": item["curr"],
                        "pnl": 0.0,
                        "first_base": None,
                        "has_exposure": False,
                    },
                )
                bucket["pnl"] = float(bucket.get("pnl") or 0.0) + float(item.get("pnl") or 0.0)
                if bucket.get("first_base") is None and float(item.get("base") or 0.0) > 0:
                    bucket["first_base"] = float(item.get("base") or 0.0)
                if item.get("has_exposure"):
                    bucket["has_exposure"] = True

        expected_total = _round_amount(sum(float(row.get("pnl") or 0.0) for row in snapshot_rows))
        items = self._finalize_items(
            aggregated.values(),
            expected_total=expected_total,
        )
        total_rate = self._compute_period_total_rate(
            snapshot_rows,
            start_date,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        return {
            "total_pnl": expected_total,
            "total_rate": total_rate,
            "items": items,
        }

    def _build_realtime_day_payload(
        self,
        target: date,
        *,
        realtime_payload: Dict[str, Any],
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any] | None:
        if self.realtime_today_service is None:
            return None

        target_key = target.strftime("%Y-%m-%d")
        realtime_asset_breakdowns = realtime_payload.get("asset_day_breakdowns_by_date")
        if isinstance(realtime_asset_breakdowns, dict) and target_key in realtime_asset_breakdowns:
            totals = realtime_payload.get("totals") or {}
            items = self._build_realtime_items_from_payload(
                realtime_asset_breakdowns.get(target_key) or [],
            )
            return {
                "total_pnl": _round_amount(totals.get("day_pnl")),
                "total_rate": _round_amount(totals.get("day_pnl_rate")),
                "items": self._finalize_items(
                    items,
                    expected_total=_round_amount(totals.get("day_pnl")),
                ),
            }

        now_utc = datetime.now(timezone.utc)
        rates = self._get_rates()
        context = self._build_period_context(
            target,
            target,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        if not context["codes"]:
            totals = realtime_payload.get("totals") or {}
            return {
                "total_pnl": _round_amount(totals.get("day_pnl")),
                "total_rate": _round_amount(totals.get("day_pnl_rate")),
                "items": [],
            }

        market_statuses = get_market_statuses(list(DEFAULT_MARKETS), now=now_utc)
        latest_nav_dates = {
            code: get_fund_latest_nav_date(code)
            for code in context["codes"]
            if self._is_otc_fund(context["meta"].get(code) or {})
        }
        quotes = self.price_batch_getter(list(context["codes"])) if context["codes"] else {}
        buy_map = context["buy_by_date"].get(target.strftime("%Y-%m-%d"), {})
        sell_map = context["sell_by_date"].get(target.strftime("%Y-%m-%d"), {})

        aggregated: Dict[str, Dict[str, Any]] = {}
        for code in context["codes"]:
            meta = context["meta"].get(code) or {}
            qty = float(context["current_qty_map"].get(code, 0.0) or 0.0)
            curr = str(meta.get("curr") or "CNY").upper()
            market = self._normalize_market(meta)
            quote = quotes.get(code) or (0.0, 0.0, 0.0, 0.0)
            current_price = _safe_float(quote[0])
            yclose = _safe_float(quote[1])
            rate_to_cny = self._rate_to_cny(curr, rates)
            item_pnl = 0.0
            item_base = 0.0
            has_exposure = qty > 0 or code in buy_map or code in sell_map

            if self._is_otc_fund(meta):
                effective_date = resolve_fund_nav_effective_date(latest_nav_dates.get(code))
                if effective_date == target.strftime("%Y-%m-%d"):
                    effective_qty = float(
                        self.db.get_position_qty_as_of_effective_date(
                            code,
                            effective_date,
                            user_id=user_id,
                            ledger_id=ledger_id,
                        )
                        or 0.0
                    )
                    if current_price > 0 and yclose > 0 and effective_qty > 0:
                        item_pnl = (current_price - yclose) * effective_qty * rate_to_cny
                        item_base = yclose * effective_qty * rate_to_cny
                        has_exposure = True
            else:
                effective_date = _resolve_snapshot_exchange_effective_date(
                    market=market,
                    now_utc=now_utc,
                    current_price=current_price,
                    yclose=yclose,
                    market_statuses=market_statuses,
                )
                if effective_date == target.strftime("%Y-%m-%d"):
                    buy_info = buy_map.get(code) or {}
                    sell_info = sell_map.get(code) or {}
                    item_pnl, item_base = self._compute_exchange_day_metrics(
                        qty=qty,
                        current_price=current_price,
                        yclose=yclose,
                        buy_qty=_safe_float(buy_info.get("qty")),
                        buy_amount=_safe_float(buy_info.get("amount")),
                        sell_qty=_safe_float(sell_info.get("qty")),
                        sell_amount=_safe_float(sell_info.get("amount")),
                        cost_fallback=_safe_float(meta.get("price")),
                        rate_to_cny=rate_to_cny,
                        allow_cost_fallback=True,
                    )
                    has_exposure = has_exposure or item_base > 0

            aggregated[code] = {
                "code": code,
                "name": str(meta.get("name") or code),
                "market": market,
                "curr": curr,
                "pnl": item_pnl,
                "base": item_base,
                "has_exposure": has_exposure,
            }

        totals = realtime_payload.get("totals") or {}
        expected_total = _round_amount(totals.get("day_pnl"))
        items = self._finalize_items(aggregated.values(), expected_total=expected_total)
        return {
            "total_pnl": expected_total,
            "total_rate": _round_amount(totals.get("day_pnl_rate")),
            "items": items,
        }

    def _build_realtime_items_from_payload(
        self,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for row in rows or []:
            code = str(row.get("code") or "").strip()
            if not code:
                continue
            pnl = _round_amount(row.get("day_pnl"))
            base = _safe_float(row.get("day_base"))
            if abs(pnl) < 1e-9 and base <= 0:
                continue
            items.append(
                {
                    "code": code,
                    "name": str(row.get("name") or code),
                    "market": str(row.get("market") or "a"),
                    "curr": str(row.get("curr") or "CNY").upper(),
                    "pnl": pnl,
                    "base": base,
                    "has_exposure": True,
                }
            )
        return items

    def _build_historical_day_payload(
        self,
        target: date,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any]:
        persisted_items = self._build_persisted_day_items(
            self.db.get_daily_snapshot_asset_breakdown_rows(
                date_str=target.strftime("%Y-%m-%d"),
                user_id=user_id,
                ledger_id=ledger_id,
            )
        )
        if persisted_items:
            items = persisted_items
        else:
            context = self._build_period_context(
                target,
                target,
                user_id=user_id,
                ledger_id=ledger_id,
            )
            items = self._build_historical_day_items(target, context=context)
        snapshot_rows = self._fetch_snapshot_rows(
            target,
            target,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        expected_total = _round_amount(sum(float(row.get("pnl") or 0.0) for row in snapshot_rows))
        total_base = sum(float(item.get("base") or 0.0) for item in items)
        finalized = self._finalize_items(items, expected_total=expected_total)
        total_rate = round(expected_total / total_base * 100, 2) if total_base > 0 else 0.0
        return {
            "total_pnl": expected_total,
            "total_rate": total_rate,
            "items": finalized,
        }

    def _build_historical_day_items(
        self,
        target: date | None,
        *,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if target is None:
            return []

        date_key = target.strftime("%Y-%m-%d")
        buy_map = context["buy_by_date"].get(date_key, {})
        sell_map = context["sell_by_date"].get(date_key, {})
        result: List[Dict[str, Any]] = []

        for code in context["codes"]:
            meta = context["meta"].get(code) or {}
            curr = str(meta.get("curr") or "CNY").upper()
            rate_to_cny = self._rate_to_cny(curr, context["rates"])
            market = self._normalize_market(meta)
            qty = self._position_qty_as_of(
                context=context,
                code=code,
                target_date=date_key,
            )
            buy_info = buy_map.get(code) or {}
            sell_info = sell_map.get(code) or {}
            has_exposure = qty > 0 or _safe_float(buy_info.get("qty")) > 0 or _safe_float(sell_info.get("qty")) > 0

            if self._is_otc_fund(meta):
                current_price, yclose = self._resolve_history_quote(
                    context=context,
                    code=code,
                    market=market,
                    target_date=date_key,
                )
                item_pnl = 0.0
                item_base = 0.0
                if current_price > 0 and yclose > 0 and qty > 0:
                    item_pnl = (current_price - yclose) * qty * rate_to_cny
                    item_base = yclose * qty * rate_to_cny
            else:
                current_price, yclose = self._resolve_history_quote(
                    context=context,
                    code=code,
                    market=market,
                    target_date=date_key,
                )
                item_pnl, item_base = self._compute_exchange_day_metrics(
                    qty=qty,
                    current_price=current_price,
                    yclose=yclose,
                    buy_qty=_safe_float(buy_info.get("qty")),
                    buy_amount=_safe_float(buy_info.get("amount")),
                    sell_qty=_safe_float(sell_info.get("qty")),
                    sell_amount=_safe_float(sell_info.get("amount")),
                    cost_fallback=_safe_float(meta.get("price")),
                    rate_to_cny=rate_to_cny,
                    allow_cost_fallback=False,
                )
                has_exposure = has_exposure or item_base > 0

            if not has_exposure and abs(item_pnl) < 1e-9:
                continue

            result.append(
                {
                    "code": code,
                    "name": str(meta.get("name") or code),
                    "market": market,
                    "curr": curr,
                    "pnl": item_pnl,
                    "base": item_base,
                    "has_exposure": has_exposure,
                }
            )
        return result

    def _build_persisted_day_items(
        self,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for row in rows or []:
            code = str(row.get("code") or "").strip()
            if not code:
                continue
            pnl = _round_amount(row.get("day_pnl"))
            base = _safe_float(row.get("day_base"))
            # 根据实际数据判断是否有敞口，不硬编码 True
            has_exposure = abs(pnl) >= 1e-9 or abs(base) >= 1e-9
            items.append(
                {
                    "code": code,
                    "name": str(row.get("name") or code),
                    "market": str(row.get("market") or "a"),
                    "curr": str(row.get("curr") or "CNY").upper(),
                    "pnl": pnl,
                    "base": base,
                    "has_exposure": has_exposure,
                }
            )
        return items

    def _build_period_context(
        self,
        start_date: date,
        end_date: date,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any]:
        current_assets = self.db.get_portfolio(
            "all",
            user_id,
            include_closed=True,
            ledger_id=ledger_id,
        )
        tx_rows = self._fetch_transactions_until(
            end_date.strftime("%Y-%m-%d"),
            user_id=user_id,
            ledger_id=ledger_id,
        )
        buy_by_date: Dict[str, Dict[str, Dict[str, float]]] = {}
        sell_by_date: Dict[str, Dict[str, Dict[str, float]]] = {}
        meta: Dict[str, Dict[str, Any]] = {}
        current_qty_map: Dict[str, float] = {}

        for asset in current_assets:
            code = str(asset.get("code") or "").strip()
            if not code:
                continue
            meta[code] = {
                "code": code,
                "name": str(asset.get("name") or code),
                "curr": str(asset.get("curr") or "CNY").upper(),
                "market": self._normalize_market(asset),
                "price": _safe_float(asset.get("price")),
            }
            current_qty_map[code] = _safe_float(asset.get("qty"))

        for row in tx_rows:
            code = str(row.get("code") or "").strip()
            if not code:
                continue
            meta.setdefault(
                code,
                {
                    "code": code,
                    "name": str(row.get("name") or code),
                    "curr": str(row.get("curr") or "CNY").upper(),
                    "market": str(row.get("market") or ""),
                    "price": 0.0,
                },
            )
            effective_date = str(row.get("effective_date") or "").strip()[:10]
            if start_date.strftime("%Y-%m-%d") <= effective_date <= end_date.strftime("%Y-%m-%d"):
                target_map = buy_by_date if str(row.get("type") or "") == "加仓" else sell_by_date
                per_date = target_map.setdefault(effective_date, {})
                bucket = per_date.setdefault(code, {"qty": 0.0, "amount": 0.0})
                bucket["qty"] += _safe_float(row.get("qty"))
                bucket["amount"] += _safe_float(row.get("amount"))

        codes = sorted(meta.keys())
        history_series = self._build_history_series_map(
            codes,
            meta=meta,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "codes": codes,
            "meta": meta,
            "buy_by_date": buy_by_date,
            "sell_by_date": sell_by_date,
            "history_series": history_series,
            "rates": self._get_rates(),
            "position_qty_cache": {},
            "user_id": user_id,
            "ledger_id": ledger_id,
            "current_qty_map": current_qty_map,
        }

    def _build_history_series_map(
        self,
        codes: List[str],
        *,
        meta: Dict[str, Dict[str, Any]],
        start_date: date,
        end_date: date,
    ) -> Dict[str, Dict[str, Any]]:
        lookback_days = max((end_date - start_date).days + 40, 40)
        result: Dict[str, Dict[str, Any]] = {}
        for code in codes:
            info = meta.get(code) or {}
            market = self._normalize_market(info)
            if self._is_otc_fund(info):
                points = _fetch_fund_history_points(code, lookback_days)
            else:
                points = _fetch_stock_history_points(code, lookback_days, market)
            normalized_points = []
            for point in points or []:
                dt_str = str((point or {}).get("date") or "").strip()
                val = _safe_float((point or {}).get("value"))
                if not dt_str or val <= 0:
                    continue
                normalized_points.append((dt_str[:10], val))
            normalized_points.sort(key=lambda item: item[0])
            result[code] = {
                "dates": [item[0] for item in normalized_points],
                "values": [item[1] for item in normalized_points],
            }
        return result

    def _resolve_history_quote(
        self,
        *,
        context: Dict[str, Any],
        code: str,
        market: str,
        target_date: str,
    ) -> tuple[float, float]:
        series = context["history_series"].get(code) or {}
        dates = list(series.get("dates") or [])
        values = list(series.get("values") or [])
        if not dates or not values:
            return 0.0, 0.0
        idx = bisect.bisect_right(dates, target_date) - 1
        if idx < 0:
            return 0.0, 0.0
        current_price = float(values[idx] or 0.0)
        exact_match = dates[idx] == target_date
        if exact_match:
            if idx > 0:
                current_dt = _parse_iso_date(dates[idx])
                previous_dt = _parse_iso_date(dates[idx - 1])
                if (
                    current_dt is not None
                    and previous_dt is not None
                    and _history_gap_is_reasonable(
                        market=market,
                        current_date=current_dt,
                        previous_date=previous_dt,
                    )
                ):
                    return current_price, float(values[idx - 1] or 0.0)
                return current_price, 0.0
            return current_price, 0.0
        return 0.0, 0.0

    def _compute_exchange_day_metrics(
        self,
        *,
        qty: float,
        current_price: float,
        yclose: float,
        buy_qty: float,
        buy_amount: float,
        sell_qty: float,
        sell_amount: float,
        cost_fallback: float,
        rate_to_cny: float,
        allow_cost_fallback: bool = True,
    ) -> tuple[float, float]:
        if current_price <= 0:
            return 0.0, 0.0

        yclose_ref = yclose if yclose > 0 else 0.0
        if yclose_ref <= 0 and allow_cost_fallback and cost_fallback > 0:
            yclose_ref = cost_fallback
        if buy_qty > 0 and yclose_ref <= 0 and buy_amount > 0:
            yclose_ref = buy_amount / buy_qty
        if yclose_ref <= 0:
            return 0.0, 0.0

        sold_qty = max(sell_qty, 0.0)
        sold_amount = max(sell_amount, 0.0)
        if buy_qty > 0 and qty > 0:
            effective_buy_qty = min(buy_qty, qty)
            effective_avg_price = (buy_amount / buy_qty) if buy_qty > 0 else yclose_ref
            pre_trade_qty = max(0.0, qty - effective_buy_qty)
            pnl = (
                (current_price - yclose_ref) * pre_trade_qty
                + (current_price - effective_avg_price) * effective_buy_qty
                + (sold_amount - yclose_ref * sold_qty)
            ) * rate_to_cny
            base = yclose_ref * (pre_trade_qty + sold_qty) * rate_to_cny
            return pnl, base

        pnl = ((current_price - yclose_ref) * qty + (sold_amount - yclose_ref * sold_qty)) * rate_to_cny
        base = yclose_ref * (qty + sold_qty) * rate_to_cny
        return pnl, base

    def _finalize_items(
        self,
        raw_items: Iterable[Dict[str, Any]],
        *,
        expected_total: float,
    ) -> List[Dict[str, Any]]:
        finalized: List[Dict[str, Any]] = []
        for item in raw_items:
            pnl = _round_amount(item.get("pnl"))
            base = float(item.get("base") or item.get("first_base") or 0.0)
            has_exposure = bool(item.get("has_exposure"))
            if not has_exposure and abs(pnl) < 1e-9:
                continue
            finalized.append(
                {
                    "code": str(item.get("code") or ""),
                    "name": str(item.get("name") or item.get("code") or ""),
                    "market": str(item.get("market") or "a"),
                    "curr": str(item.get("curr") or "CNY").upper(),
                    "pnl": pnl,
                    "pnl_rate": round(pnl / base * 100, 2) if base > 0 else None,
                    "base": base,
                    "has_exposure": has_exposure,
                }
            )

        residual = _round_amount(expected_total - sum(float(item.get("pnl") or 0.0) for item in finalized))
        if abs(residual) > 0.05:
            finalized.append(
                {
                    "code": UNALLOCATED_DETAIL_CODE,
                    "name": UNALLOCATED_DETAIL_NAME,
                    "market": "unallocated",
                    "curr": "CNY",
                    "pnl": residual,
                    "pnl_rate": None,
                    "base": 0.0,
                    "has_exposure": True,
                }
            )
        elif finalized and abs(residual) > 0:
            finalized[0]["pnl"] = _round_amount(float(finalized[0]["pnl"] or 0.0) + residual)
            base = float(finalized[0].get("base") or 0.0)
            finalized[0]["pnl_rate"] = round(float(finalized[0]["pnl"] or 0.0) / base * 100, 2) if base > 0 else None

        for item in finalized:
            item.pop("base", None)
            item.pop("has_exposure", None)
        return finalized

    def _fetch_snapshot_rows(
        self,
        start_date: date,
        end_date: date,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        table = "ledger_daily_snapshots" if ledger_id is not None else "daily_snapshots"
        base_column = "total_cost" if ledger_id is not None else "total_invest"
        user_condition, user_params = self._user_filter_sql(user_id)
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_params = (ledger_id,) if ledger_id is not None else ()
        try:
            cursor.execute(
                f"""
                SELECT date, day_pnl, {base_column} AS period_base
                FROM {table}
                WHERE date >= ? AND date <= ? AND {user_condition}{ledger_condition}
                ORDER BY date ASC
                """,
                (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")) + user_params + ledger_params,
            )
            return [
                {
                    "date": str(row["date"] or ""),
                    "pnl": _round_amount(row["day_pnl"]),
                    "period_base": _safe_float(row["period_base"]),
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def _compute_period_total_rate(
        self,
        snapshot_rows: List[Dict[str, Any]],
        start_date: date,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> float:
        if not snapshot_rows:
            return 0.0
        expected_total = _round_amount(sum(float(row.get("pnl") or 0.0) for row in snapshot_rows))
        prev_base = self._fetch_prev_period_base(
            start_date,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        base = prev_base if prev_base > 0 else _safe_float(snapshot_rows[0].get("period_base"))
        return round(expected_total / base * 100, 2) if base > 0 else 0.0

    def _fetch_prev_period_base(
        self,
        start_date: date,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> float:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        table = "ledger_daily_snapshots" if ledger_id is not None else "daily_snapshots"
        base_column = "total_cost" if ledger_id is not None else "total_invest"
        user_condition, user_params = self._user_filter_sql(user_id)
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_params = (ledger_id,) if ledger_id is not None else ()
        try:
            cursor.execute(
                f"""
                SELECT {base_column} AS period_base
                FROM {table}
                WHERE date < ? AND {user_condition}{ledger_condition}
                ORDER BY date DESC
                LIMIT 1
                """,
                (start_date.strftime("%Y-%m-%d"),) + user_params + ledger_params,
            )
            row = cursor.fetchone()
            return _safe_float(row["period_base"]) if row else 0.0
        finally:
            conn.close()

    def _fetch_transactions_until(
        self,
        end_date: str,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        user_condition, user_params = self._user_filter_sql(user_id)
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_params = (ledger_id,) if ledger_id is not None else ()
        try:
            cursor.execute(
                f"""
                SELECT id, code, name, type, qty, amount, pnl, curr, market, effective_date, time
                FROM transactions
                WHERE effective_date <= ? AND {user_condition}{ledger_condition}
                ORDER BY effective_date ASC, time ASC, id ASC
                """,
                (end_date,) + user_params + ledger_params,
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _position_qty_as_of(
        self,
        *,
        context: Dict[str, Any],
        code: str,
        target_date: str,
    ) -> float:
        cache_key = f"{code}|{target_date}"
        cached = context["position_qty_cache"].get(cache_key)
        if cached is not None:
            return float(cached or 0.0)
        qty = float(
            self.db.get_position_qty_as_of_effective_date(
                code,
                target_date,
                user_id=context["user_id"],
                ledger_id=context["ledger_id"],
            )
            or 0.0
        )
        context["position_qty_cache"][cache_key] = qty
        return qty

    def _resolve_period_bounds(self, scope: str, target: date) -> tuple[date, date]:
        if scope == "month":
            start_date = target.replace(day=1)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
        else:
            start_date = target.replace(month=1, day=1)
            end_date = target.replace(month=12, day=31)

        today = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).date()
        if end_date > today:
            end_date = today
        return start_date, end_date

    def _normalize_market(self, item: Dict[str, Any]) -> str:
        market = str(item.get("market") or item.get("asset_type") or "").strip().lower()
        if market in DEFAULT_MARKETS:
            return market
        resolved = str(market_from_asset(item) or "a").lower()
        return resolved if resolved in DEFAULT_MARKETS else "a"

    def _is_otc_fund(self, item: Dict[str, Any]) -> bool:
        code = str(item.get("code") or "").strip()
        return code.lower().startswith(("f_", "ft_")) and not is_exchange_fund_code(code)

    def _rate_to_cny(self, curr: str, rates: Dict[str, float]) -> float:
        code = str(curr or "CNY").strip().upper()
        if code == "CNY":
            return 1.0
        if self.convert_amount is not None:
            try:
                return float(self.convert_amount(1.0, code, "CNY", rates) or 1.0)
            except Exception:
                pass
        try:
            value = float((rates or {}).get(code, 0.0) or 0.0)
        except Exception:
            value = 0.0
        return value if value > 0 else 1.0

    def _get_rates(self) -> Dict[str, float]:
        if self.rates_getter is None:
            return {}
        try:
            return self.rates_getter() or {}
        except Exception:
            return {}

    def _load_realtime_payload(
        self,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any]:
        if self.realtime_today_service is None:
            return {}
        try:
            return self.realtime_today_service.build_payload(
                user_id=user_id,
                ledger_id=ledger_id,
            ) or {}
        except Exception as exc:
            logger.warning("build realtime asset breakdown payload failed: %s", exc)
            return {}

    def _user_filter_sql(self, user_id: str | None) -> tuple[str, tuple]:
        if user_id:
            return "user_id = ?", (user_id,)
        return "(user_id IS NULL OR user_id = '')", ()

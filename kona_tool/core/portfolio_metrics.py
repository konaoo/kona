"""持仓实时指标口径。

这里专门放“读侧实时指标”的纯计算逻辑。
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Optional, Tuple

from .market_calendar import market_from_asset
from .price import is_exchange_fund_code


def _to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_positive(values: Iterable[float]) -> float:
    for value in values:
        if value > 0:
            return value
    return 0.0


def _compute_display_cost_price(price: float, qty: float, adjustment: float) -> float:
    return price


def _compute_day_pnl_metrics(
    *,
    current_price: float,
    quote_yclose: float,
    qty: float,
    today_buy_qty: float = 0.0,
) -> tuple[float, float, float]:
    """按记账口径计算当日盈亏：只看昨仓，今天新买不参与。"""
    if current_price <= 0 or quote_yclose <= 0 or qty == 0:
        return 0.0, 0.0, 0.0

    if qty < 0:
        # 空头持仓：全量参与日内计算，不考虑 today_buy_qty
        delta = current_price - quote_yclose
        day_pnl = delta * qty  # qty 为负，跌了赚钱
        day_base = quote_yclose * abs(qty)
        day_pnl_rate = (day_pnl / day_base * 100) if day_base > 0 else 0.0
        return day_pnl, day_pnl_rate, qty

    effective_today_buy_qty = min(max(today_buy_qty, 0.0), qty)
    yesterday_qty = max(0.0, qty - effective_today_buy_qty)
    if yesterday_qty <= 0:
        return 0.0, 0.0, 0.0

    delta = current_price - quote_yclose
    day_pnl = delta * yesterday_qty
    day_base = quote_yclose * yesterday_qty

    day_pnl_rate = (day_pnl / day_base * 100) if day_base > 0 else 0.0
    return day_pnl, day_pnl_rate, yesterday_qty


def build_portfolio_items_with_metrics(
    items: List[Dict],
    quotes: Dict[str, Tuple[float, float, float, float, Optional[str]]],
    rates: Dict[str, float],
    market_statuses: Dict[str, Dict[str, float]],
    convert_amount: Callable[[float, str, str, Dict[str, float]], float],
    today_buys: Dict[str, Dict[str, float]] | None = None,
    latest_nav_dates: Dict[str, str | None] | None = None,
) -> List[Dict]:
    """为实时持仓补齐统一指标口径。"""
    enriched: List[Dict] = []
    for item in items:
        code = str(item.get("code") or "").strip()
        qty = _to_float(item.get("qty"))
        raw_cost_price = _to_float(item.get("price"))
        adjustment = _to_float(item.get("adjustment_total", item.get("adjustment")))
        curr = str(item.get("curr") or "CNY").strip().upper()

        market = str(item.get("category_type") or item.get("asset_type") or "").lower()
        if market not in {"a", "hk", "us", "fund"}:
            market = market_from_asset(item)

        is_exchange_fund = is_exchange_fund_code(code)
        status_market = "a" if is_exchange_fund else market
        status = market_statuses.get(status_market, {}) if isinstance(market_statuses, dict) else {}
        market_open = bool(status.get("open"))
        market_trading_day = bool(status.get("trading_day"))
        market_status_reason = str(status.get("reason") or "")

        quote = quotes.get(code) or (0.0, 0.0, 0.0, 0.0, None)
        quote_price = _to_float(quote[0])
        quote_yclose = _to_float(quote[1])
        quote_change = _to_float(quote[2])
        quote_change_pct = _to_float(quote[3])
        quote_date = str(quote[4] or "").strip() or None

        quoted_current_price = _first_positive([quote_price, quote_yclose])
        current_price = _first_positive([quoted_current_price, raw_cost_price])

        nav_update_pending = code.lower().startswith(("f_", "ft_")) and not is_exchange_fund
        latest_nav_date = str((latest_nav_dates or {}).get(code) or "").strip() or quote_date or None
        quote_ready = quote_price > 0
        quote_pending = (not nav_update_pending) and (not quote_ready)

        display_cost_price = _compute_display_cost_price(raw_cost_price, qty, adjustment)
        cost = raw_cost_price * qty
        value = current_price * qty
        total_pnl = value - cost + adjustment
        # 累计收益率只认当前还压在这只持仓里的本金，不再把已兑现收益继续塞回分母。
        total_pnl_base = abs(cost)
        total_pnl_rate = (total_pnl / total_pnl_base * 100) if total_pnl_base > 0 else 0.0

        day_pnl_ready = (not nav_update_pending) and current_price > 0 and quote_yclose > 0
        buy_info = (today_buys or {}).get(code)
        if day_pnl_ready:
            (
                day_pnl_display,
                day_pnl_rate_display,
                yesterday_qty,
            ) = _compute_day_pnl_metrics(
                current_price=current_price,
                quote_yclose=quote_yclose,
                qty=qty,
                today_buy_qty=_to_float((buy_info or {}).get("qty")),
            )
            day_pnl_display_enabled = yesterday_qty > 0
            day_pnl_base_display = quote_yclose * yesterday_qty if yesterday_qty > 0 else 0.0
        else:
            day_pnl_display = 0.0
            day_pnl_rate_display = 0.0
            day_pnl_display_enabled = False
            day_pnl_base_display = 0.0
        day_pnl_aggregate_enabled = day_pnl_display_enabled and market_trading_day
        day_pnl_aggregate = day_pnl_display if day_pnl_aggregate_enabled else 0.0
        day_pnl_rate_aggregate = day_pnl_rate_display if day_pnl_aggregate_enabled else 0.0
        day_pnl_base_aggregate = day_pnl_base_display if day_pnl_aggregate_enabled else 0.0

        rate_to_cny = convert_amount(1.0, curr, "CNY", rates)
        value_cny = value * rate_to_cny
        cost_cny = cost * rate_to_cny
        total_pnl_cny = total_pnl * rate_to_cny
        total_pnl_base_cny = total_pnl_base * rate_to_cny
        day_pnl_cny = day_pnl_display * rate_to_cny
        day_pnl_aggregate_cny = day_pnl_aggregate * rate_to_cny
        day_pnl_base_display_cny = day_pnl_base_display * rate_to_cny
        day_pnl_base_aggregate_cny = day_pnl_base_aggregate * rate_to_cny

        enriched.append(
            {
                **item,
                "market": market,
                "market_open": market_open,
                "market_trading_day": market_trading_day,
                "market_status_reason": market_status_reason,
                "current_price": current_price,
                "yclose": quote_yclose,
                "display_cost_price": display_cost_price,
                "cost": cost,
                "raw_cost_total": cost,
                "value": value,
                "total_pnl": total_pnl,
                "total_pnl_base": total_pnl_base,
                "total_pnl_rate": total_pnl_rate,
                "day_pnl": day_pnl_display,
                "day_pnl_base": day_pnl_base_display,
                "day_pnl_rate": day_pnl_rate_display,
                "day_pnl_display": day_pnl_display,
                "day_pnl_base_display": day_pnl_base_display,
                "day_pnl_rate_display": day_pnl_rate_display,
                "day_pnl_aggregate": day_pnl_aggregate,
                "day_pnl_base_aggregate": day_pnl_base_aggregate,
                "day_pnl_rate_aggregate": day_pnl_rate_aggregate,
                "nav_update_pending": nav_update_pending,
                "latest_nav_date": latest_nav_date,
                "quote_ready": quote_ready,
                "quote_pending": quote_pending,
                "day_pnl_display_enabled": day_pnl_display_enabled,
                "day_pnl_aggregate_enabled": day_pnl_aggregate_enabled,
                "rate_to_cny": rate_to_cny,
                "value_cny": value_cny,
                "cost_cny": cost_cny,
                "total_pnl_cny": total_pnl_cny,
                "total_pnl_base_cny": total_pnl_base_cny,
                "day_pnl_cny": day_pnl_cny,
                "day_pnl_base_cny": day_pnl_base_display_cny,
                "day_pnl_aggregate_cny": day_pnl_aggregate_cny,
                "day_pnl_base_aggregate_cny": day_pnl_base_aggregate_cny,
                "quote_price": quote_price,
                "quote_change": quote_change,
                "quote_change_pct": quote_change_pct,
            }
        )

    total_value_cny = sum(float(row.get("value_cny") or 0.0) for row in enriched)
    if total_value_cny > 0:
        for row in enriched:
            value_cny = row.get("value_cny")
            if value_cny is None:
                row["position_pct"] = None
            else:
                row["position_pct"] = round(float(value_cny) / total_value_cny * 100, 6)
    else:
        for row in enriched:
            row["position_pct"] = None

    return enriched

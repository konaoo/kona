"""持仓实时指标口径。

这里专门放“读侧实时指标”的纯计算逻辑。
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Tuple

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
    if abs(qty) <= 1e-9:
        return price
    return (price * qty - adjustment) / qty


def build_portfolio_items_with_metrics(
    items: List[Dict],
    quotes: Dict[str, Tuple[float, float, float, float]],
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
        adjustment = _to_float(item.get("adjustment"))
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

        quote = quotes.get(code) or (0.0, 0.0, 0.0, 0.0)
        quote_price = _to_float(quote[0])
        quote_yclose = _to_float(quote[1])
        quote_change = _to_float(quote[2])
        quote_change_pct = _to_float(quote[3])

        quoted_current_price = _first_positive([quote_price, quote_yclose])
        current_price = _first_positive([quoted_current_price, raw_cost_price])

        nav_update_pending = code.lower().startswith(("f_", "ft_")) and not is_exchange_fund
        latest_nav_date = str((latest_nav_dates or {}).get(code) or "").strip() or None
        quote_ready = quote_price > 0
        quote_pending = (not nav_update_pending) and (not quote_ready)

        display_cost_price = _compute_display_cost_price(raw_cost_price, qty, adjustment)
        cost = raw_cost_price * qty
        value = current_price * qty
        total_pnl = value - cost + adjustment
        # 分母用 |持仓成本| + max(0, 已实现盈亏)，避免减仓后分母缩水导致收益率虚高
        cost_denominator = abs(cost) + max(0.0, adjustment)
        total_pnl_rate = (total_pnl / cost_denominator * 100) if cost_denominator > 0 else 0.0

        day_pnl_display_enabled = (not nav_update_pending) and current_price > 0 and quote_yclose > 0
        if day_pnl_display_enabled:
            delta = current_price - quote_yclose
            # 修正：今日加仓的份额不应该用昨收价算当日盈亏，用实际买入均价代替
            buy_info = (today_buys or {}).get(code)
            if buy_info and buy_info.get("qty", 0) > 0:
                today_buy_qty = min(float(buy_info["qty"]), qty)  # 不超过当前持仓
                today_avg_price = float(buy_info["amount"]) / today_buy_qty
                pre_trade_qty = max(0.0, qty - today_buy_qty)
                day_pnl_display = (current_price - quote_yclose) * pre_trade_qty + (current_price - today_avg_price) * today_buy_qty
            else:
                day_pnl_display = delta * qty
            day_pnl_rate_display = (delta / quote_yclose) * 100
        else:
            day_pnl_display = 0.0
            day_pnl_rate_display = 0.0
        day_pnl_aggregate_enabled = day_pnl_display_enabled and market_trading_day
        day_pnl_aggregate = day_pnl_display if day_pnl_aggregate_enabled else 0.0
        day_pnl_rate_aggregate = day_pnl_rate_display if day_pnl_aggregate_enabled else 0.0

        rate_to_cny = convert_amount(1.0, curr, "CNY", rates)
        value_cny = value * rate_to_cny
        cost_cny = cost * rate_to_cny
        total_pnl_cny = total_pnl * rate_to_cny
        day_pnl_cny = day_pnl_display * rate_to_cny
        day_pnl_aggregate_cny = day_pnl_aggregate * rate_to_cny

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
                "total_pnl_rate": total_pnl_rate,
                "day_pnl": day_pnl_display,
                "day_pnl_rate": day_pnl_rate_display,
                "day_pnl_display": day_pnl_display,
                "day_pnl_rate_display": day_pnl_rate_display,
                "day_pnl_aggregate": day_pnl_aggregate,
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
                "day_pnl_cny": day_pnl_cny,
                "day_pnl_aggregate_cny": day_pnl_aggregate_cny,
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

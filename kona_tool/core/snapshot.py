"""
资产快照管理模块
负责在后台计算并保存每日资产快照
"""
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict
from zoneinfo import ZoneInfo

from .day_pnl_attribution import (
    resolve_exchange_effective_date,
    resolve_fund_nav_effective_date,
)
from .db import db
from .fund import get_fund_latest_nav_date
from .market_calendar import (
    all_markets_closed,
    get_market_statuses,
    is_markets_closed_on_date,
    is_trading_day,
    market_from_asset,
)
from .price import batch_get_prices, get_forex_rates, is_exchange_fund_code

logger = logging.getLogger(__name__)
DEFAULT_MARKETS = ["a", "hk", "us", "fund"]
MARKET_TIMEZONES = {
    "a": "Asia/Shanghai",
    "hk": "Asia/Hong_Kong",
    "us": "America/New_York",
    "fund": "Asia/Shanghai",
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


def _rate_to_cny(curr: Any, rates: Dict[str, Any]) -> float:
    code = str(curr or "CNY").strip().upper()
    if code == "CNY":
        return 1.0
    try:
        rate = float((rates or {}).get(code, 0.0) or 0.0)
    except Exception:
        rate = 0.0
    return rate if rate > 0 else 1.0


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


def _round_market_breakdown(data: Dict[str, float] | None) -> Dict[str, float]:
    normalized = _empty_market_breakdown()
    for market in DEFAULT_MARKETS:
        normalized[market] = round(float((data or {}).get(market, 0.0) or 0.0), 2)
    return normalized


def calculate_portfolio_stats(user_id: str = None, now_utc: datetime = None) -> Dict[str, Any]:
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
    portfolio = db.get_portfolio(user_id=user_id, include_closed=True)
    cash_assets = db.get_cash_assets(user_id=user_id)
    other_assets = db.get_other_assets(user_id=user_id)
    liabilities = db.get_liabilities(user_id=user_id)
    
    # 2. 获取实时价格和汇率
    codes = [p['code'] for p in portfolio]
    prices = batch_get_prices(codes)
    rates = get_forex_rates()
    
    # 3. 计算投资资产 stats
    invest_mv = 0.0
    total_pnl = 0.0
    day_pnl_breakdowns_by_date: Dict[str, Dict[str, float]] = {}
    now_utc = now_utc or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    market_statuses = get_market_statuses(DEFAULT_MARKETS, now=now_utc)
    market_trading_days = {
        market: _market_trading_day_now(market, now_utc, market_statuses)
        for market in DEFAULT_MARKETS
    }
    snapshot_date = now_utc.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    today_buys_by_effective_date = db.get_buy_transactions_grouped_by_effective_date(user_id=user_id)
    otc_fund_codes = [
        code for code in codes
        if str(code or "").lower().startswith(("f_", "ft_")) and not is_exchange_fund_code(code)
    ]
    latest_nav_dates = {
        code: get_fund_latest_nav_date(code)
        for code in otc_fund_codes
    } if otc_fund_codes else {}
    active_effective_candidates = {
        _market_local_date(market, now_utc).strftime("%Y-%m-%d")
        for market, trading_day in market_trading_days.items()
        if bool(trading_day)
    }

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
        market_trading_day = bool(market_trading_days.get(market))
        # 场外基金（f_/ft_ 开头且非场内 ETF）白天净值尚未更新，
        # 价格源返回的是昨日净值，算出来是昨天的涨跌而非今天的，必须跳过
        nav_update_pending = code.lower().startswith(("f_", "ft_")) and not is_exchange_fund_code(code)
        item_float_pnl = (cur_price - cost) * qty * rate
        item_total_pnl = item_float_pnl + (adj * rate)

        if nav_update_pending:
            effective_date = resolve_fund_nav_effective_date(latest_nav_dates.get(code))
            effective_qty = (
                db.get_position_qty_as_of_effective_date(code, effective_date, user_id=user_id)
                if effective_date else 0.0
            )
            if (
                effective_date
                and cur_price > 0
                and yclose_ref > 0
                and effective_qty > 0
                and abs(cur_price - yclose_ref) / yclose_ref >= 1e-9
            ):
                item_day_pnl = (cur_price - yclose_ref) * effective_qty * rate
                _add_market_breakdown(day_pnl_breakdowns_by_date, effective_date, market, item_day_pnl)
        else:
            effective_date = resolve_exchange_effective_date(
                market=market,
                now_utc=now_utc,
                current_price=cur_price,
                yclose=yclose_ref,
                market_trading_day=market_trading_day,
            )
            if effective_date:
                buy_info = (today_buys_by_effective_date.get(effective_date) or {}).get(code)
                if buy_info and buy_info.get("qty", 0) > 0:
                    effective_buy_qty = min(float(buy_info["qty"]), qty)
                    effective_avg_price = float(buy_info["amount"]) / effective_buy_qty
                    pre_trade_qty = max(0.0, qty - effective_buy_qty)
                    item_day_pnl = (
                        (cur_price - yclose_ref) * pre_trade_qty
                        + (cur_price - effective_avg_price) * effective_buy_qty
                    ) * rate
                else:
                    item_day_pnl = (cur_price - yclose_ref) * qty * rate
                _add_market_breakdown(day_pnl_breakdowns_by_date, effective_date, market, item_day_pnl)

        # 累加
        invest_mv += item_mv
        total_pnl += item_total_pnl
        
    # 4. 计算非投资资产 stats
    total_cash = sum(_asset_amount_to_cny(a, rates) for a in cash_assets)
    total_other = sum(_asset_amount_to_cny(a, rates) for a in other_assets)
    total_liability = sum(_asset_amount_to_cny(a, rates, use_abs=True) for a in liabilities)
    
    # 5. 获取今日已实现盈亏（卖出）
    relevant_effective_dates = set(day_pnl_breakdowns_by_date.keys())
    relevant_effective_dates.add(snapshot_date)
    realized_pnl_grouped = db.get_realized_pnl_grouped_by_effective_date(user_id=user_id)
    for effective_date, market_map in realized_pnl_grouped.items():
        if effective_date not in relevant_effective_dates:
            continue
        for market, realized_pnl in (market_map or {}).items():
            _add_market_breakdown(
                day_pnl_breakdowns_by_date,
                effective_date,
                market,
                float(realized_pnl or 0.0),
            )
    # 注意：total_pnl 在上面计算的是 (当前持仓市值 - 当前持仓成本 + adjustment)。
    # 这里的 adjustment 已经是“旧 portfolio.adjustment + 流水表汇总”的总调整值。
    # 所以 total_pnl 已经包含了历史所有 realized_pnl / 分红 / 手工补差。
    # 因此这里只需要将 realized_pnl 加到 day_pnl 中即可（因为 loop calculated floating day pnl only）。
    
    # 6. 汇总
    total_asset = total_cash + invest_mv + total_other - total_liability
    active_effective_date = max(active_effective_candidates) if active_effective_candidates else snapshot_date
    realtime_day_pnl_by_market = _round_market_breakdown(day_pnl_breakdowns_by_date.get(active_effective_date))
    realtime_day_pnl = round(sum(realtime_day_pnl_by_market.values()), 2)
    snapshot_day_pnl_by_market = _round_market_breakdown(day_pnl_breakdowns_by_date.get(snapshot_date))
    snapshot_day_pnl = round(sum(snapshot_day_pnl_by_market.values()), 2)
    rounded_breakdowns_by_date = {
        date_str: _round_market_breakdown(market_map)
        for date_str, market_map in sorted(day_pnl_breakdowns_by_date.items())
    }
    
    return {
        'total_invest': round(invest_mv, 2),
        'total_cash': round(total_cash, 2),
        'total_other': round(total_other, 2),
        'total_liability': round(total_liability, 2),
        'total_asset': round(total_asset, 2),
        'total_pnl': round(total_pnl, 2),
        'day_pnl': realtime_day_pnl,
        'day_pnl_effective_date': active_effective_date,
        'day_pnl_by_market': realtime_day_pnl_by_market,
        'snapshot_day_pnl': snapshot_day_pnl,
        'snapshot_day_pnl_by_market': snapshot_day_pnl_by_market,
        'day_pnl_breakdowns_by_date': rounded_breakdowns_by_date,
        'snapshot_date': snapshot_date,
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
            stats = calculate_portfolio_stats(uid)
            snapshot_date = str(stats.get("snapshot_date") or datetime.now().strftime("%Y-%m-%d"))
            snapshot_payload = {
                **stats,
                "day_pnl": float(stats.get("snapshot_day_pnl", 0.0) or 0.0),
            }
            success = db.save_daily_snapshot(snapshot_payload, uid, snapshot_date=snapshot_date)
            success_any = success_any or success
            if success:
                breakdown_dates = set((stats.get("day_pnl_breakdowns_by_date") or {}).keys())
                breakdown_dates.add(snapshot_date)
                for effective_date in sorted(breakdown_dates):
                    market_map = (
                        (stats.get("day_pnl_breakdowns_by_date") or {}).get(effective_date)
                        if effective_date != snapshot_date
                        else stats.get("snapshot_day_pnl_by_market")
                    ) or _empty_market_breakdown()
                    breakdown_ok = db.save_daily_snapshot_market_breakdown(
                        date_str=effective_date,
                        day_pnl_by_market=market_map,
                        total_day_pnl=sum(float(v or 0.0) for v in market_map.values()),
                        user_id=uid,
                        source="exact",
                        confidence=1.0,
                    )
                    if not breakdown_ok:
                        logger.warning("Market breakdown save failed: user=%s date=%s", uid, effective_date)
                logger.info(f"Snapshot saved successfully: user={uid}, Total={stats['total_asset']}, DayPnl={stats['day_pnl']}")
            else:
                logger.error(f"Failed to save snapshot to database: user={uid}")

        return success_any
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        return False

"""
资产快照管理模块
负责在后台计算并保存每日资产快照
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from zoneinfo import ZoneInfo

from .db import db
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
    day_pnl = 0.0
    total_pnl = 0.0
    day_pnl_by_market = {market: 0.0 for market in DEFAULT_MARKETS}
    now_utc = now_utc or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    market_statuses = get_market_statuses(DEFAULT_MARKETS, now=now_utc)
    market_trading_days = {
        market: _market_trading_day_now(market, now_utc, market_statuses)
        for market in DEFAULT_MARKETS
    }
    # 今日加仓记录，用于修正 day_pnl（避免把新买入份额的昨收价差算进今日盈亏）
    snapshot_date_for_buys = now_utc.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    today_buys = db.get_today_buy_transactions(snapshot_date_for_buys, user_id=user_id)
    
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
        if market not in day_pnl_by_market:
            market = "a"
        market_trading_day = bool(market_trading_days.get(market))
        # 场外基金（f_/ft_ 开头且非场内 ETF）白天净值尚未更新，
        # 价格源返回的是昨日净值，算出来是昨天的涨跌而非今天的，必须跳过
        nav_update_pending = code.lower().startswith(("f_", "ft_")) and not is_exchange_fund_code(code)
        # 开盘前价格源返回的 cur_price ≈ yclose_ref（都是上一个收盘价），
        # 此时不应计入当日盈亏，否则会把昨天的涨幅错误记到今天
        if nav_update_pending:
            item_day_pnl = 0.0
        elif not market_trading_day:
            item_day_pnl = 0.0
        elif yclose_ref > 0 and abs(cur_price - yclose_ref) / yclose_ref < 1e-9:
            item_day_pnl = 0.0
        else:
            # 修正：今日加仓的份额不应用昨收价算今日盈亏，用实际买入均价代替
            buy_info = today_buys.get(code)
            if buy_info and buy_info.get("qty", 0) > 0:
                today_buy_qty = min(float(buy_info["qty"]), qty)
                today_avg_price = float(buy_info["amount"]) / today_buy_qty
                pre_trade_qty = max(0.0, qty - today_buy_qty)
                item_day_pnl = (
                    (cur_price - yclose_ref) * pre_trade_qty
                    + (cur_price - today_avg_price) * today_buy_qty
                ) * rate
            else:
                item_day_pnl = (cur_price - yclose_ref) * qty * rate
        item_float_pnl = (cur_price - cost) * qty * rate
        item_total_pnl = item_float_pnl + (adj * rate)
        
        # 累加
        invest_mv += item_mv
        day_pnl += item_day_pnl
        total_pnl += item_total_pnl
        day_pnl_by_market[market] += item_day_pnl
        
    # 4. 计算非投资资产 stats
    total_cash = sum(_asset_amount_to_cny(a, rates) for a in cash_assets)
    total_other = sum(_asset_amount_to_cny(a, rates) for a in other_assets)
    total_liability = sum(_asset_amount_to_cny(a, rates, use_abs=True) for a in liabilities)
    
    # 5. 获取今日已实现盈亏（卖出）
    # 统一用北京时间作为快照日期，和 cron、服务器时区、用户认知一致
    snapshot_date = now_utc.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    realized_pnl_by_market = db.get_realized_pnl_by_date(snapshot_date, user_id=user_id)
    realized_pnl = sum(float(v or 0.0) for v in realized_pnl_by_market.values())
    try:
        closed_on_snapshot_date = is_markets_closed_on_date(DEFAULT_MARKETS, snapshot_date)
    except Exception:
        closed_on_snapshot_date = all_markets_closed(DEFAULT_MARKETS, now=now_utc)
    if not closed_on_snapshot_date:
        day_pnl += realized_pnl
        for market in DEFAULT_MARKETS:
            day_pnl_by_market[market] += float(realized_pnl_by_market.get(market, 0.0) or 0.0)
    # 注意：total_pnl 在上面计算的是 (当前持仓市值 - 当前持仓成本 + adjustment)。
    # adjustment 字段通常用于存储 "已实现盈亏 + 分红" 等历史调整。
    # 当我们减仓时，modify_asset/sell_asset 会更新 adjustment 吗？
    # 检查 db.py: sell_asset 更新 adjustment = adjustment + pnl。
    # 所以 total_pnl 已经包含了历史所有 realized_pnl (包括今天的)。
    # 因此这里只需要将 realized_pnl 加到 day_pnl 中即可（因为 loop calculated floating day pnl only）。
    
    # 6. 汇总
    total_asset = total_cash + invest_mv + total_other - total_liability
    
    return {
        'total_invest': round(invest_mv, 2),
        'total_cash': round(total_cash, 2),
        'total_other': round(total_other, 2),
        'total_liability': round(total_liability, 2),
        'total_asset': round(total_asset, 2),
        'total_pnl': round(total_pnl, 2),
        'day_pnl': round(day_pnl, 2),
        'day_pnl_by_market': {
            market: round(float(day_pnl_by_market.get(market, 0.0) or 0.0), 2)
            for market in DEFAULT_MARKETS
        },
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
            success = db.save_daily_snapshot(stats, uid, snapshot_date=snapshot_date)
            success_any = success_any or success
            if success:
                snapshot_date = str(stats.get("snapshot_date") or datetime.now().strftime("%Y-%m-%d"))
                breakdown_ok = db.save_daily_snapshot_market_breakdown(
                    date_str=snapshot_date,
                    day_pnl_by_market=stats.get("day_pnl_by_market") or {},
                    total_day_pnl=float(stats.get("day_pnl", 0.0) or 0.0),
                    user_id=uid,
                    source="exact",
                    confidence=1.0,
                )
                if not breakdown_ok:
                    logger.warning("Market breakdown save failed: user=%s date=%s", uid, snapshot_date)
                logger.info(f"Snapshot saved successfully: user={uid}, Total={stats['total_asset']}, DayPnl={stats['day_pnl']}")
            else:
                logger.error(f"Failed to save snapshot to database: user={uid}")

        return success_any
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        return False

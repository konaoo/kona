"""
资产快照管理模块
负责在后台计算并保存每日资产快照
"""
import logging
import time
from datetime import datetime
from typing import Dict

from .db import db
from .price import batch_get_prices, get_forex_rates

logger = logging.getLogger(__name__)


def is_market_closed() -> bool:
    """
    判断当前是否休市
    
    休市条件：
    1. 周末（周六、周日）
    2. 非交易时间（9:30前或15:00后）
    
    Returns:
        True 表示休市，False 表示开市
    """
    now = datetime.now()
    
    # 周末休市
    if now.weekday() >= 5:  # 5=周六, 6=周日
        return True
    
    # 交易时间判断 (9:30 - 15:00)
    current_time = now.hour * 100 + now.minute
    if current_time < 930 or current_time >= 1500:
        return True
    
    return False

def calculate_portfolio_stats(user_id: str = None) -> Dict[str, float]:
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
    portfolio = db.get_portfolio(user_id=user_id)
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
    
    for asset in portfolio:
        code = asset['code']
        qty = float(asset['qty'])
        cost = float(asset['price'])
        curr = asset['curr']
        adj = float(asset['adjustment'] or 0)
        
        # 汇率
        rate = rates.get(curr, 1.0)
        
        # 价格数据
        price_data = prices.get(code, (0, 0, 0, 0))
        cur_price = price_data[0]
        yclose = price_data[1]
        
        # 如果获取失败或为0，使用成本价或昨收作为后备
        if cur_price <= 0:
            cur_price = yclose if yclose > 0 else cost
        
        yclose_ref = yclose if yclose > 0 else cost
        
        # 计算单项指标 (转换为CNY)
        item_mv = cur_price * qty * rate
        item_day_pnl = (cur_price - yclose_ref) * qty * rate
        item_float_pnl = (cur_price - cost) * qty * rate
        item_total_pnl = item_float_pnl + (adj * rate)
        
        # 累加
        invest_mv += item_mv
        day_pnl += item_day_pnl
        total_pnl += item_total_pnl
        
    # 4. 计算非投资资产 stats
    total_cash = sum(a['amount'] for a in cash_assets)
    total_other = sum(a['amount'] for a in other_assets)
    total_liability = sum(abs(a['amount']) for a in liabilities)
    
    # 5. 获取今日已实现盈亏（卖出）
    realized_pnl = db.get_today_realized_pnl()
    day_pnl += realized_pnl
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
        'day_pnl': round(day_pnl, 2)
    }

def take_snapshot(user_id: str = None) -> bool:
    """
    执行快照保存
    
    注意：休市时 day_pnl 固定为 0
    """
    try:
        logger.info("Starting background snapshot task...")
        stats = calculate_portfolio_stats(user_id)
        
        # 休市时 day_pnl 应为 0
        if is_market_closed():
            logger.info("Market is closed, setting day_pnl to 0")
            stats['day_pnl'] = 0.0
        
        # 保存到数据库
        success = db.save_daily_snapshot(stats, user_id)
        
        if success:
            logger.info(f"Snapshot saved successfully: Total={stats['total_asset']}, DayPnl={stats['day_pnl']}")
        else:
            logger.error("Failed to save snapshot to database")
            
        return success
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        return False

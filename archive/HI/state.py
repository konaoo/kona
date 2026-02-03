"""
状态管理模块 - 统一管理应用状态
"""
import flet as ft
from typing import List, Dict, Any, Optional, Callable
from config import Theme
from datetime import datetime

class AppState:
    """应用全局状态管理类"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        
        # 导航状态
        self.current_page_stack: List[str] = []
        self.current_category: str = "all"
        
        # 数据缓存
        self.portfolio_data: List[Dict[str, Any]] = []
        self.prices: Dict[str, Dict[str, Any]] = {}
        self.portfolio_loaded: bool = False
        
        # UI 状态
        self.amount_hidden: bool = False
        
        # 首页数据
        self.total_asset: float = 0
        self.total_cash: float = 0
        self.total_invest: float = 0
        self.total_other: float = 0
        
        # 投资页面汇总数据
        self.invest_total_mv: float = 0
        self.invest_day_pnl: float = 0
        self.invest_day_pnl_pct: float = 0
        self.invest_holding_pnl: float = 0
        self.invest_holding_pnl_pct: float = 0
        self.invest_total_pnl: float = 0
        self.invest_total_pnl_pct: float = 0

        # 汇率数据
        self.exchange_rates: Dict[str, float] = {"USD": 7.25, "HKD": 0.93, "CNY": 1.0}
        
        # 回调函数
        self._on_state_change: Optional[Callable] = None
    
    def set_on_state_change(self, callback: Callable):
        """设置状态变化回调"""
        self._on_state_change = callback
    
    def notify(self):
        """通知状态变化"""
        if self._on_state_change:
            self._on_state_change()
        self.page.update()
    
    # ============================================================
    # 金额显示控制
    # ============================================================
    
    def toggle_amount_hidden(self):
        """切换金额显示/隐藏"""
        self.amount_hidden = not self.amount_hidden
        self.notify()
    
    def mask_amount(self, value: str) -> str:
        """根据状态返回金额或掩码"""
        return "****" if self.amount_hidden else value
    
    def format_amount(self, amount: float, prefix: str = "¥") -> str:
        """格式化金额并应用掩码"""
        formatted = f"{prefix}{amount:,.0f}"
        return self.mask_amount(formatted)
    
    # ============================================================
    # 导航状态管理
    # ============================================================
    
    def push_page(self, page_name: str):
        """进入子页面"""
        self.current_page_stack.append(page_name)
    
    def pop_page(self) -> Optional[str]:
        """返回上一页"""
        if self.current_page_stack:
            return self.current_page_stack.pop()
        return None
    
    def set_category(self, category: str):
        """设置当前分类"""
        self.current_category = category
        self.notify()
    
    # ============================================================
    # 数据更新
    # ============================================================
    
    def update_home_data(self, total: float, cash: float, invest: float, other: float):
        """更新首页数据"""
        self.total_asset = total
        self.total_cash = cash
        self.total_invest = invest
        self.total_other = other
    
    def update_portfolio(self, data: List[Dict], prices: Dict):
        """更新投资组合数据"""
        self.portfolio_data = data
        self.prices = prices
        self.portfolio_loaded = True
        self._calculate_invest_summary()

    def update_exchange_rates(self, rates: Dict[str, float]):
        """更新汇率数据"""
        self.exchange_rates = rates
        # 汇率更新后重新计算投资汇总（如果已经加载了投资组合）
        if self.portfolio_loaded:
            self._calculate_invest_summary()
    
    def _calculate_invest_summary(self):
        """计算投资汇总数据"""
        total_mv_cny = 0  # 总市值（人民币）
        total_cost = 0
        total_day = 0
        total_adj = 0

        # 判断是否休市（周末）
        # 0=Mon, 6=Sun
        is_weekend = datetime.now().weekday() >= 5

        for item in self.portfolio_data:
            code = item['code']
            qty = float(item['qty'])
            cost = float(item['price'])
            adj = float(item.get('adjustment', 0))

            pi = self.prices.get(code, {})
            # 当前价：优先使用 price，其次 yclose，最后用成本价
            cp = pi.get('price', 0) or pi.get('yclose', 0) or cost
            # 昨收价：必须存在且不为 0，否则用当前价（今日盈亏为 0）
            yc = pi.get('yclose', 0) or cp

            # 🔧 获取汇率
            market_type = self.get_market_type(code)
            if market_type == 'hk':
                exchange_rate = self.exchange_rates.get('HKD', 0.93)
            elif market_type == 'us':
                exchange_rate = self.exchange_rates.get('USD', 7.25)
            else:
                exchange_rate = 1.0

            # 🔧 市值和成本换算成人民币
            mv_original = cp * qty  # 原币种市值
            mv_cny = mv_original * exchange_rate  # 换算成人民币
            cost_cny = cost * qty * exchange_rate  # 成本换算成人民币

            total_mv_cny += mv_cny
            total_cost += cost_cny

            # 🔧 修复今日盈亏计算逻辑
            # 如果是周末，今日盈亏显示为 0
            if is_weekend:
                total_day += 0
            # 如果昨收价无效（为 0 或不存在），今日盈亏为 0
            elif pi.get('yclose', 0) == 0 or pi.get('yclose') is None:
                total_day += 0
            # 正常计算：(当前价 - 昨收价) × 数量 × 汇率
            else:
                total_day += (cp - yc) * qty * exchange_rate

            total_adj += adj * exchange_rate  # 调整值也换算成人民币

        self.invest_total_mv = total_mv_cny
        self.invest_day_pnl = total_day
        self.invest_day_pnl_pct = (total_day / (total_mv_cny - total_day) * 100) if (total_mv_cny - total_day) > 0 else 0

        h_pnl = total_mv_cny - total_cost + total_adj
        self.invest_holding_pnl = h_pnl
        self.invest_holding_pnl_pct = (h_pnl / total_cost * 100) if total_cost > 0 else 0

        self.invest_total_pnl = h_pnl
        self.invest_total_pnl_pct = self.invest_holding_pnl_pct
    
    def clear_portfolio_cache(self):
        """清除投资组合缓存"""
        self.portfolio_loaded = False
        self.portfolio_data = []
        self.prices = {}
    
    # ============================================================
    # 工具方法
    # ============================================================
    
    @staticmethod
    def get_market_type(code: str) -> str:
        """判断市场类型"""
        code_upper = code.upper()
        if 'HK' in code_upper:
            return 'hk'
        elif code_upper.startswith('US') or (len(code) <= 5 and code.isalpha()):
            return 'us'
        elif any(code_upper.startswith(p) for p in ['OF', '15', '16', '51', '52']):
            return 'fund'
        else:
            return 'a'
    
    @staticmethod
    def format_code(code: str) -> str:
        """格式化显示代码"""
        if '.' in code:
            parts = code.split('.')
            return parts[1] if len(parts) > 1 else parts[0]
        return code[:6] if len(code) > 6 else code
    
    @staticmethod
    def get_pnl_color(value: float) -> str:
        """根据盈亏值返回颜色"""
        return Theme.DANGER if value >= 0 else Theme.SUCCESS
    
    @staticmethod
    def format_pnl(value: float, with_sign: bool = True) -> str:
        """格式化盈亏金额"""
        sign = "+" if value >= 0 and with_sign else ""
        return f"{sign}{value:,.2f}"
    
    @staticmethod
    def format_pct(value: float, with_sign: bool = True) -> str:
        """格式化百分比"""
        sign = "+" if value >= 0 and with_sign else ""
        return f"{sign}{value:.2f}%"

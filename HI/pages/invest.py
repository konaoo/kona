"""
投资页面 - 持仓列表
优化版：去掉 loading，显示 -- 占位符，后台加载数据
"""
import flet as ft
import re
from typing import Callable, Dict, Any

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from components import (
    loading_indicator, empty_state, gradient_card,
    horizontal_padding, spacer, tab_button
)


def build_invest_page(
    state: AppState,
    portfolio_container: ft.Column,
    category_row: ft.Row,
    on_category_change: Callable[[str], None]
) -> ft.Container:
    """
    构建投资页面

    特性：
    - 立即显示 UI，数据未加载时显示 --
    - 后台加载数据，完成后自动更新

    Args:
        state: 应用状态
        portfolio_container: 持仓列表容器
        category_row: 分类标签行
        on_category_change: 分类切换回调
    """
    # ============================================================
    # 辅助函数：显示金额或占位符
    # ============================================================

    def display_amount(value: float, prefix: str = "¥") -> str:
        """显示金额，如果为 0 则显示 --"""
        if value == 0:
            return "--"
        formatted = f"{prefix}{value:,.0f}"
        return state.mask_amount(formatted)

    def display_pnl(value: float) -> str:
        """显示盈亏，如果为 0 则显示 --"""
        if value == 0:
            return "--"
        return state.mask_amount(state.format_pnl(value))

    # ============================================================
    # UI 组件
    # ============================================================

    eye_icon = ft.Icons.VISIBILITY_OFF if state.amount_hidden else ft.Icons.VISIBILITY

    # 根据隐藏状态显示金额
    display_total = display_amount(state.invest_total_mv)
    display_day_pnl = display_pnl(state.invest_day_pnl)
    display_holding_pnl = display_pnl(state.invest_holding_pnl)
    display_total_pnl = display_pnl(state.invest_total_pnl)

    day_color = state.get_pnl_color(state.invest_day_pnl) if state.invest_day_pnl != 0 else Theme.TEXT_SECONDARY
    holding_color = state.get_pnl_color(state.invest_holding_pnl) if state.invest_holding_pnl != 0 else Theme.TEXT_SECONDARY
    total_color = state.get_pnl_color(state.invest_total_pnl) if state.invest_total_pnl != 0 else Theme.TEXT_SECONDARY

    # 汇总卡片内容
    card_content = ft.Column([
        # 总市值 + 眼睛图标 + 今日盈亏
        ft.Row([
            ft.Column([
                ft.Row([
                    ft.Text("总市值", size=FontSize.BASE, color=Theme.TEXT_TERTIARY),
                    ft.IconButton(
                        icon=eye_icon,
                        icon_size=16,
                        icon_color=Theme.TEXT_SECONDARY,
                        on_click=lambda _: state.toggle_amount_hidden(),
                    ),
                ], spacing=0),
                ft.Text(display_total, size=FontSize.HERO, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY),
            ], spacing=2, expand=True),
            ft.Column([
                ft.Text("今日盈亏", size=11, color=Theme.TEXT_TERTIARY),
                ft.Text(display_day_pnl, size=FontSize.LG, color=day_color),
                ft.Text(
                    state.format_pct(state.invest_day_pnl_pct) if state.invest_day_pnl_pct != 0 else "--",
                    size=FontSize.BASE,
                    color=Theme.TEXT_SECONDARY
                ),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
        ]),

        spacer(Spacing.MD),
        ft.Divider(height=1, color=Theme.BORDER),
        spacer(Spacing.MD),

        # 持仓盈亏 - 持仓盈亏率 - 累计盈亏 - 累计盈亏率
        ft.Row([
            ft.Column([
                ft.Text("持仓盈亏", size=FontSize.XS, color=Theme.TEXT_TERTIARY, text_align=ft.TextAlign.CENTER),
                ft.Text(display_holding_pnl, size=FontSize.LG, color=holding_color, text_align=ft.TextAlign.CENTER),
            ], spacing=2, width=75, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([
                ft.Text("持仓盈亏率", size=FontSize.XS, color=Theme.TEXT_TERTIARY, text_align=ft.TextAlign.CENTER),
                ft.Text(
                    state.format_pct(state.invest_holding_pnl_pct) if state.invest_holding_pnl_pct != 0 else "--",
                    size=FontSize.BASE,
                    color=holding_color,
                    text_align=ft.TextAlign.CENTER
                ),
            ], spacing=2, width=75, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([
                ft.Text("累计盈亏", size=FontSize.XS, color=Theme.TEXT_TERTIARY, text_align=ft.TextAlign.CENTER),
                ft.Text(display_total_pnl, size=FontSize.LG, color=total_color, text_align=ft.TextAlign.CENTER),
            ], spacing=2, width=75, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([
                ft.Text("累计盈亏率", size=FontSize.XS, color=Theme.TEXT_TERTIARY, text_align=ft.TextAlign.CENTER),
                ft.Text(
                    state.format_pct(state.invest_total_pnl_pct) if state.invest_total_pnl_pct != 0 else "--",
                    size=FontSize.BASE,
                    color=total_color,
                    text_align=ft.TextAlign.CENTER
                ),
            ], spacing=2, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
    ])
    
    return ft.Container(
        content=ft.Column([
            spacer(Spacing.LG),  # 🔧 减少顶部间距，卡片移到最顶部
            horizontal_padding(gradient_card(card_content, padding=Spacing.XL)),
            spacer(Spacing.MD),
            portfolio_container,
        ]),
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )


def build_category_tabs(
    state: AppState,
    category_row: ft.Row,
    on_click: Callable[[str], None]
):
    """构建分类标签"""
    category_row.controls.clear()
    categories = [("all", "全部"), ("a", "A股"), ("us", "美股"), ("hk", "港股"), ("fund", "基金")]
    
    for cat_id, cat_name in categories:
        is_selected = state.current_category == cat_id
        category_row.controls.append(
            tab_button(cat_name, is_selected, lambda _, c=cat_id: on_click(c))
        )


def build_portfolio_header() -> ft.Container:
    """构建持仓列表表头（左对齐）"""
    return ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Text("资产名称", size=FontSize.SM, color=Theme.TEXT_TERTIARY), width=80),
            ft.Container(content=ft.Text("市值/数量", size=FontSize.SM, color=Theme.TEXT_TERTIARY), width=70),
            ft.Container(content=ft.Text("现价/成本", size=FontSize.SM, color=Theme.TEXT_TERTIARY), width=70),
            ft.Container(content=ft.Text("累计盈亏", size=FontSize.SM, color=Theme.TEXT_TERTIARY), expand=True),
        ], spacing=8),
        padding=ft.Padding(14, 8, 14, 4),
        margin=ft.Margin(Spacing.XL, 0, Spacing.XL, 0),
    )


def build_portfolio_card(item: Dict[str, Any], price_info: Dict[str, Any], state: AppState) -> ft.Container:
    """构建持仓卡片"""
    code = item['code']
    name = item['name']
    qty = float(item['qty'])
    cost = float(item['price'])
    adjustment = float(item.get('adjustment', 0))

    curr_price = price_info.get('price', 0) or price_info.get('yclose', cost) or cost

    mv = curr_price * qty
    cost_total = cost * qty
    holding_pnl = mv - cost_total + adjustment
    holding_pnl_pct = (holding_pnl / cost_total * 100) if cost_total > 0 else 0

    holding_color = state.get_pnl_color(holding_pnl)

    # 🔧 根据市场类型确定币种符号
    market_type = state.get_market_type(code)
    if market_type == 'hk':
        currency_symbol = 'HK$'
    elif market_type == 'us':
        currency_symbol = '$'
    else:
        currency_symbol = '¥'

    # 提取代码数字部分
    display_code = _extract_code_number(code)
    display_name = name if len(name) <= 5 else name[:5] + "…"

    # 🔧 根据隐藏状态显示数据（使用对应币种符号）
    display_mv = state.mask_amount(f"{currency_symbol}{mv:,.2f}")
    display_qty = state.mask_amount(f"{qty:,.0f}")  # 去掉"股"字
    display_curr_price = f"{currency_symbol}{curr_price:.2f}"
    display_cost = f"{currency_symbol}{cost:.2f}"
    display_pnl = state.mask_amount(f"{'+' if holding_pnl >= 0 else ''}{holding_pnl:,.2f}")
    display_pnl_pct = f"{'+' if holding_pnl_pct >= 0 else ''}{holding_pnl_pct:.2f}%"

    return ft.Container(
        content=ft.Row([
            # 资产名称（左对齐）
            ft.Container(
                content=ft.Column([
                    ft.Text(display_name, size=FontSize.BASE, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(display_code, size=FontSize.SM, color=Theme.TEXT_TERTIARY),
                ], spacing=2),
                width=80,
            ),
            # 市值/数量（左对齐）
            ft.Container(
                content=ft.Column([
                    ft.Text(display_mv, size=FontSize.MD, weight=ft.FontWeight.W_500, color=Theme.TEXT_PRIMARY),
                    ft.Text(display_qty, size=FontSize.XS, color=Theme.TEXT_TERTIARY),
                ], spacing=2),
                width=70,
            ),
            # 现价/成本（左对齐）
            ft.Container(
                content=ft.Column([
                    ft.Text(display_curr_price, size=FontSize.MD, color=Theme.TEXT_PRIMARY),
                    ft.Text(display_cost, size=FontSize.XS, color=Theme.TEXT_TERTIARY),
                ], spacing=2),
                width=70,
            ),
            # 累计盈亏（左对齐）
            ft.Container(
                content=ft.Column([
                    ft.Text(display_pnl, size=FontSize.MD, weight=ft.FontWeight.W_600, color=holding_color),
                    ft.Text(display_pnl_pct, size=FontSize.XS, color=holding_color),
                ], spacing=2),
                expand=True,
            ),
        ], spacing=8),
        padding=ft.Padding(14, 10, 14, 10),
        bgcolor=Theme.BG_CARD,
        border_radius=BorderRadius.MD,
        margin=ft.Margin(Spacing.XL, 0, Spacing.XL, 0),
    )


def _extract_code_number(code: str) -> str:
    """提取代码中的数字或字母部分"""
    match = re.search(r'(\d{5,6}|\b[A-Z]{2,5}\b)', code.upper())
    if match:
        return match.group(1)
    if '.' in code:
        return code.split('.')[0]
    return code[:6]

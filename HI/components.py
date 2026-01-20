"""
组件模块 - 可复用的 UI 组件
"""
import flet as ft
from typing import Optional, Callable
from config import Theme, Spacing, FontSize, BorderRadius


# ============================================================
# 基础组件
# ============================================================

def loading_indicator(size: int = 30) -> ft.Container:
    """加载指示器"""
    return ft.Container(
        content=ft.ProgressRing(
            width=size,
            height=size,
            stroke_width=3,
            color=Theme.ACCENT
        ),
        padding=40,
        alignment=ft.Alignment(0, 0)
    )


def empty_state(icon: str, text: str) -> ft.Container:
    """空状态占位"""
    return ft.Container(
        content=ft.Column([
            ft.Icon(icon, size=48, color=Theme.TEXT_TERTIARY),
            ft.Text(text, size=FontSize.XL, color=Theme.TEXT_SECONDARY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=Spacing.MD),
        padding=60,
        alignment=ft.Alignment(0, 0)
    )


def error_state(message: str = "加载失败") -> ft.Container:
    """错误状态"""
    return ft.Container(
        content=ft.Text(message, size=FontSize.LG, color=Theme.DANGER),
        padding=40,
        alignment=ft.Alignment(0, 0)
    )


# ============================================================
# 卡片组件
# ============================================================

def card(
    content: ft.Control,
    padding: int = Spacing.LG,
    border_radius: int = BorderRadius.LG,
    bgcolor: str = Theme.BG_CARD,
    margin: Optional[ft.Margin] = None,
    on_click: Optional[Callable] = None,
    gradient: bool = False
) -> ft.Container:
    """通用卡片容器"""
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=border_radius,
        bgcolor=None if gradient else bgcolor,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=Theme.CARD_GRADIENT
        ) if gradient else None,
        margin=margin,
        on_click=on_click
    )


def gradient_card(content: ft.Control, padding: int = Spacing.XL) -> ft.Container:
    """渐变背景卡片"""
    return card(content, padding=padding, gradient=True, border_radius=BorderRadius.XXL)


# ============================================================
# 列表项组件
# ============================================================

def asset_row(
    icon: str,
    title: str,
    on_click: Optional[Callable] = None
) -> ft.Container:
    """资产入口行"""
    return ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Icon(icon, size=20, color=Theme.ACCENT_LIGHT),
                bgcolor=Theme.BG_ELEVATED,
                border_radius=BorderRadius.MD,
                padding=Spacing.SM + 2
            ),
            ft.Container(width=Spacing.MD),
            ft.Text(title, size=15, color=Theme.TEXT_SECONDARY, expand=True),
            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=20, color=Theme.TEXT_TERTIARY),
        ]),
        padding=ft.Padding(Spacing.LG, Spacing.LG - 2, Spacing.LG, Spacing.LG - 2),
        border_radius=BorderRadius.LG,
        bgcolor=Theme.BG_CARD,
        on_click=on_click,
    )


def setting_row(
    icon: str,
    title: str,
    on_click: Optional[Callable] = None
) -> ft.Container:
    """设置项行"""
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=20, color=Theme.ACCENT_LIGHT),
            ft.Container(width=Spacing.MD),
            ft.Text(title, size=15, color=Theme.TEXT_PRIMARY, expand=True),
            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=20, color=Theme.TEXT_TERTIARY)
        ]),
        padding=Spacing.LG,
        bgcolor=Theme.BG_CARD,
        border_radius=BorderRadius.LG,
    )


def detail_item(
    name: str,
    amount: float,
    is_liability: bool = False
) -> ft.Container:
    """详情列表项"""
    color = Theme.DANGER if is_liability else Theme.TEXT_PRIMARY
    prefix = "-" if is_liability else ""
    
    return ft.Container(
        content=ft.Row([
            ft.Text(name, size=15, color=Theme.TEXT_PRIMARY, expand=True),
            ft.Text(f"{prefix}¥{amount:,.0f}", size=15, weight=ft.FontWeight.W_600, color=color),
        ]),
        padding=Spacing.LG,
        bgcolor=Theme.BG_CARD,
        border_radius=BorderRadius.LG,
    )


# ============================================================
# 页面头部组件
# ============================================================

def page_header(
    title: str,
    on_back: Optional[Callable] = None
) -> ft.Container:
    """页面头部（带返回按钮）"""
    controls = []
    
    if on_back:
        controls.append(
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS,
                icon_color=Theme.TEXT_PRIMARY,
                icon_size=20,
                on_click=on_back
            )
        )
    
    controls.append(
        ft.Text(title, size=FontSize.XXL, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY)
    )
    
    return ft.Container(
        content=ft.Row(controls, spacing=0),
        padding=ft.Padding(Spacing.MD, 50, Spacing.XL, Spacing.SM),
    )


def simple_header(title: str) -> ft.Container:
    """简单页面标题"""
    return ft.Container(
        content=ft.Text(title, size=FontSize.XXL, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY),
        padding=ft.Padding(Spacing.XL, 60, Spacing.XL, Spacing.SM),
    )


# ============================================================
# 标签组件
# ============================================================

def tab_button(
    text: str,
    is_selected: bool,
    on_click: Optional[Callable] = None
) -> ft.Container:
    """标签按钮"""
    return ft.Container(
        content=ft.Text(
            text,
            size=FontSize.LG,
            weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_400,
            color=Theme.TEXT_PRIMARY if is_selected else Theme.TEXT_TERTIARY
        ),
        padding=ft.Padding(Spacing.LG, Spacing.SM, Spacing.LG, Spacing.SM),
        border_radius=BorderRadius.XXL,
        bgcolor=Theme.ACCENT if is_selected else "transparent",
        on_click=on_click,
    )


def toggle_button(
    text: str,
    is_selected: bool,
    on_click: Optional[Callable] = None
) -> ft.Container:
    """切换按钮（小型）"""
    return ft.Container(
        content=ft.Text(
            text,
            size=FontSize.BASE,
            color=Theme.TEXT_PRIMARY if is_selected else Theme.TEXT_SECONDARY
        ),
        padding=ft.Padding(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM),
        bgcolor=Theme.ACCENT if is_selected else "transparent",
        border_radius=BorderRadius.SM,
        on_click=on_click
    )


# ============================================================
# 数据展示组件
# ============================================================

def stat_item(
    label: str,
    value: str,
    color: str = Theme.TEXT_PRIMARY,
    label_size: int = FontSize.XS,
    value_size: int = FontSize.LG
) -> ft.Column:
    """统计数据项"""
    return ft.Column([
        ft.Text(label, size=label_size, color=Theme.TEXT_TERTIARY),
        ft.Text(value, size=value_size, color=color),
    ], spacing=2)


def pnl_display(
    value: float,
    show_sign: bool = True,
    size: int = FontSize.LG
) -> ft.Text:
    """盈亏金额显示"""
    color = Theme.DANGER if value >= 0 else Theme.SUCCESS
    sign = "+" if value >= 0 and show_sign else ""
    return ft.Text(f"{sign}{value:,.2f}", size=size, color=color, weight=ft.FontWeight.W_600)


def pct_display(
    value: float,
    show_sign: bool = True,
    size: int = FontSize.BASE
) -> ft.Text:
    """百分比显示"""
    color = Theme.DANGER if value >= 0 else Theme.SUCCESS
    sign = "+" if value >= 0 and show_sign else ""
    return ft.Text(f"{sign}{value:.2f}%", size=size, color=color)


# ============================================================
# 布局辅助
# ============================================================

def horizontal_padding(child: ft.Control, padding: int = Spacing.XL) -> ft.Container:
    """水平边距包装"""
    return ft.Container(
        content=child,
        padding=ft.Padding(padding, 0, padding, 0)
    )


def spacer(height: int) -> ft.Container:
    """垂直间距"""
    return ft.Container(height=height)


# ============================================================
# 下拉刷新组件
# ============================================================

def refreshable_container(
    content: ft.Control,
    on_refresh: Callable,
) -> ft.Column:
    """
    下拉刷新容器

    Args:
        content: 页面内容
        on_refresh: 刷新回调函数（异步）

    Returns:
        包装后的可刷新容器
    """
    # 使用 Flet 原生的下拉刷新（如果支持）
    # 否则使用简单的刷新按钮
    return ft.Column([content], scroll=ft.ScrollMode.AUTO, expand=True)

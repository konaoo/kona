"""
首页 - 资产总览（重构版）
优化版：资产里程碑数据 + 去掉 loading，显示 -- 占位符
"""
import flet as ft
from typing import Callable
import threading

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from api import api
from components import (
    gradient_card, horizontal_padding, spacer
)


def build_home_page(
    state: AppState,
    on_navigate: Callable[[str], None],
    on_switch_tab: Callable[[int], None],
    on_refresh: Callable[[], None] = None
) -> ft.Container:
    """
    构建首页

    新特性：
    - 资产里程碑数据（本月变动、今年变动、历史峰值）
    - 下方卡片显示总金额
    - 立即显示 UI，数据未加载时显示 --
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

    def display_change(value: float, prefix: str = "") -> str:
        """显示变动金额，如果为 0 则显示 --"""
        if value == 0:
            return "--"
        sign = "+" if value > 0 else ""
        formatted = f"{sign}{value:,.0f}"
        return state.mask_amount(formatted)

    # ============================================================
    # UI 组件
    # ============================================================

    eye_icon = ft.Icons.VISIBILITY_OFF if state.amount_hidden else ft.Icons.VISIBILITY

    # TODO: 这些数据需要后端支持，暂时使用占位符
    # 后续需要添加 API 接口获取：
    # - monthly_change: 本月变动
    # - yearly_change: 今年变动（从录入资产那一刻起）
    # - peak_value: 历史峰值
    monthly_change = 0  # 待实现
    yearly_change = 0   # 待实现
    peak_value = 0      # 待实现

    # 总资产卡片内容（新版 - 资产里程碑）
    card_content = ft.Column([
        # 标题 + 眼睛图标
        ft.Row([
            ft.Text("总资产估值", size=13, color=Theme.TEXT_SECONDARY),
            ft.IconButton(
                icon=eye_icon,
                icon_size=18,
                icon_color=Theme.TEXT_SECONDARY,
                on_click=lambda _: state.toggle_amount_hidden(),
            ),
        ], spacing=4),

        # 总资产金额
        ft.Text(
            display_amount(state.total_asset),
            size=FontSize.HERO,
            weight=ft.FontWeight.BOLD,
            color=Theme.TEXT_PRIMARY
        ),

        spacer(Spacing.XL),

        # 资产里程碑数据（三列）
        ft.Row([
            # 本月变动
            ft.Column([
                ft.Text("本月变动", size=11, color=Theme.TEXT_TERTIARY),
                ft.Text(
                    display_amount(monthly_change),
                    size=FontSize.LG,
                    weight=ft.FontWeight.W_600,
                    color=Theme.TEXT_PRIMARY
                ),
                ft.Text(
                    display_change(monthly_change),
                    size=FontSize.SM,
                    color=Theme.SUCCESS if monthly_change >= 0 else Theme.DANGER
                ),
            ], spacing=4, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),

            # 今年变动
            ft.Column([
                ft.Text("今年变动", size=11, color=Theme.TEXT_TERTIARY),
                ft.Text(
                    display_amount(yearly_change),
                    size=FontSize.LG,
                    weight=ft.FontWeight.W_600,
                    color=Theme.TEXT_PRIMARY
                ),
                ft.Text(
                    display_change(yearly_change),
                    size=FontSize.SM,
                    color=Theme.SUCCESS if yearly_change >= 0 else Theme.DANGER
                ),
            ], spacing=4, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),

            # 历史峰值
            ft.Column([
                ft.Text("历史峰值", size=11, color=Theme.TEXT_TERTIARY),
                ft.Text(
                    display_amount(peak_value),
                    size=FontSize.LG,
                    weight=ft.FontWeight.W_600,
                    color=Theme.TEXT_PRIMARY
                ),
                ft.Text(
                    display_change(state.total_asset - peak_value),
                    size=FontSize.SM,
                    color=Theme.SUCCESS if (state.total_asset - peak_value) >= 0 else Theme.DANGER
                ),
            ], spacing=4, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ]),
    ])

    # ============================================================
    # 资产分类卡片（新版 - 显示总金额）
    # ============================================================

    def build_asset_card(title: str, amount: float, icon: str, on_click_handler):
        """构建资产卡片（带箭头图标）"""
        return ft.Container(
            content=ft.Row([
                # 左侧：图标 + 文字
                ft.Row([
                    ft.Icon(icon, size=20, color=Theme.ACCENT),
                    ft.Column([
                        ft.Text(title, size=FontSize.BASE, color=Theme.TEXT_SECONDARY),
                        ft.Text(
                            display_amount(amount),
                            size=FontSize.XL,
                            weight=ft.FontWeight.BOLD,
                            color=Theme.TEXT_PRIMARY
                        ),
                    ], spacing=4),
                ], spacing=12),
                # 占位符（把箭头推到最右边）
                ft.Container(expand=True),
                # 右侧：箭头图标
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=24, color=Theme.TEXT_TERTIARY),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=Theme.BG_CARD,
            padding=Spacing.LG,
            border_radius=BorderRadius.LG,
            border=ft.border.all(1, Theme.BORDER),
            on_click=on_click_handler,
            ink=True,
        )

    # 垂直排列的 4 个卡片（1列4行）
    asset_cards = ft.Column([
        # 现金资产卡片
        build_asset_card(
            "现金资产",
            state.total_cash,
            ft.Icons.ACCOUNT_BALANCE_WALLET,
            lambda _: on_navigate("cash_detail")
        ),
        spacer(Spacing.MD),
        # 投资资产卡片（点击跳转投资页）
        build_asset_card(
            "投资资产",
            state.total_invest,
            ft.Icons.TRENDING_UP,
            lambda _: on_switch_tab(1)
        ),
        spacer(Spacing.MD),
        # 其他资产卡片
        build_asset_card(
            "其他资产",
            state.total_other,
            ft.Icons.DATASET,
            lambda _: on_navigate("other_detail")
        ),
        spacer(Spacing.MD),
        # 我的负债卡片
        build_asset_card(
            "我的负债",
            0,  # TODO: 需要添加负债数据到 state
            ft.Icons.CREDIT_CARD,
            lambda _: on_navigate("liability_detail")
        ),
    ], spacing=0)

    # ============================================================
    # 添加资产按钮 + 弹窗逻辑
    # ============================================================

    def show_add_overlay(e):
        """显示添加资产弹窗"""
        # 控件定义
        type_dropdown = ft.Dropdown(
            label="资产类型",
            options=[
                ft.dropdown.Option("cash", "现金资产"),
                ft.dropdown.Option("other", "其他资产"),
                ft.dropdown.Option("liability", "我的负债"),  # 🔧 文案改为"我的负债"
            ],
            border_color=Theme.ACCENT,
            value="cash",
            bgcolor=Theme.BG_CARD,
            border_radius=BorderRadius.MD,
            content_padding=Spacing.LG,
            text_style=ft.TextStyle(color=Theme.TEXT_PRIMARY),
            label_style=ft.TextStyle(color=Theme.TEXT_SECONDARY),
        )

        name_field = ft.TextField(
            label="资产名称",  # 🔧 文案改为"资产名称"
            border_color=Theme.ACCENT,
            bgcolor=Theme.BG_CARD,
            border_radius=BorderRadius.MD,
            content_padding=Spacing.LG,
            color=Theme.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=Theme.TEXT_SECONDARY),
        )

        amount_field = ft.TextField(
            label="金额",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=Theme.ACCENT,
            bgcolor=Theme.BG_CARD,
            border_radius=BorderRadius.MD,
            content_padding=Spacing.LG,
            color=Theme.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=Theme.TEXT_SECONDARY),
        )

        save_btn_ref = ft.Ref[ft.ElevatedButton]()
        overlay_ref = [None]

        def close_overlay(_=None):
            if overlay_ref[0] and overlay_ref[0] in state.page.overlay:
                state.page.overlay.remove(overlay_ref[0])
                state.page.update()

        def save_asset(_):
            asset_type = type_dropdown.value
            name = name_field.value.strip()
            amount_str = amount_field.value.strip()

            if not name or not amount_str:
                name_field.error_text = "必填" if not name else None
                amount_field.error_text = "必填" if not amount_str else None
                state.page.update()
                return

            try:
                amount = float(amount_str)
            except ValueError:
                amount_field.error_text = "格式错误"
                state.page.update()
                return

            save_btn_ref.current.text = "保存中..."
            save_btn_ref.current.disabled = True
            state.page.update()

            def do_save():
                success = False
                try:
                    if asset_type == "cash":
                        success = api.add_cash_asset_sync(name, amount)
                    elif asset_type == "other":
                        success = api.add_other_asset_sync(name, amount)
                    elif asset_type == "liability":
                        success = api.add_liability_sync(name, amount)
                except Exception as ex:
                    print(f"Save error: {ex}")

                try:
                    if overlay_ref[0] and overlay_ref[0] in state.page.overlay:
                        state.page.overlay.remove(overlay_ref[0])
                    if success and on_refresh:
                        on_refresh()
                    state.page.update()
                except Exception as ex:
                    print(f"Close overlay error: {ex}")

            threading.Thread(target=do_save, daemon=True).start()

        dialog_card = ft.Container(
            content=ft.Stack([
                # 主体内容
                ft.Column([
                    ft.Container(
                        content=ft.Text(
                            "记一笔",
                            size=FontSize.XXL,
                            weight=ft.FontWeight.BOLD,
                            color=Theme.TEXT_PRIMARY
                        ),
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding(0, 0, 0, Spacing.MD),
                    ),
                    type_dropdown,
                    spacer(Spacing.MD),
                    name_field,
                    spacer(Spacing.MD),
                    amount_field,
                    spacer(Spacing.XXL),
                    # 🔧 去掉取消按钮，只保留保存按钮，居中显示
                    ft.Container(
                        content=ft.ElevatedButton(
                            "保存",
                            ref=save_btn_ref,
                            bgcolor=Theme.ACCENT,
                            color=Theme.TEXT_PRIMARY,
                            on_click=save_asset,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                                padding=ft.Padding(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG),
                            ),
                        ),
                        alignment=ft.Alignment(0, 0),  # 居中
                    ),
                ], tight=True),
                # 🔧 右上角X关闭按钮
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=20,
                        icon_color=Theme.TEXT_SECONDARY,
                        on_click=close_overlay,
                        tooltip="关闭",
                    ),
                    alignment=ft.Alignment(1, -1),  # 右上角
                ),
            ]),
            bgcolor=Theme.BG_ELEVATED,
            padding=Spacing.XXL,
            border_radius=BorderRadius.XXL,
            border=ft.border.all(1, Theme.BORDER),
            width=320,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color="#00000030",
                offset=ft.Offset(0, 4),
            ),
        )

        overlay = ft.Container(
            content=ft.Stack([
                ft.Container(
                    bgcolor="#00000080",
                    expand=True,
                    on_click=close_overlay
                ),
                ft.Container(
                    content=dialog_card,
                    alignment=ft.Alignment(0, 0)
                ),
            ]),
            expand=True,
        )

        overlay_ref[0] = overlay
        state.page.overlay.append(overlay)
        state.page.update()

    # ============================================================
    # 页面布局
    # ============================================================

    return ft.Container(
        content=ft.Column([
            spacer(Spacing.LG),  # 🔧 减少顶部间距，卡片移到最顶部

            # 总资产卡片
            horizontal_padding(gradient_card(card_content, padding=Spacing.XXL)),

            spacer(Spacing.XXL),

            # 资产分类卡片（垂直布局 - 1列4行）
            horizontal_padding(asset_cards),

            spacer(Spacing.XXL),

            # 🔧 添加按钮 - 居中显示
            ft.Container(
                content=ft.ElevatedButton(
                    "记一笔",
                    icon=ft.Icons.ADD,
                    bgcolor=Theme.ACCENT,
                    color=Theme.TEXT_PRIMARY,
                    on_click=show_add_overlay,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.LG),
                        padding=ft.Padding(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG),
                    ),
                ),
                alignment=ft.Alignment(0, 0),  # 居中对齐
                padding=ft.Padding(Spacing.XL, 0, Spacing.XL, 0),
            ),

            spacer(Spacing.XXL),
        ], scroll=ft.ScrollMode.AUTO),  # 🔧 添加滚动支持
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )

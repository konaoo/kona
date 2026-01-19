"""
首页 - 资产总览
"""
import flet as ft
from typing import Callable
import threading

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from api import api
from components import (
    asset_row, gradient_card, horizontal_padding, spacer
)


def build_home_page(
    state: AppState,
    on_navigate: Callable[[str], None],
    on_switch_tab: Callable[[int], None],
    on_refresh: Callable[[], None] = None
) -> ft.Container:
    """
    构建首页
    """
    eye_icon = ft.Icons.VISIBILITY_OFF if state.amount_hidden else ft.Icons.VISIBILITY
    
    # 总资产卡片内容
    card_content = ft.Column([
        ft.Row([
            ft.Text("总资产估值", size=13, color=Theme.TEXT_SECONDARY),
            ft.IconButton(
                icon=eye_icon,
                icon_size=18,
                icon_color=Theme.TEXT_SECONDARY,
                on_click=lambda _: state.toggle_amount_hidden(),
            ),
        ], spacing=4),
        ft.Text(
            state.mask_amount(f"¥{state.total_asset:,.0f}"),
            size=FontSize.HERO,
            weight=ft.FontWeight.BOLD,
            color=Theme.TEXT_PRIMARY
        ),
        spacer(Spacing.XL),
        # 三列显示
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("现金资产", size=11, color=Theme.TEXT_TERTIARY),
                    ft.Text(state.mask_amount(f"¥{state.total_cash:,.0f}"), size=FontSize.LG, color=Theme.TEXT_PRIMARY),
                ], spacing=4, expand=True),
                on_click=lambda _: on_navigate("cash_detail"),
                ink=True,
                padding=10,
                border_radius=8,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("投资资产", size=11, color=Theme.TEXT_TERTIARY),
                    ft.Text(state.mask_amount(f"¥{state.total_invest:,.0f}"), size=FontSize.LG, color=Theme.TEXT_PRIMARY),
                ], spacing=4, expand=True),
                on_click=lambda _: on_switch_tab(1),
                ink=True,
                padding=10,
                border_radius=8,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("其他资产", size=11, color=Theme.TEXT_TERTIARY),
                    ft.Text(state.mask_amount(f"¥{state.total_other:,.0f}"), size=FontSize.LG, color=Theme.TEXT_PRIMARY),
                ], spacing=4, expand=True),
                on_click=lambda _: on_navigate("other_detail"),
                ink=True,
                padding=10,
                border_radius=8,
            ),
        ]),
    ])
    
    # ============================================================
    # 自定义弹窗逻辑 (Overlay)
    # ============================================================
    
    def show_add_overlay(e):
        """显示添加资产弹窗"""
        # 控件定义
        type_dropdown = ft.Dropdown(
            label="资产类型",
            options=[
                ft.dropdown.Option("cash", "现金资产"),
                ft.dropdown.Option("other", "其他资产"),
                ft.dropdown.Option("liability", "负债"),
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
            label="名称", 
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
        overlay_ref = [None]  # 用于存储 overlay 引用
        
        def close_overlay(_):
            if overlay_ref[0] and overlay_ref[0] in state.page.overlay:
                state.page.overlay.remove(overlay_ref[0])
                state.page.update()
            
        def save_asset(_):
            asset_type = type_dropdown.value
            name = name_field.value.strip()
            amount_str = amount_field.value.strip()
            
            # 验证输入
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
            
            # UI 反馈
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
                
                # 关闭弹窗并刷新
                try:
                    if overlay_ref[0] and overlay_ref[0] in state.page.overlay:
                        state.page.overlay.remove(overlay_ref[0])
                    if success and on_refresh:
                        on_refresh()
                    state.page.update()
                except Exception as ex:
                    print(f"Close overlay error: {ex}")
            
            threading.Thread(target=do_save, daemon=True).start()

        # 弹窗卡片 - 统一UI风格
        dialog_card = ft.Container(
            content=ft.Column([
                # 标题
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
                # 按钮行
                ft.Row([
                    ft.TextButton(
                        "取消", 
                        on_click=close_overlay,
                        style=ft.ButtonStyle(
                            color=Theme.TEXT_SECONDARY,
                            padding=Spacing.LG,
                        )
                    ),
                    ft.ElevatedButton(
                        "保存", 
                        ref=save_btn_ref,
                        bgcolor=Theme.ACCENT, 
                        color=Theme.TEXT_PRIMARY,
                        on_click=save_asset,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                            padding=Spacing.LG,
                        ),
                        width=120,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], tight=True),
            bgcolor=Theme.BG_ELEVATED,
            padding=Spacing.XXL,
            border_radius=BorderRadius.XXL,
            border=ft.border.all(1, Theme.BORDER),
            width=320,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color="#80000000",
            ),
            on_click=lambda _: None,  # 阻止点击穿透
        )
        
        # 全屏遮罩
        overlay = ft.Container(
            content=ft.Container(content=dialog_card, alignment=ft.Alignment(0, 0)),
            bgcolor="#B3000000",  # 70% 黑色遮罩
            expand=True,
            on_click=close_overlay,
            alignment=ft.Alignment(0, 0),
        )
        
        overlay_ref[0] = overlay
        state.page.overlay.append(overlay)
        state.page.update()

    
    # 设置页面级 FAB
    state.page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        bgcolor=Theme.ACCENT,
        on_click=show_add_overlay,
    )
    
    return ft.Container(
        content=ft.Column([
                spacer(60),
                
                # 总资产卡片
                horizontal_padding(gradient_card(card_content)),
                
                spacer(Spacing.XXL),
                
                # 资产入口
                horizontal_padding(
                    ft.Column([
                        asset_row(ft.Icons.ACCOUNT_BALANCE_WALLET, "现金资产", lambda _: on_navigate("cash_detail")),
                        spacer(Spacing.SM),
                        asset_row(ft.Icons.TRENDING_UP, "投资资产", lambda _: on_switch_tab(1)),
                        spacer(Spacing.SM),
                        asset_row(ft.Icons.DIAMOND, "其他资产", lambda _: on_navigate("other_detail")),
                        spacer(Spacing.SM),
                        asset_row(ft.Icons.CREDIT_CARD, "我的负债", lambda _: on_navigate("liability_detail")),
                    ])
                ),
                
                spacer(80), # 底部留白
            ], scroll=ft.ScrollMode.AUTO),
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )

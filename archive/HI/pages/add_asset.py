"""
添加资产页面
"""
import flet as ft
from typing import Callable
import threading

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from api import api
from components import page_header, spacer

def build_add_asset_page(
    state: AppState,
    on_back: Callable,
    on_refresh: Callable
) -> ft.Container:
    
    # 状态
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
    )
    name_field = ft.TextField(label="名称", border_color=Theme.ACCENT, bgcolor=Theme.BG_CARD)
    amount_field = ft.TextField(label="金额", keyboard_type=ft.KeyboardType.NUMBER, border_color=Theme.ACCENT, bgcolor=Theme.BG_CARD)
    
    def save_asset(e):
        asset_type = type_dropdown.value
        name = name_field.value.strip()
        amount_str = amount_field.value.strip()
        
        if not name or not amount_str:
            name_field.error_text = "请输入名称" if not name else None
            amount_field.error_text = "请输入金额" if not amount_str else None
            state.page.update()
            return
            
        try:
            amount = float(amount_str)
        except ValueError:
            amount_field.error_text = "金额格式错误"
            state.page.update()
            return
            
        # 禁用按钮防止重复提交
        save_btn.disabled = True
        save_btn.text = "保存中..."
        state.page.update()
        
        def do_save():
            success = False
            if asset_type == "cash":
                success = api.add_cash_asset_sync(name, amount)
            elif asset_type == "other":
                success = api.add_other_asset_sync(name, amount)
            elif asset_type == "liability":
                success = api.add_liability_sync(name, amount)
            
            if success:
                if on_refresh:
                    on_refresh()
                # 返回上一页
                on_back(None)
            else:
                save_btn.disabled = False
                save_btn.text = "保存失败，重试"
                state.page.update()
        
        threading.Thread(target=do_save, daemon=True).start()
    
    save_btn = ft.ElevatedButton(
        "保存",
        on_click=save_asset,
        bgcolor=Theme.ACCENT,
        color=Theme.TEXT_PRIMARY,
        height=50,
        width=200,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
        )
    )
    
    return ft.Container(
        content=ft.Column([
            page_header("记一笔", on_back=on_back),
            
            ft.Container(
                content=ft.Column([
                    type_dropdown,
                    spacer(Spacing.MD),
                    name_field,
                    spacer(Spacing.MD),
                    amount_field,
                    spacer(Spacing.XL),
                    save_btn
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=Spacing.XL,
                alignment=ft.Alignment(0, 0)
            )
        ]),
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )

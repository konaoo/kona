"""
详情页面 - 现金资产/其他资产/负债详情
重构版本：优化删除交互、页面加载、UI风格
"""
import flet as ft
from typing import Callable, List, Dict
import threading

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from api import api
from components import (
    loading_indicator, empty_state, error_state,
    page_header, card, spacer
)


def build_detail_page(
    state: AppState,
    title: str,
    page_type: str,
    on_back: Callable
) -> ft.Container:
    """
    构建详情页面
    """
    
    # 根据类型确定配置
    config_map = {
        "cash_detail": {
            "icon": ft.Icons.ACCOUNT_BALANCE_WALLET,
            "empty_text": "暂无现金资产",
            "is_liability": False,
            "fetch_sync": api.get_cash_assets_sync,
            "add_sync": api.add_cash_asset_sync,
            "delete_sync": api.delete_cash_asset_sync,
            "add_title": "添加现金资产",
        },
        "other_detail": {
            "icon": ft.Icons.DIAMOND,
            "empty_text": "暂无其他资产",
            "is_liability": False,
            "fetch_sync": api.get_other_assets_sync,
            "add_sync": api.add_other_asset_sync,
            "delete_sync": api.delete_other_asset_sync,
            "add_title": "添加其他资产",
        },
        "liability_detail": {
            "icon": ft.Icons.CREDIT_CARD,
            "empty_text": "暂无负债",
            "is_liability": True,
            "fetch_sync": api.get_liabilities_sync,
            "add_sync": api.add_liability_sync,
            "delete_sync": api.delete_liability_sync,
            "add_title": "添加负债",
        },
    }
    
    config = config_map.get(page_type, config_map["cash_detail"])
    is_liability = config["is_liability"]
    
    # 使用字典存储状态，避免闭包问题
    page_state = {
        "assets_data": [],
        "is_loading": True,
    }
    
    # 列表视图 - 使用 ListView 支持滚动
    list_view = ft.ListView(
        controls=[loading_indicator()],
        spacing=Spacing.SM,
        padding=ft.Padding(Spacing.XL, 0, Spacing.XL, 100),  # 底部留白100，避免FAB遮挡
        expand=True,
    )
    
    # ============================================================
    # 删除确认弹窗
    # ============================================================
    def show_delete_confirm(asset_id: int, asset_name: str):
        """显示删除确认弹窗"""
        overlay_ref = [None]
        
        def close_overlay(_=None):
            if overlay_ref[0] and overlay_ref[0] in state.page.overlay:
                state.page.overlay.remove(overlay_ref[0])
                state.page.update()
        
        def confirm_delete(_):
            close_overlay()
            do_delete_asset(asset_id)
        
        dialog_card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=48, color=Theme.DANGER),
                spacer(Spacing.MD),
                ft.Text(
                    "确认删除", 
                    size=FontSize.XXL, 
                    weight=ft.FontWeight.BOLD,
                    color=Theme.TEXT_PRIMARY
                ),
                spacer(Spacing.SM),
                ft.Text(
                    f"确定要删除「{asset_name}」吗？",
                    size=FontSize.LG,
                    color=Theme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                spacer(Spacing.XXL),
                ft.Row([
                    ft.TextButton(
                        "取消",
                        on_click=close_overlay,
                        style=ft.ButtonStyle(color=Theme.TEXT_SECONDARY, padding=Spacing.LG)
                    ),
                    ft.ElevatedButton(
                        "确认删除",
                        bgcolor=Theme.DANGER,
                        color=Theme.TEXT_PRIMARY,
                        on_click=confirm_delete,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                            padding=Spacing.LG,
                        ),
                        width=120,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=Theme.BG_ELEVATED,
            padding=Spacing.XXL,
            border_radius=BorderRadius.XXL,
            border=ft.border.all(1, Theme.BORDER),
            width=300,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=20, color="#80000000"),
            on_click=lambda _: None,
        )
        
        overlay = ft.Container(
            content=ft.Container(content=dialog_card, alignment=ft.Alignment(0, 0)),
            bgcolor="#B3000000",
            expand=True,
            on_click=close_overlay,
            alignment=ft.Alignment(0, 0),
        )
        
        overlay_ref[0] = overlay
        state.page.overlay.append(overlay)
        state.page.update()
    
    # ============================================================
    # 删除资产
    # ============================================================
    def do_delete_asset(asset_id: int):
        """执行删除资产操作"""
        # 立即从本地移除并更新UI
        page_state["assets_data"] = [
            item for item in page_state["assets_data"] 
            if item.get('id') != asset_id
        ]
        render_list()
        
        # 后台执行API删除
        def delete_in_bg():
            try:
                success = config["delete_sync"](asset_id)
                if not success:
                    print(f"Delete failed: {asset_id}")
            except Exception as ex:
                print(f"Delete error: {ex}")
        
        threading.Thread(target=delete_in_bg, daemon=True).start()
    
    # ============================================================
    # 构建列表项
    # ============================================================
    def build_asset_item(asset_id: int, name: str, amount: float):
        """构建资产列表项"""
        color = Theme.DANGER if is_liability else Theme.TEXT_PRIMARY
        prefix = "-" if is_liability else ""
        
        def on_delete_click(e):
            show_delete_confirm(asset_id, name)
        
        return ft.Container(
            content=ft.Row([
                # 左侧：资产名称
                ft.Text(name, size=15, color=Theme.TEXT_PRIMARY, expand=True),
                # 中间：金额
                ft.Text(
                    f"{prefix}¥{amount:,.0f}", 
                    size=15, 
                    weight=ft.FontWeight.W_600, 
                    color=color
                ),
                # 右侧：删除按钮
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=Theme.TEXT_TERTIARY,
                    icon_size=20,
                    tooltip="删除",
                    on_click=on_delete_click,
                    style=ft.ButtonStyle(padding=8),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(Spacing.LG, Spacing.MD, Spacing.SM, Spacing.MD),
            bgcolor=Theme.BG_CARD,
            border_radius=BorderRadius.LG,
        )
    
    # ============================================================
    # 渲染列表
    # ============================================================
    def render_list():
        """根据数据渲染列表"""
        controls = []
        assets = page_state["assets_data"]
        
        if not assets:
            controls.append(empty_state(config["icon"], config["empty_text"]))
        else:
            # 计算总额
            total = sum(float(item.get('amount', 0)) for item in assets)
            color = Theme.DANGER if is_liability else Theme.TEXT_PRIMARY
            prefix = "-" if is_liability else ""
            
            # 总额卡片 - 不额外加padding，由ListView统一控制
            controls.append(
                card(
                    ft.Column([
                        ft.Text(f"{title}总额", size=FontSize.LG, color=Theme.TEXT_SECONDARY),
                        ft.Text(
                            f"{prefix}¥{total:,.0f}",
                            size=FontSize.HERO,
                            weight=ft.FontWeight.BOLD,
                            color=color
                        ),
                    ]),
                    padding=Spacing.XL,
                    border_radius=BorderRadius.XL,
                )
            )
            controls.append(spacer(Spacing.SM))
            
            # 列表项
            for item in assets:
                asset_id = item.get('id')
                name = item.get('name', '未命名')
                amount = float(item.get('amount', 0))
                controls.append(build_asset_item(asset_id, name, amount))
        
        list_view.controls = controls
        safe_update()
    
    # ============================================================
    # 安全更新UI
    # ============================================================
    def safe_update():
        """安全地更新UI"""
        try:
            list_view.update()
        except Exception:
            try:
                state.page.update()
            except Exception:
                pass
    
    # ============================================================
    # 加载数据
    # ============================================================
    def load_data():
        """加载资产数据"""
        page_state["is_loading"] = True
        list_view.controls = [loading_indicator()]
        safe_update()
        
        def fetch():
            try:
                data = config["fetch_sync"]()
                page_state["assets_data"] = data if data else []
                page_state["is_loading"] = False
                render_list()
            except Exception as ex:
                print(f"Load error: {ex}")
                page_state["is_loading"] = False
                list_view.controls = [error_state("加载失败，请返回重试")]
                safe_update()
        
        threading.Thread(target=fetch, daemon=True).start()
    
    # ============================================================
    # 添加资产弹窗
    # ============================================================
    def show_add_dialog(_):
        """显示添加资产弹窗"""
        overlay_ref = [None]
        
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
        
        def close_overlay(_=None):
            if overlay_ref[0] and overlay_ref[0] in state.page.overlay:
                state.page.overlay.remove(overlay_ref[0])
                state.page.update()
        
        def save_click(_):
            name = name_field.value.strip()
            amount_str = amount_field.value.strip()
            
            # 验证
            has_error = False
            if not name:
                name_field.error_text = "请输入名称"
                has_error = True
            else:
                name_field.error_text = None
                
            if not amount_str:
                amount_field.error_text = "请输入金额"
                has_error = True
            else:
                amount_field.error_text = None
            
            if has_error:
                state.page.update()
                return
            
            try:
                amount = float(amount_str)
            except ValueError:
                amount_field.error_text = "金额格式错误"
                state.page.update()
                return
            
            # 禁用按钮
            save_btn_ref.current.text = "保存中..."
            save_btn_ref.current.disabled = True
            state.page.update()
            
            def do_save():
                try:
                    success = config["add_sync"](name, amount)
                    # 先关闭弹窗
                    if overlay_ref[0] and overlay_ref[0] in state.page.overlay:
                        state.page.overlay.remove(overlay_ref[0])
                    
                    if success:
                        # 重新加载数据
                        load_data()
                    else:
                        state.page.update()
                except Exception as ex:
                    print(f"Save error: {ex}")
                    if overlay_ref[0] and overlay_ref[0] in state.page.overlay:
                        state.page.overlay.remove(overlay_ref[0])
                    state.page.update()
            
            threading.Thread(target=do_save, daemon=True).start()
        
        dialog_card = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(
                        config["add_title"], 
                        size=FontSize.XXL, 
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(0, 0, 0, Spacing.MD),
                ),
                name_field,
                spacer(Spacing.MD),
                amount_field,
                spacer(Spacing.XXL),
                ft.Row([
                    ft.TextButton(
                        "取消",
                        on_click=close_overlay,
                        style=ft.ButtonStyle(color=Theme.TEXT_SECONDARY, padding=Spacing.LG)
                    ),
                    ft.ElevatedButton(
                        "保存",
                        ref=save_btn_ref,
                        bgcolor=Theme.ACCENT,
                        color=Theme.TEXT_PRIMARY,
                        on_click=save_click,
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
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=20, color="#80000000"),
            on_click=lambda _: None,
        )
        
        overlay = ft.Container(
            content=ft.Container(content=dialog_card, alignment=ft.Alignment(0, 0)),
            bgcolor="#B3000000",
            expand=True,
            on_click=close_overlay,
            alignment=ft.Alignment(0, 0),
        )
        
        overlay_ref[0] = overlay
        state.page.overlay.append(overlay)
        state.page.update()
    
    # ============================================================
    # 初始化加载
    # ============================================================
    load_data()
    
    # ============================================================
    # 页面布局
    # ============================================================
    return ft.Container(
        content=ft.Stack([
            ft.Column([
                page_header(title, on_back=on_back),
                list_view,
            ]),
            # 悬浮添加按钮
            ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                bgcolor=Theme.ACCENT,
                on_click=show_add_dialog,
                right=20,
                bottom=20,
            )
        ]),
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )

"""
我的页面 - 个人中心
"""
import flet as ft
import asyncio

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from components import setting_row, spacer
from auth.manager import auth_manager


def build_profile_page(state: AppState, on_logout: callable = None, on_navigate: callable = None) -> ft.Container:
    """
    构建我的页面
    
    Args:
        state: 应用状态
        on_logout: 退出登录回调
        on_navigate: 页面跳转回调
    """
    
    # 获取本地存储的用户信息
    try:
        nickname = state.page.client_storage.get("nickname") or "咔咔用户"
        avatar_base64 = state.page.client_storage.get("avatar_base64")
    except Exception:
        nickname = "咔咔用户"
        avatar_base64 = None
    
    email = auth_manager.email or ""
    
    # === 获取用户 ID ===
    try:
        user_number = state.page.client_storage.get("user_number")
        display_id = f"ID: {user_number}" if user_number else ""
    except:
        display_id = ""
    # =================
    
    async def handle_logout(e):
        """处理退出登录"""
        await auth_manager.logout()
        if on_logout:
            on_logout()
    
    def on_logout_click(e):
        """退出登录按钮点击"""
        asyncio.create_task(handle_logout(e))
        
    def go_edit(e):
        if on_navigate:
            on_navigate("edit_profile")
        
    def show_about_dialog(e):
        # ... (keep existing)
        state.page.dialog = ft.AlertDialog(
            title=ft.Text("关于我们"),
            content=ft.Column([
                ft.Image(src="/icon.png", width=64, height=64, error_content=ft.Icon(ft.Icons.APPS, size=64)),
                ft.Text("咔咔记账", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("v1.0.0", size=14, color=Theme.TEXT_SECONDARY),
                spacer(10),
                ft.Text("专注于个人资产管理的极简应用。", size=14),
                ft.Text("© 2026 Kona Tool", size=12, color=Theme.TEXT_TERTIARY),
            ], height=200, tight=True, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("确定", on_click=lambda _: state.page.close_dialog()),
            ],
        )
        state.page.dialog.open = True
        state.page.update()

    # UI 引用
    nickname_text_control = ft.Text(nickname, size=FontSize.XL, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY)
    
    # 头像
    avatar_content = None
    if avatar_base64:
        avatar_content = ft.Image(src_base64=avatar_base64, fit="cover", width=70, height=70, border_radius=35)
    else:
        avatar_content = ft.CircleAvatar(
            content=ft.Text(nickname[0].upper(), size=24, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY),
            bgcolor=Theme.ACCENT,
            radius=35
        )

    return ft.Container(
        content=ft.Column([
            spacer(Spacing.XL), # 顶部间距
            
            # 用户信息卡片 (可点击编辑)
            ft.Container(
                content=ft.Row([
                    avatar_content if isinstance(avatar_content, ft.Image) else avatar_content,
                    ft.Container(width=Spacing.LG),
                    ft.Column([
                        nickname_text_control,
                        ft.Text(email, size=13, color=Theme.TEXT_SECONDARY),
                        ft.Text(display_id, size=11, color=Theme.TEXT_TERTIARY),
                    ], spacing=4, expand=True),
                    ft.IconButton(ft.Icons.EDIT, icon_color=Theme.TEXT_TERTIARY, on_click=go_edit)
                ]),
                padding=ft.Padding(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG),
                bgcolor=Theme.BG_CARD,
                border_radius=BorderRadius.LG,
                margin=ft.Margin(Spacing.LG, 0, Spacing.LG, Spacing.LG),
                on_click=go_edit,
            ),
            
            # 设置项
            ft.Container(
                content=ft.Column([
                    setting_row(ft.Icons.SETTINGS, "系统设置"),
                    # spacer(Spacing.SM),
                    # setting_row(ft.Icons.CLOUD_UPLOAD, "数据备份"), # 已移除
                    spacer(Spacing.SM),
                    setting_row(ft.Icons.INFO_OUTLINE, "关于我们", on_click=show_about_dialog),
                ]),
                padding=ft.Padding(Spacing.XL, 0, Spacing.XL, 0),
            ),
            
            # 占位
            ft.Container(expand=True),
            
            # 退出登录按钮
            ft.Container(
                content=ft.Container(
                    content=ft.Text(
                        "退出登录",
                        size=FontSize.LG,
                        color=Theme.DANGER,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    bgcolor=Theme.BG_CARD,
                    border_radius=BorderRadius.MD,
                    padding=ft.Padding(0, Spacing.LG, 0, Spacing.LG),
                    alignment=ft.Alignment(0, 0),
                    on_click=on_logout_click,
                    ink=True,
                ),
                padding=ft.Padding(Spacing.XL, 0, Spacing.XL, Spacing.XXL),
            ),
        ], scroll=ft.ScrollMode.AUTO),
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )

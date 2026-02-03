"""
登录页面

UI 风格与主应用保持一致（深色主题）
优化：按钮点击效果、异步加载防卡顿
"""
import flet as ft
import asyncio
import re
from typing import Callable

from config import Theme, Spacing, FontSize, BorderRadius
from components import spacer
from auth.manager import auth_manager


def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def build_login_page(
    page: ft.Page,
    on_login_success: Callable[[], None]
) -> ft.Container:
    """
    构建登录页面
    
    Args:
        page: Flet 页面对象
        on_login_success: 登录成功回调
    """
    
    # ========== 状态 ==========
    state = {
        "step": "email",  # email | code
        "countdown": 0,
        "send_loading": False,  # 发送按钮加载中
        "login_loading": False,  # 登录按钮加载中
        "send_disabled": False,  # 发送按钮禁用（倒计时中）
    }
    
    # ========== 组件引用 ==========
    email_field = ft.TextField(
        label="邮箱地址",
        hint_text="example@email.com",
        keyboard_type=ft.KeyboardType.EMAIL,
        border_color=Theme.BORDER,
        focused_border_color=Theme.ACCENT,
        label_style=ft.TextStyle(color=Theme.TEXT_SECONDARY),
        text_style=ft.TextStyle(color=Theme.TEXT_PRIMARY),
        hint_style=ft.TextStyle(color=Theme.TEXT_TERTIARY),
        cursor_color=Theme.ACCENT,
        bgcolor=Theme.BG_CARD,
        border_radius=BorderRadius.MD,
        expand=True,
        height=56,  # 🔧 统一高度
        content_padding=ft.Padding(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM),
    )

    code_field = ft.TextField(
        label="验证码",
        hint_text="请输入6位数字验证码",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=Theme.BORDER,
        focused_border_color=Theme.ACCENT,
        label_style=ft.TextStyle(color=Theme.TEXT_SECONDARY),
        text_style=ft.TextStyle(color=Theme.TEXT_PRIMARY),
        hint_style=ft.TextStyle(color=Theme.TEXT_TERTIARY),
        cursor_color=Theme.ACCENT,
        bgcolor=Theme.BG_CARD,
        border_radius=BorderRadius.MD,
        visible=True,  # 🔧 始终显示验证码输入框
        max_length=6,
        height=56,  # 🔧 统一高度
        content_padding=ft.Padding(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM),
        on_change=lambda e: on_code_change(e),  # 🔧 监听输入变化
    )
    
    error_text = ft.Text(
        "",
        size=FontSize.BASE,
        color=Theme.DANGER,
        visible=False,
    )
    
    # 发送按钮文字
    send_button_text = ft.Text(
        "发送验证码",  # 🔧 改为更明确的文案
        size=13,
        weight=ft.FontWeight.BOLD,
        color=Theme.TEXT_PRIMARY,
    )
    
    # 发送按钮 loading 指示器
    send_button_loading = ft.ProgressRing(
        width=16,
        height=16,
        stroke_width=2,
        color=Theme.TEXT_PRIMARY,
        visible=False,
    )
    
    # 发送按钮内容
    send_button_content = ft.Row(
        [send_button_text, send_button_loading],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
    )
    
    # 登录按钮文字
    login_button_text = ft.Text(
        "登录",
        size=FontSize.LG,
        weight=ft.FontWeight.W_600,
        color=Theme.TEXT_PRIMARY,
    )
    
    # 登录按钮 loading 指示器
    login_button_loading = ft.ProgressRing(
        width=20,
        height=20,
        stroke_width=2,
        color=Theme.TEXT_PRIMARY,
        visible=False,
    )
    
    # 登录按钮内容
    login_button_content = ft.Row(
        [login_button_text, login_button_loading],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )
    
    # ========== 方法 ==========
    def show_error(message: str):
        """显示错误信息"""
        error_text.value = message
        error_text.visible = True
        page.update()

    def hide_error():
        """隐藏错误信息"""
        error_text.visible = False
        page.update()

    def on_code_change(e):
        """验证码输入变化时检查登录按钮状态"""
        code = code_field.value.strip()
        # 🔧 当验证码输入完整（6位）时，登录按钮可用；否则灰色禁用
        if len(code) == 6:
            login_button.bgcolor = Theme.ACCENT
            login_button.opacity = 1.0
        else:
            login_button.bgcolor = Theme.BG_ELEVATED
            login_button.opacity = 0.5
        page.update()
    
    def update_send_button(loading: bool = False, disabled: bool = False, text: str = None):
        """更新发送按钮状态"""
        state["send_loading"] = loading
        state["send_disabled"] = disabled
        send_button_loading.visible = loading
        send_button_text.visible = not loading
        if text:
            send_button_text.value = text

        # 🔧 禁用时灰色，正常时强调色
        if disabled or loading:
            send_button.bgcolor = Theme.BG_ELEVATED
            send_button.opacity = 0.6
        else:
            send_button.bgcolor = Theme.ACCENT
            send_button.opacity = 1.0
        page.update()
    
    def update_login_button(loading: bool = False):
        """更新登录按钮状态"""
        state["login_loading"] = loading
        login_button_loading.visible = loading
        login_button_text.visible = not loading
        login_button.bgcolor = Theme.BG_ELEVATED if loading else Theme.ACCENT
        page.update()
    
    async def do_send_code():
        """发送验证码（异步执行）"""
        email = email_field.value.strip()
        
        # 验证邮箱
        if not email:
            show_error("请输入邮箱地址")
            return
        
        if not is_valid_email(email):
            show_error("请输入有效的邮箱地址")
            return
        
        hide_error()
        update_send_button(loading=True)
        
        # 异步发送验证码
        success, error = await auth_manager.send_code(email)
        
        if success:
            # 🔧 切换到验证码输入步骤（验证码输入框已经始终可见）
            state["step"] = "code"

            # 开始倒计时
            state["countdown"] = 60
            update_send_button(disabled=True, text=f"重新发送({state['countdown']}s)")  # 🔧 改为"重新发送"

            # 启动倒计时任务
            asyncio.create_task(countdown_timer())
            page.update()

            # 自动聚焦验证码输入框 (兼容新旧版本)
            try:
                res = code_field.focus()
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                pass
        else:
            update_send_button(loading=False)
            show_error(error or "发送失败，请稍后重试")
    
    async def countdown_timer():
        """倒计时"""
        while state["countdown"] > 0:
            await asyncio.sleep(1)
            state["countdown"] -= 1
            if state["countdown"] > 0:
                update_send_button(disabled=True, text=f"重新发送({state['countdown']}s)")  # 🔧 倒计时文案
            else:
                update_send_button(disabled=False, text="重新发送")  # 🔧 倒计时结束后显示"重新发送"
    
    async def do_verify_code():
        """验证验证码（异步执行）"""
        email = email_field.value.strip()
        code = code_field.value.strip()
        
        if not code:
            show_error("请输入验证码")
            return
        
        hide_error()
        update_login_button(loading=True)
        
        # 1. 本地验证（Resend 验证码检查）
        result = await auth_manager.verify_code(email, code)
        
        if result.success:
            # 2. 服务器登录（换取 JWT Token）
            from api import api
            
            # 在线程池中执行同步请求，避免阻塞
            loop = asyncio.get_running_loop()
            login_data = await loop.run_in_executor(
                None, 
                lambda: api.login_sync(result.user_id, result.email)
            )
            
            if login_data and login_data.get("token"):
                token = login_data["token"]
                user_number = login_data.get("user_number", 0)
                
                # 保存 Token 和 ID 到本地存储
                try:
                    page.client_storage.set("jwt_token", token)
                    page.client_storage.set("user_number", user_number)
                except Exception as e:
                    print(f"Failed to save token: {e}")
                
                # 登录成功
                on_login_success()
            else:
                update_login_button(loading=False)
                show_error("服务器连接失败，请重试")
        else:
            update_login_button(loading=False)
            show_error(result.error or "验证失败，请检查验证码")
    
    def on_send_click(e):
        """发送按钮点击"""
        if not state["send_loading"] and not state["send_disabled"]:
            asyncio.create_task(do_send_code())
    
    def on_login_click(e):
        """登录按钮点击"""
        # 🔧 只有验证码输入完整（6位）且不在加载中时才允许点击
        code = code_field.value.strip()
        if len(code) == 6 and not state["login_loading"]:
            asyncio.create_task(do_verify_code())
    
    # ========== 按钮组件 ==========
    
    send_button = ft.Container(
        content=send_button_content,
        bgcolor=Theme.ACCENT,
        border_radius=BorderRadius.MD,
        width=110,  # 🔧 增加宽度以容纳"发送验证码"文字
        height=56,  # 🔧 统一高度与邮箱输入框一致
        alignment=ft.Alignment(0, 0),
        on_click=on_send_click,
        ink=True,
    )

    login_button = ft.Container(
        content=login_button_content,
        bgcolor=Theme.BG_ELEVATED,  # 🔧 初始状态为灰色
        border_radius=BorderRadius.MD,
        padding=ft.Padding(0, Spacing.LG, 0, Spacing.LG),
        alignment=ft.Alignment(0, 0),
        visible=True,  # 🔧 始终显示登录按钮
        opacity=0.5,  # 🔧 初始半透明（禁用状态）
        on_click=on_login_click,
        ink=True,
    )
    
    # ========== 页面布局 ==========
    return ft.Container(
        content=ft.Column([
            spacer(80),
            
            # Logo 区域
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(
                            src="/kaka02.png", # 替换为新 Logo
                            width=100,
                            height=100,
                            fit="contain",
                            error_content=ft.Text("🐷", size=64),
                        ),
                        width=100,
                        height=100,
                        border_radius=20, # 图片圆角
                        bgcolor=Theme.BG_CARD,
                        alignment=ft.Alignment(0, 0),
                    ),
                    spacer(Spacing.MD),
                    ft.Text(
                        "咔咔记账",
                        size=FontSize.TITLE,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "轻松管理你的投资",
                        size=FontSize.LG,
                        color=Theme.TEXT_SECONDARY,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
            ),
            
            spacer(50),
            
            # 表单区域
            ft.Container(
                content=ft.Column([
                    # 邮箱 + 发送按钮
                    ft.Row([
                        email_field,
                        ft.Container(width=10),
                        send_button
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),

                    spacer(Spacing.MD),

                    # 验证码（宽度与登录按钮一致，不需要在Row中）
                    code_field,
                    
                    # 错误提示
                    error_text,
                    
                    spacer(Spacing.LG),
                    
                    # 登录按钮
                    login_button,
                ]),
                padding=ft.Padding(Spacing.XL, 0, Spacing.XL, 0),
            ),
            
            ft.Container(expand=True),
            
            # 底部说明
            ft.Container(
                content=ft.Text(
                    "登录即表示同意服务条款和隐私政策",
                    size=FontSize.SM,
                    color=Theme.TEXT_TERTIARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.Padding(0, 0, 0, Spacing.XXL),
                alignment=ft.Alignment(0, 0),
            ),
        ]),
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )

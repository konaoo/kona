"""
Portfolio App - 深色主题版 v5
重构版 - 模块化架构 + 登录认证 + 优化加载体验
"""
import flet as ft
import threading
import asyncio

from config import Theme, Window, BREVO_API_KEY, BREVO_SENDER_EMAIL
from state import AppState
from api import api
from cache import cache
from components import loading_indicator, spacer
from error_handler import setup_global_exception_handler
from data_manager import data_manager

from pages.home import build_home_page
from pages.invest import (
    build_invest_page, build_category_tabs,
    build_portfolio_header, build_portfolio_card
)
from pages.analysis import build_analysis_page
from pages.news import build_news_page
from pages.profile import build_profile_page
from pages.detail import build_detail_page
from pages.login import build_login_page
from pages.edit_profile import build_edit_profile_page
from pages.add_asset import build_add_asset_page

from auth.manager import auth_manager
from auth.brevo_auth import BrevoAuthProvider

# 设置全局异常处理
setup_global_exception_handler()


def main(page: ft.Page):
    """应用入口"""
    # 页面配置
    page.title = "咔咔记账"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = Theme.BG_PRIMARY
    page.padding = 0
    page.window.width = Window.WIDTH
    page.window.height = Window.HEIGHT
    
    # ============================================================
    # 认证初始化
    # ============================================================
    
    # 使用 Brevo 邮件服务（免费300封/天，支持任意邮箱）
    if BREVO_API_KEY and BREVO_SENDER_EMAIL:
        brevo_provider = BrevoAuthProvider(BREVO_API_KEY, BREVO_SENDER_EMAIL)
        auth_manager.set_provider(brevo_provider)
    
    # 主容器
    root_container = ft.Container(expand=True)
    
    # ============================================================
    # 导航栏初始化（先创建，后面再控制显示）
    # ============================================================
    
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="首页"),
            ft.NavigationBarDestination(icon=ft.Icons.BUSINESS_CENTER_OUTLINED, selected_icon=ft.Icons.BUSINESS_CENTER, label="投资"),
            ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART_OUTLINED, selected_icon=ft.Icons.INSERT_CHART, label="分析"),
            ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, selected_icon=ft.Icons.FLASH_ON, label="快讯"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, selected_icon=ft.Icons.PERSON, label="我的"),
        ],
        bgcolor=Theme.NAV_BG,
        selected_index=0,
        indicator_color=Theme.ACCENT,
        elevation=0,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        visible=False,  # 初始隐藏
    )
    
    page.add(root_container)
    
    # ============================================================
    # 主应用逻辑
    # ============================================================
    
    def show_main_app():
        """显示主应用"""
        # 初始化状态
        state = AppState(page)

        # 设置 DataManager 的 state 引用
        data_manager.set_state(state)

        # 🔧 获取实时汇率（后台执行，不阻塞 UI）
        def load_exchange_rates():
            try:
                rates = api.get_exchange_rates_sync()
                state.update_exchange_rates(rates)
                print(f"✅ 汇率更新成功: USD={rates.get('USD')}, HKD={rates.get('HKD')}")
            except Exception as e:
                print(f"⚠️ 汇率获取失败，使用默认汇率: {e}")

        threading.Thread(target=load_exchange_rates, daemon=True).start()

        # 当前页面索引（用于防止异步回调覆盖错误页面）
        current_page_index = [0]  # 使用列表来避免 nonlocal 问题

        # 🚀 登录后立即预加载所有数据（后台执行，不阻塞 UI）
        asyncio.create_task(data_manager.preload_all())

        # 🔄 启动自动刷新（每 30 秒）
        asyncio.create_task(data_manager.start_auto_refresh(interval=30))
        
        # 共享 UI 容器
        body = ft.Container(expand=True)
        portfolio_container = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=8)
        category_row = ft.Row(spacing=8)
        
        # ============================================================
        # 导航逻辑
        # ============================================================
        
        def navigate_to(page_name: str):
            """导航到子页面"""
            state.push_page(page_name)
            page.navigation_bar.visible = False
            page.floating_action_button = None # 清除首页 FAB
            
            if page_name == "edit_profile":
                body.content = build_edit_profile_page(
                    state=state,
                    on_back=lambda _: go_back()
                )
            elif page_name == "add_asset":
                body.content = build_add_asset_page(
                    state=state,
                    on_back=lambda _: go_back(),
                    on_refresh=refresh_home_data
                )
            else:
                body.content = build_detail_page(
                    state=state,
                    title=_get_detail_title(page_name),
                    page_type=page_name,
                    on_back=lambda _: go_back()
                )
            page.update()
        
        def _get_detail_title(page_name: str) -> str:
            """获取详情页标题"""
            titles = {
                "cash_detail": "现金资产",
                "other_detail": "其他资产",
                "liability_detail": "我的负债",
            }
            return titles.get(page_name, "详情")
        
        def go_back():
            """返回上一页"""
            state.pop_page()
            page.navigation_bar.visible = True
            switch_page(0)
        
        def switch_page(index: int):
            """切换底部 Tab 页面"""
            current_page_index[0] = index
            page.navigation_bar.selected_index = index
            
            # 清除之前的 FAB (如果在首页会由 build_home_page 重新设置)
            page.floating_action_button = None
            
            if index == 0:
                body.content = build_home_page(
                    state=state,
                    on_navigate=navigate_to,
                    on_switch_tab=switch_page,
                    on_refresh=refresh_home_data
                )
                refresh_home_data()
            elif index == 1:
                body.content = build_invest_page(
                    state=state,
                    portfolio_container=portfolio_container,
                    category_row=category_row,
                    on_category_change=on_category_click
                )
                load_portfolio()
            elif index == 2:
                body.content = build_analysis_page(state)
            elif index == 3:
                body.content = build_news_page(state)
            elif index == 4:
                body.content = build_profile_page(state, on_logout=page.on_logout)
            
            page.update()
        
        def on_nav_change(e):
            """底部导航栏切换"""
            switch_page(e.control.selected_index)
        
        # ============================================================
        # 数据加载
        # ============================================================
        
        def refresh_home_data():
            """刷新首页数据"""
            def do_refresh():
                try:
                    # 并行获取各项资产数据 (同步调用)
                    cash_list = api.get_cash_assets_sync()
                    other_list = api.get_other_assets_sync()
                    liab_list = api.get_liabilities_sync()
                    portfolio, prices = cache.get_portfolio_sync() 
                    
                    # 计算总额
                    total_cash = sum(float(x['amount']) for x in cash_list)
                    total_other = sum(float(x['amount']) for x in other_list)
                    total_liab = sum(float(x['amount']) for x in liab_list)
                    
                    # 计算投资总额
                    total_invest = 0
                    for item in portfolio:
                        code = item['code']
                        qty = float(item['qty'])
                        cost = float(item['price'])
                        pi = prices.get(code, {})
                        # 优先使用当前价，否则昨日收盘价，否则成本价
                        cp = pi.get('price', 0) or pi.get('yclose', cost) or cost
                        total_invest += cp * qty
                    
                    # 总资产 = 资产总和 - 负债
                    total_asset = total_cash + total_invest + total_other - total_liab
                    
                    # 更新状态
                    state.update_home_data(
                        total=total_asset,
                        cash=total_cash,
                        invest=total_invest,
                        other=total_other
                    )
                    
                    # 检查是否仍在首页
                    if current_page_index[0] != 0:
                        return
                    
                    # 重建首页以更新数据
                    body.content = build_home_page(
                        state=state,
                        on_navigate=navigate_to,
                        on_switch_tab=switch_page,
                        on_refresh=refresh_home_data
                    )
                    page.update()
                except Exception as e:
                    print(f"Error refreshing home data: {e}")
            
            threading.Thread(target=do_refresh, daemon=True).start()
        
        def load_portfolio(force_refresh: bool = False):
            """加载投资组合"""
            def do_load():
                # 检查是否仍在投资页面
                if current_page_index[0] != 1:
                    return

                # 使用缓存
                if state.portfolio_loaded and not force_refresh:
                    render_portfolio()
                    return

                # ✅ 去掉 loading，立即显示空列表或骨架
                # 不再显示 loading_indicator，直接渲染占位符
                render_portfolio()  # 先显示空状态或已有数据

                # 使用缓存获取数据
                portfolio, prices = cache.get_portfolio_sync(force_refresh)

                # 再次检查是否仍在投资页面
                if current_page_index[0] != 1:
                    return

                if portfolio:
                    state.update_portfolio(portfolio, prices)

                    # 重建投资页面以更新汇总数据
                    body.content = build_invest_page(
                        state=state,
                        portfolio_container=portfolio_container,
                        category_row=category_row,
                        on_category_change=on_category_click
                    )

                render_portfolio()

            threading.Thread(target=do_load, daemon=True).start()
        
        def render_portfolio():
            """渲染持仓列表"""
            portfolio_container.controls.clear()
            
            # 分类标签
            build_category_tabs(state, category_row, on_category_click)
            portfolio_container.controls.append(
                ft.Container(content=category_row, padding=ft.Padding(20, 0, 20, 8))
            )
            
            # 过滤数据
            filtered = state.portfolio_data
            if state.current_category != "all":
                filtered = [
                    item for item in state.portfolio_data 
                    if state.get_market_type(item['code']) == state.current_category
                ]
            
            if not filtered:
                from components import empty_state
                portfolio_container.controls.append(
                    empty_state(ft.Icons.BUSINESS_CENTER, "暂无持仓")
                )
            else:
                portfolio_container.controls.append(build_portfolio_header())
                for item in filtered:
                    price_info = state.prices.get(item['code'], {})
                    portfolio_container.controls.append(
                        build_portfolio_card(item, price_info, state)
                    )
            
            page.update()
        
        def on_category_click(category: str):
            """分类标签点击"""
            state.current_category = category
            render_portfolio()
        
        # ============================================================
        # 启动主应用
        # ============================================================
        
        page.navigation_bar.on_change = on_nav_change
        page.navigation_bar.visible = True
        root_container.content = body
        switch_page(0)
        page.update()
    
    # ============================================================
    # 登录页面
    # ============================================================
    
    def show_login():
        """显示登录页面"""
        page.navigation_bar.visible = False
        root_container.content = build_login_page(
            page=page,
            on_login_success=on_login_success
        )
        page.update()
    
    def on_login_success():
        """登录成功回调"""
        show_main_app()
    
    def on_logout():
        """退出登录回调"""
        from api import api
        api.clear_token()  # 清除 API token
        try:
            page.client_storage.remove("jwt_token")
        except:
            pass
        show_login()
    
    # 保存到全局，供 profile 页面使用
    page.on_logout = on_logout
    
    # ============================================================
    # 启动：检查登录状态
    # ============================================================
    
    # 尝试从本地存储恢复 JWT Token
    try:
        stored_token = page.client_storage.get("jwt_token")
        if stored_token:
            api.set_token(stored_token)
            # 如果 auth_manager 没登录但有 token (意外情况)，我们也手动设置 auth_manager 状态
            # 但 auth_manager 逻辑比较复杂，我们主要依赖 api token 即可
            # 不过为了保持一致性，如果 auth_manager 没登录，我们可能需要重新登录
            # 简化逻辑：只要有 token，就认为是登录状态
    except Exception as e:
        print(f"Failed to load token: {e}")
    
    # 检查是否已登录 (要求: auth_manager 认证过 且 api 有 token)
    # 如果缺少其一，都视为未登录，重新走流程
    if auth_manager.is_logged_in and api._token:
        # 已登录，显示主应用
        show_main_app()
    else:
        # 未登录，显示登录页面
        show_login()


if __name__ == "__main__":
    ft.app(target=main)

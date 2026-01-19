"""
快讯页面 - 财经新闻
优化版：使用全局缓存，避免每次切换都重新加载
"""
import flet as ft

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from cache import cache
from components import loading_indicator, empty_state, error_state, simple_header


def build_news_page(state: AppState) -> ft.Container:
    """构建快讯页面"""
    
    news_list = ft.ListView(expand=True, spacing=Spacing.SM, padding=ft.Padding(Spacing.XL, 0, Spacing.XL, 0))
    
    def render_news(items):
        """渲染快讯列表"""
        news_list.controls.clear()
        
        if not items:
            news_list.controls.append(empty_state(ft.Icons.ARTICLE, "暂无快讯"))
        else:
            for item in items[:20]:
                content = item.get('content', '') or item.get('title', '')
                time_str = item.get('time', '')
                news_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(content, size=FontSize.LG, color=Theme.TEXT_PRIMARY, max_lines=3),
                            ft.Text(time_str, size=FontSize.MD, color=Theme.TEXT_TERTIARY),
                        ], spacing=Spacing.SM),
                        padding=Spacing.LG,
                        bgcolor=Theme.BG_CARD,
                        border_radius=BorderRadius.LG,
                    )
                )
        
        try:
            state.page.update()
        except:
            pass
    
    def load_news():
        """加载快讯"""
        def on_data(items):
            if items is None:
                news_list.controls.clear()
                news_list.controls.append(error_state("加载失败"))
                try:
                    state.page.update()
                except:
                    pass
            else:
                render_news(items)
        
        # 先检查是否有缓存
        cached = cache.get("news")
        if cached:
            # 有缓存，立即显示
            render_news(cached)
            # 后台刷新
            cache.get_news(callback=render_news)
        else:
            # 无缓存，显示加载中
            news_list.controls.clear()
            news_list.controls.append(loading_indicator())
            try:
                state.page.update()
            except:
                pass
            
            # 加载数据
            cache.get_news(callback=on_data)
    
    load_news()
    
    return ft.Container(
        content=ft.Column([
            simple_header("快讯"),
            news_list,
        ]),
        bgcolor=Theme.BG_PRIMARY,
        expand=True
    )

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

    news_list = ft.ListView(expand=True, spacing=Spacing.MD, padding=ft.Padding(Spacing.XL, 0, Spacing.XL, Spacing.XL))

    def render_news(items):
        """渲染快讯列表"""
        news_list.controls.clear()

        if not items:
            news_list.controls.append(empty_state(ft.Icons.ARTICLE, "暂无快讯"))
        else:
            for item in items[:20]:
                content = item.get('content', '') or item.get('title', '')
                time_str = item.get('time', '')

                # 🎨 新布局：日期在卡片外 + 左侧辅助线 + 卡片描边
                news_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            # 卡片内容 + 左侧辅助线
                            ft.Container(
                                content=ft.Row([
                                    # 左侧辅助线
                                    ft.Container(
                                        width=3,
                                        bgcolor=Theme.ACCENT,
                                        border_radius=ft.border_radius.all(2),
                                    ),
                                    # 内容区域
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text(
                                                content,
                                                size=FontSize.BASE,
                                                color=Theme.TEXT_PRIMARY,
                                                max_lines=4,
                                                overflow=ft.TextOverflow.ELLIPSIS
                                            ),
                                            spacer(4),
                                            # 🔧 日期移到左下角
                                            ft.Text(time_str, size=FontSize.XS, color=Theme.TEXT_TERTIARY),
                                        ], spacing=0),
                                        padding=ft.Padding(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM),
                                        expand=True,
                                    ),
                                ], spacing=0),
                                # 卡片描边
                                bgcolor=Theme.BG_CARD,
                                border_radius=BorderRadius.MD,
                                border=ft.border.all(1, Theme.BORDER),
                            ),
                        ], spacing=0),
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
    
    # 🎯 自定义标题："市场快讯LIVE" + 标志
    custom_header = ft.Container(
        content=ft.Row([
            ft.Text("市场快讯", size=FontSize.XXL, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY),
            ft.Container(
                content=ft.Text("LIVE", size=FontSize.SM, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY),
                bgcolor=Theme.DANGER,
                padding=ft.Padding(6, 2, 6, 2),
                border_radius=BorderRadius.SM,
            ),
        ], spacing=8),
        padding=ft.Padding(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.MD),  # 🔧 减少顶部间距
    )

    return ft.Container(
        content=ft.Column([
            custom_header,
            news_list,
        ], spacing=0),
        bgcolor=Theme.BG_PRIMARY,
        expand=True
    )

"""
分析页面 - 盈亏分析
优化版本 v5: 使用全局缓存，优化加载速度，彻底解决卡顿问题
"""
import flet as ft
import threading
from typing import Dict, List, Any
from datetime import datetime
import calendar

from config import Theme, Spacing, FontSize, BorderRadius
from state import AppState
from components import horizontal_padding, spacer
from cache import cache


# ============================================================
# 休市判断
# ============================================================

def is_market_closed() -> bool:
    """
    判断当前是否休市
    休市条件：
    1. 周末（周六、周日）
    2. 非交易时间（9:30前或15:00后）
    """
    now = datetime.now()
    
    # 周末休市
    if now.weekday() >= 5:  # 5=周六, 6=周日
        return True
    
    # 交易时间判断 (9:30 - 15:00)
    current_time = now.hour * 100 + now.minute
    if current_time < 930 or current_time >= 1500:
        return True
    
    return False


# ============================================================
# 默认空数据（作为无数据时的显示）
# ============================================================

def get_empty_overview_data() -> Dict[str, Dict]:
    return {
        "day": {"label": "当日", "pnl": 0, "pnl_rate": 0},
        "month": {"label": "本月", "pnl": 0, "pnl_rate": 0},
        "year": {"label": "今年", "pnl": 0, "pnl_rate": 0},
        "all": {"label": "全部", "pnl": 0, "pnl_rate": 0},
    }


def get_real_overview_data() -> Dict[str, Dict]:
    """从缓存/API 获取真实的盈亏概览数据"""
    try:
        data = cache.get_analysis_overview()
        if data:
            # 转换为前端需要的格式
            labels = {"day": "当日", "month": "本月", "year": "今年", "all": "全部"}
            result = {}
            for period in ["day", "month", "year", "all"]:
                if period in data:
                    result[period] = {
                        "label": labels.get(period, period),
                        "pnl": data[period].get("pnl", 0),
                        "pnl_rate": data[period].get("pnl_rate", 0)
                    }
            if result:
                # 补全缺失的周期
                empty = get_empty_overview_data()
                for key in empty:
                    if key not in result:
                        result[key] = empty[key]
                return result
    except Exception as e:
        print(f"Failed to get overview data: {e}")
    return get_empty_overview_data()


def get_empty_calendar_data(time_type: str) -> Dict:
    now = datetime.now()
    title = f"{now.month}月累计" if time_type == "day" else (f"{now.year}年累计" if time_type == "month" else "总累计")
    return {"items": [], "total_pnl": 0, "total_rate": 0, "title": title}


def get_real_calendar_data(time_type: str) -> Dict:
    """从缓存/API 获取真实的收益日历数据"""
    try:
        data = cache.get_analysis_calendar(time_type)
        if data and data.get("items"):
            return data
    except Exception as e:
        print(f"Failed to get calendar data: {e}")
    return get_empty_calendar_data(time_type)


def get_empty_rank_data(market: str = "all") -> Dict[str, List[Dict]]:
    return {"gain": [], "loss": []}


def get_real_rank_data(market: str = "all") -> Dict[str, List[Dict]]:
    """从缓存/API 获取真实的盈亏排行数据"""
    try:
        data = cache.get_analysis_rank(market)
        if data and (data.get("gain") or data.get("loss")):
            return data
    except Exception as e:
        print(f"Failed to get rank data: {e}")
    return get_empty_rank_data(market)


# ============================================================
# 页面构建
# ============================================================

def build_analysis_page(state: AppState) -> ft.Container:
    # ========== 状态 ==========
    current_period = "day"
    calendar_time_type = "day"
    rank_type = "gain"
    is_mounted = False

    # 🔧 优先使用缓存数据，如果缓存不存在才使用空数据
    overview_data = get_real_overview_data()
    calendar_data = get_real_calendar_data("day")
    rank_data = get_real_rank_data("all")
    
    # ============================================================
    # 1. 盈亏概览
    # ============================================================
    def build_overview() -> ft.Container:
        nonlocal current_period
        data = overview_data.get(current_period, overview_data["day"])
        pnl = data["pnl"]
        pnl_rate = data["pnl_rate"]
        
        # 休市判断
        market_closed = is_market_closed()
        show_day_pnl = not (current_period == "day" and market_closed)
        
        pnl_color = Theme.DANGER if pnl >= 0 else Theme.SUCCESS
        sign = "+" if pnl >= 0 else ""
        
        labels = {"day": "今日盈亏", "month": "本月盈亏", "year": "今年盈亏", "all": "累计盈亏"}
        display_label = labels.get(current_period, "盈亏")
        
        if show_day_pnl:
            pnl_text = f"{sign}¥{pnl:,.2f}"
            rate_text = f"收益率 {sign}{pnl_rate:.2f}%"
        else:
            pnl_text = "¥0.00"
            rate_text = "收益率 0.00%"
            pnl_color = Theme.TEXT_TERTIARY
        
        period_tabs = ft.Row(spacing=0, alignment=ft.MainAxisAlignment.CENTER)
        for key in ["day", "month", "year", "all"]:
            item = overview_data[key]
            is_selected = (key == current_period)
            period_tabs.controls.append(
                ft.Container(
                    content=ft.Text(
                        item["label"],
                        size=FontSize.BASE,
                        color=Theme.TEXT_PRIMARY if is_selected else Theme.TEXT_TERTIARY,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL
                    ),
                    padding=ft.Padding(18, 10, 18, 10),
                    bgcolor=Theme.ACCENT if is_selected else "transparent",
                    border_radius=20,
                    on_click=lambda _, k=key: on_period_change(k),
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(display_label, size=FontSize.BASE, color=Theme.TEXT_SECONDARY),
                spacer(4),
                ft.Text(pnl_text, size=32, weight=ft.FontWeight.BOLD, color=pnl_color),
                spacer(4),
                ft.Row([
                    ft.Icon(ft.Icons.TRENDING_UP if pnl >= 0 and show_day_pnl else ft.Icons.ACCESS_TIME, size=16, color=pnl_color),
                    ft.Text(rate_text, size=FontSize.BASE, color=pnl_color),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                spacer(Spacing.MD),
                period_tabs,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.LG),
            border_radius=BorderRadius.XL,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=Theme.CARD_GRADIENT
            ),
        )
    
    def on_period_change(period: str):
        nonlocal current_period
        current_period = period
        refresh_page()
    
    # ============================================================
    # 2. 收益日历
    # ============================================================
    def build_calendar() -> ft.Column:
        nonlocal calendar_time_type
        # 使用闭包变量，不调用外部API
        data = calendar_data
        
        items = data["items"]
        total_pnl = data["total_pnl"]
        total_rate = data["total_rate"]
        title = data["title"]
        
        total_color = Theme.DANGER if total_pnl >= 0 else Theme.SUCCESS
        total_sign = "+" if total_pnl >= 0 else ""
        
        time_toggles = ft.Row([
            _build_toggle("日", calendar_time_type == "day", lambda _, t="day": on_calendar_time_change(t)),
            _build_toggle("月", calendar_time_type == "month", lambda _, t="month": on_calendar_time_change(t)),
            _build_toggle("年", calendar_time_type == "year", lambda _, t="year": on_calendar_time_change(t)),
        ], spacing=0)
        
        grid_items = []
        for item in items:
            pnl = item["pnl"]
            bg_color = Theme.DANGER if pnl >= 0 else Theme.SUCCESS
            max_val = 4000 if calendar_time_type == "day" else (20000 if calendar_time_type == "month" else 80000)
            opacity = min(abs(pnl) / max_val, 1.0) * 0.65 + 0.35
            
            if abs(pnl) >= 10000:
                display_pnl = f"{pnl/10000:+.1f}w"
            elif abs(pnl) >= 1000:
                display_pnl = f"{pnl/1000:+.1f}k"
            else:
                display_pnl = f"{int(pnl):+d}"
            
            grid_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(item["label"], size=11, color=Theme.TEXT_PRIMARY, weight=ft.FontWeight.W_600),
                        ft.Text(display_pnl, size=10, color="white90", weight=ft.FontWeight.W_500),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    bgcolor=bg_color,
                    opacity=opacity,
                    border_radius=BorderRadius.MD,
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(4, 6, 4, 6),
                )
            )
        
        if calendar_time_type == "day":
            runs_count, max_extent = 6, 55
        elif calendar_time_type == "month":
            runs_count, max_extent = 4, 80
        else:
            runs_count, max_extent = 5, 68
        
        return ft.Column([
            ft.Row([
                ft.Text("收益日历", size=FontSize.XL, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Container(content=time_toggles, bgcolor=Theme.BG_CARD, border_radius=8, padding=2),
            ]),
            spacer(Spacing.MD),
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(title, size=FontSize.SM, color=Theme.TEXT_TERTIARY),
                        ft.Text(f"{total_sign}¥{total_pnl:,.0f}", size=FontSize.XXL, color=total_color, weight=ft.FontWeight.BOLD),
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.Column([
                        ft.Text("收益率", size=FontSize.SM, color=Theme.TEXT_TERTIARY),
                        ft.Text(f"{total_sign}{total_rate:.2f}%", size=FontSize.XL, color=total_color, weight=ft.FontWeight.BOLD),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                ]),
                bgcolor=Theme.BG_CARD,
                padding=Spacing.LG,
                border_radius=BorderRadius.LG,
            ),
            spacer(Spacing.MD),
            ft.GridView(
                runs_count=runs_count,
                max_extent=max_extent,
                spacing=6,
                run_spacing=6,
                controls=grid_items,
                child_aspect_ratio=0.9,
            )
        ])
    
    def _build_toggle(text: str, is_selected: bool, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Text(text, size=FontSize.BASE, color=Theme.TEXT_PRIMARY if is_selected else Theme.TEXT_SECONDARY),
            padding=ft.Padding(12, 6, 12, 6),
            bgcolor=Theme.ACCENT if is_selected else "transparent",
            border_radius=6,
            on_click=on_click,
        )
    
    def on_calendar_time_change(time_type: str):
        nonlocal calendar_time_type
        calendar_time_type = time_type
        # 切换类型时，重新触发后台加载以获取新数据
        threading.Thread(target=load_real_data, daemon=True).start()
        refresh_page()
    
    # ============================================================
    # 3. 盈亏排行（主页部分）
    # ============================================================
    def build_rank() -> ft.Column:
        nonlocal rank_type
        # 使用闭包变量，不调用外部API
        data = rank_data
        items = data.get(rank_type, [])[:5]
        
        rank_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
        
        rank_items = []
        for idx, item in enumerate(items):
            pnl = item["pnl"]
            pnl_rate = item["pnl_rate"]
            color = Theme.DANGER if pnl >= 0 else Theme.SUCCESS
            
            if idx < 3:
                rank_widget = ft.Container(
                    content=ft.Text(str(idx + 1), size=12, color="white", weight=ft.FontWeight.BOLD),
                    width=24, height=24,
                    bgcolor=rank_colors[idx],
                    border_radius=12,
                    alignment=ft.Alignment(0, 0),
                )
            else:
                rank_widget = ft.Container(
                    content=ft.Text(str(idx + 1), size=FontSize.LG, color=Theme.TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                    width=24,
                    alignment=ft.Alignment(0, 0)
                )
            
            rank_items.append(
                ft.Container(
                    content=ft.Row([
                        rank_widget,
                        ft.Container(width=Spacing.SM),
                        ft.Text(item["name"], size=FontSize.LG, color=Theme.TEXT_PRIMARY, weight=ft.FontWeight.W_500, expand=True),
                        ft.Column([
                            ft.Text(f"{'+'if pnl >= 0 else ''}¥{pnl:,.0f}", size=FontSize.LG, color=color, weight=ft.FontWeight.W_600),
                            ft.Text(f"{'+' if pnl_rate >= 0 else ''}{pnl_rate:.2f}%", size=FontSize.MD, color=color),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ]),
                    padding=ft.Padding(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD),
                    bgcolor=Theme.BG_CARD,
                    border_radius=BorderRadius.LG,
                )
            )
        
        if not rank_items:
            rank_items.append(
                ft.Container(
                    content=ft.Text("暂无数据", size=FontSize.LG, color=Theme.TEXT_TERTIARY),
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                )
            )
        
        def build_tab(text: str, tab_type: str):
            is_selected = (tab_type == rank_type)
            return ft.Container(
                content=ft.Text(
                    text,
                    size=FontSize.LG,
                    weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                    color=Theme.TEXT_PRIMARY if is_selected else Theme.TEXT_TERTIARY
                ),
                padding=ft.Padding(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM),
                bgcolor=Theme.ACCENT if is_selected else "transparent",
                border_radius=BorderRadius.MD,
                on_click=lambda _, t=tab_type: on_rank_type_change(t)
            )
        
        return ft.Column([
            ft.Text("盈亏排行", size=FontSize.XL, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY),
            spacer(Spacing.MD),
            ft.Row([
                build_tab("盈利榜", "gain"),
                ft.Container(width=Spacing.SM),
                build_tab("亏损榜", "loss"),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text("查看全部 >", size=FontSize.BASE, color=Theme.ACCENT_LIGHT),
                    on_click=lambda _: show_full_rank_page(),
                ),
            ]),
            spacer(Spacing.MD),
            ft.Column(rank_items, spacing=Spacing.SM)
        ])
    
    def on_rank_type_change(new_type: str):
        nonlocal rank_type
        rank_type = new_type
        refresh_page()
    
    # ============================================================
    # 全屏排行榜页面
    # ============================================================
    def show_full_rank_page():
        """显示全屏排行榜页面"""
        full_rank_type = rank_type
        full_rank_market = "all"
        
        rank_list_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        
        def build_rank_list(r_type: str, market: str):
            data = get_real_rank_data(market)
            items = data.get(r_type, [])
            
            rank_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
            rank_items = []
            
            for idx, item in enumerate(items):
                pnl = item["pnl"]
                pnl_rate = item["pnl_rate"]
                code = item["code"]
                color = Theme.DANGER if pnl >= 0 else Theme.SUCCESS
                
                # 前三名用数字圆形图标
                if idx < 3:
                    rank_widget = ft.Container(
                        content=ft.Text(str(idx + 1), size=12, color="white", weight=ft.FontWeight.BOLD),
                        width=26, height=26,
                        bgcolor=rank_colors[idx],
                        border_radius=13,
                        alignment=ft.Alignment(0, 0),
                    )
                else:
                    rank_widget = ft.Container(
                        content=ft.Text(str(idx + 1), size=FontSize.LG, color=Theme.TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                        width=26,
                        alignment=ft.Alignment(0, 0)
                    )
                
                rank_items.append(
                    ft.Container(
                        content=ft.Row([
                            rank_widget,
                            ft.Container(width=Spacing.SM),
                            # 名称和代码
                            ft.Column([
                                ft.Text(item["name"], size=FontSize.LG, color=Theme.TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                                ft.Text(code, size=FontSize.SM, color=Theme.TEXT_TERTIARY),
                            ], spacing=2, expand=True),
                            # 盈亏金额和收益率
                            ft.Column([
                                ft.Text(f"{'+'if pnl >= 0 else ''}¥{pnl:,.0f}", size=FontSize.LG, color=color, weight=ft.FontWeight.W_600),
                                ft.Text(f"{'+' if pnl_rate >= 0 else ''}{pnl_rate:.2f}%", size=FontSize.MD, color=color),
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                        ]),
                        padding=ft.Padding(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD),
                        bgcolor=Theme.BG_CARD,
                        border_radius=BorderRadius.LG,
                    )
                )
            
            if not rank_items:
                rank_items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.INBOX, size=48, color=Theme.TEXT_TERTIARY),
                            ft.Text("暂无数据", size=FontSize.LG, color=Theme.TEXT_TERTIARY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=Spacing.MD),
                        padding=60,
                        alignment=ft.Alignment(0, 0),
                    )
                )
            
            rank_list_container.controls = rank_items
            try:
                if state.page and state.page.overlay:
                    state.page.update()
            except:
                pass
        
        def on_full_rank_type_change(t: str):
            nonlocal full_rank_type
            full_rank_type = t
            update_tabs_and_list()
        
        def on_full_rank_market_change(m: str):
            nonlocal full_rank_market
            full_rank_market = m
            update_tabs_and_list()
        
        def update_tabs_and_list():
            # 更新 Tab 状态
            for i, t in enumerate(["gain", "loss"]):
                is_sel = (t == full_rank_type)
                type_tabs.controls[i * 2].bgcolor = Theme.ACCENT if is_sel else "transparent"
                type_tabs.controls[i * 2].content.color = Theme.TEXT_PRIMARY if is_sel else Theme.TEXT_TERTIARY
                type_tabs.controls[i * 2].content.weight = ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL
            
            # 更新市场按钮状态
            markets = ["all", "a", "us", "hk", "fund"]
            for i, m in enumerate(markets):
                is_sel = (m == full_rank_market)
                market_row.controls[i].bgcolor = Theme.ACCENT if is_sel else Theme.BG_ELEVATED
                market_row.controls[i].content.color = Theme.TEXT_PRIMARY if is_sel else Theme.TEXT_SECONDARY
            
            build_rank_list(full_rank_type, full_rank_market)
        
        def close_full_page(_=None):
            state.page.overlay.remove(full_page_overlay)
            state.page.update()
        
        def build_type_tab(text: str, t: str):
            is_sel = (t == full_rank_type)
            return ft.Container(
                content=ft.Text(
                    text,
                    size=FontSize.LG,
                    color=Theme.TEXT_PRIMARY if is_sel else Theme.TEXT_TERTIARY,
                    weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL
                ),
                padding=ft.Padding(Spacing.LG, Spacing.SM, Spacing.LG, Spacing.SM),
                bgcolor=Theme.ACCENT if is_sel else "transparent",
                border_radius=BorderRadius.MD,
                on_click=lambda _, t=t: on_full_rank_type_change(t),
            )
        
        def build_market_btn(text: str, m: str):
            is_sel = (m == full_rank_market)
            return ft.Container(
                content=ft.Text(text, size=FontSize.SM, color=Theme.TEXT_PRIMARY if is_sel else Theme.TEXT_SECONDARY),
                padding=ft.Padding(Spacing.MD, 6, Spacing.MD, 6),
                bgcolor=Theme.ACCENT if is_sel else Theme.BG_ELEVATED,
                border_radius=BorderRadius.SM,
                on_click=lambda _, m=m: on_full_rank_market_change(m),
            )
        
        # Tab 行
        type_tabs = ft.Row([
            build_type_tab("盈利榜", "gain"),
            ft.Container(width=Spacing.SM),
            build_type_tab("亏损榜", "loss"),
        ])
        
        # 市场筛选行
        market_row = ft.Row([
            build_market_btn("全部", "all"),
            build_market_btn("A股", "a"),
            build_market_btn("美股", "us"),
            build_market_btn("港股", "hk"),
            build_market_btn("基金", "fund"),
        ], spacing=8)
        
        # 初始加载列表
        build_rank_list(full_rank_type, full_rank_market)
        
        # 全屏页面
        full_page_overlay = ft.Container(
            content=ft.Column([
                # 顶部栏
                ft.Container(
                    content=ft.Row([
                        ft.Text("盈亏排行", size=FontSize.XXL, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color=Theme.TEXT_PRIMARY,
                            icon_size=24,
                            on_click=close_full_page,
                        ),
                    ]),
                    padding=ft.Padding(Spacing.XL, 50, Spacing.MD, Spacing.MD),
                ),
                # Tab 切换
                ft.Container(
                    content=type_tabs,
                    padding=ft.Padding(Spacing.XL, 0, Spacing.XL, Spacing.MD),
                ),
                # 市场筛选
                ft.Container(
                    content=market_row,
                    padding=ft.Padding(Spacing.XL, 0, Spacing.XL, Spacing.MD),
                ),
                # 列表
                ft.Container(
                    content=rank_list_container,
                    padding=ft.Padding(Spacing.XL, 0, Spacing.XL, 0),
                    expand=True,
                ),
            ]),
            bgcolor=Theme.BG_PRIMARY,
            expand=True,
        )
        
        state.page.overlay.append(full_page_overlay)
        state.page.update()
    
    # ============================================================
    # 刷新页面
    # ============================================================
    def refresh_page():
        nonlocal is_mounted
        if is_mounted:
            page_content.controls = build_page_controls()
            try:
                page_content.update()
            except:
                pass
    
    def build_page_controls() -> List:
        return [
            spacer(50),
            horizontal_padding(build_overview()),
            spacer(Spacing.XL),
            horizontal_padding(build_calendar()),
            spacer(Spacing.XL),
            horizontal_padding(build_rank()),
            spacer(60),
        ]
    
    page_content = ft.Column(build_page_controls(), scroll=ft.ScrollMode.AUTO)
    is_mounted = True

    # 🔧 后台静默刷新（只在缓存过期时才会触发）
    def load_real_data():
        nonlocal overview_data, calendar_data, rank_data
        try:
            # 强制刷新缓存（从API获取最新数据）
            # 1. Overview
            real_overview = get_real_overview_data()
            if real_overview and real_overview != overview_data:
                overview_data = real_overview

            # 2. Calendar (Current Type)
            real_calendar = get_real_calendar_data(calendar_time_type)
            if real_calendar and real_calendar != calendar_data:
                calendar_data = real_calendar

            # 3. Rank
            real_rank = get_real_rank_data("all")
            if real_rank and real_rank != rank_data:
                rank_data = real_rank

            # 🔧 只有数据发生变化时才更新UI
            if is_mounted:
                page_content.controls = build_page_controls()
                try:
                    state.page.update()
                except:
                    pass
        except Exception as e:
            print(f"⚠️ 分析页后台刷新失败: {e}")

    # 🔧 后台静默刷新（不阻塞UI显示）
    threading.Thread(target=load_real_data, daemon=True).start()
    
    return ft.Container(
        content=page_content,
        bgcolor=Theme.BG_PRIMARY,
        expand=True,
    )

"""
Pages 模块 - 导出所有页面构建函数
"""
from pages.home import build_home_page
from pages.invest import build_invest_page
from pages.analysis import build_analysis_page
from pages.news import build_news_page
from pages.profile import build_profile_page
from pages.detail import build_detail_page

__all__ = [
    'build_home_page',
    'build_invest_page',
    'build_analysis_page',
    'build_news_page',
    'build_profile_page',
    'build_detail_page',
]

# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent.absolute()
DATABASE_PATH = Path(os.getenv("KONA_DATABASE_PATH", str(BASE_DIR / "portfolio.db")))
BACKUP_CSV_PATH = BASE_DIR / "portfolio.csv"
TRANSACTION_PATH = BASE_DIR / "transactions.csv"

# 服务器配置
HOST = "0.0.0.0"
PORT = 5003
DEBUG = False
APP_VERSION = "v12.0.0"  # 多用户版本

# JWT 认证配置（必须显式配置，缺失即启动失败）
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is required. Please set JWT_SECRET in environment (.env)."
    )
JWT_EXPIRY_HOURS = 24 * 7  # 7 天

# API配置
API_TIMEOUT = 3
RETRY_TIMES = 3
RETRY_DELAY = 2

# HTTP请求头配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

API_HEADERS = {
    "default": {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    },
    "ft": {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    },
    "eastmoney": {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://fund.eastmoney.com/"
    },
    "eastmoney_mobile": {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://fund.eastmoney.com/"
    }
}

# 缓存配置
CACHE_ENABLED = True
CACHE_TTL = 60

# 汇率配置
DEFAULT_FOREX_RATES = {
    "USD": 7.25,
    "HKD": 0.93,
    "CNY": 1.00
}

# 证券代码前缀映射
CODE_PREFIX_MAPPING = {
    "fund": "f_",
    "fund_ft": "ft_",
    "stock_sh": "sh",
    "stock_sz": "sz",
    "stock_bj": "bj",
    "stock_hk": "hk",
    "stock_us": "gb_"
}

# API端点配置
API_ENDPOINTS = {
    "sinajs_stock": "http://hq.sinajs.cn/list",
    "sina_stock": "http://hq.sinajs.cn/list={code}",
    "tencent_stock": "http://qt.gtimg.cn/q={code}",
    "sina_forex": "http://hq.sinajs.cn/list=hf_USDCNY,hf_HKDCNY",
    "sina_search": "http://suggest3.sinajs.cn/suggest/type=11,12,13,14,15&key={query}&name=suggestdata_{timestamp}",
    "eastmoney_stock": "https://push2.eastmoney.com/api/qt/stock/get",
    "eastmoney_fund10": "https://api.fund.10jqka.com/fund?apiversion=2.0",
    "eastmoney_fund_nav": "https://api.fund.10jqka.com/fund?apiversion=1.0",
    "eastmoney_fund_info": "https://fund.10jqka.com/fund?apiversion=1.0",
    "eastmoney_fund_rank": "https://fund.10jqka.com/fund?apiversion=1.0",
    "eastmoney_fund_f10": "https://fundf10.eastmoney.com/F10DataApi/F10DataApi",
    "eastmoney_fund_mobile": "https://fund.eastmoney.com/data/F10DataApi_Type.aspx",
    "tiantian_fund": "https://fundgz.1234567.com.cn/js/{code}.js",
    "markets_ft_index": "https://markets.ft.com/data/tearsheet/summary?sisin={isin}:USD",
    "ft_fund": "https://markets.ft.com/data/equities/tearsheet/summary?s={isin}:USD"
}

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = BASE_DIR / "app.log"

# SMTP 邮件配置（用于验证码）
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "咔咔记账")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() != "false"

# 免验证码登录白名单（逗号分隔邮箱）
LOGIN_BYPASS_EMAILS = [
    e.strip().lower()
    for e in os.getenv("LOGIN_BYPASS_EMAILS", "").split(",")
    if e.strip()
]

# 快照后台任务开关
# 说明：如果你使用 cron 在固定时间触发快照（例如 07:00），建议关闭后台任务。
ENABLE_BACKGROUND_SNAPSHOT = os.getenv("ENABLE_BACKGROUND_SNAPSHOT", "false").lower() == "true"
ENABLE_STARTUP_SNAPSHOT = os.getenv("ENABLE_STARTUP_SNAPSHOT", "false").lower() == "true"

# 证券类型分类
ASSET_TYPES = {
    "stock_cn": {"name": "A股", "prefixes": ["sh", "sz", "bj"]},
    "stock_hk": {"name": "港股", "suffixes": [".HK"]},
    "stock_us": {"name": "美股", "prefixes": ["gb_"]},
    "fund": {"name": "fund", "prefixes": ["f_", "ft_"]}
}

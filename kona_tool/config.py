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
MARKET_HOLIDAY_OVERRIDES_PATH = Path(
    os.getenv(
        "MARKET_HOLIDAY_OVERRIDES_PATH",
        str(BASE_DIR / "market_holidays.json"),
    )
)

# 服务器配置
# 优先读取 KONA_HOST/KONA_PORT，兼容旧变量 HOST/PORT
# 默认改为仅本机回环地址，避免与其他项目冲突
HOST = os.getenv("KONA_HOST", os.getenv("HOST", "127.0.0.1"))
PORT = int(os.getenv("KONA_PORT", os.getenv("PORT", "52345")))
DEBUG = False
APP_VERSION = "v12.0.0"  # 多用户版本

# 客户端 App 更新配置 (Flutter端检查更新使用)
CLIENT_APP_VERSION = os.getenv("CLIENT_APP_VERSION", "1.0.20").strip()
CLIENT_APP_BUILD_NUMBER = int(os.getenv("CLIENT_APP_BUILD_NUMBER", "20"))
CLIENT_APP_RELEASE_NOTES = os.getenv(
    "CLIENT_APP_RELEASE_NOTES",
    "1. 修复网络异常问题\n2. 优化升级流程"
).strip()
CLIENT_APP_DOWNLOAD_URL = os.getenv(
    "CLIENT_APP_DOWNLOAD_URL",
    "https://kaka-wallet-1300924971.cos.ap-beijing.myqcloud.com/app-release.apk"
).strip()
CLIENT_APP_FORCE_UPDATE = os.getenv("CLIENT_APP_FORCE_UPDATE", "false").lower() == "true"

# 新 Web 门户配置（独立 H5）
WEB_APK_DOWNLOAD_URL = os.getenv(
    "WEB_APK_DOWNLOAD_URL",
    "",
).strip()
WEB_APK_FILENAME = os.getenv("WEB_APK_FILENAME", "kaka-latest-release.apk").strip() or "kaka-latest-release.apk"
WEB_APK_LOCAL_PATH = BASE_DIR / "static" / "downloads" / WEB_APK_FILENAME
WEB_PORTAL_TITLE = os.getenv("WEB_PORTAL_TITLE", "Kona Portfolio").strip() or "Kona Portfolio"
WEB_ENABLE_LEGACY_REDIRECT = os.getenv("WEB_ENABLE_LEGACY_REDIRECT", "true").lower() != "false"

# JWT 认证配置（必须显式配置，缺失即启动失败）
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is required. Please set JWT_SECRET in environment (.env)."
    )
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "2"))  # access token 默认 2 小时
AUTH_REFRESH_TOKEN_DAYS = int(os.getenv("AUTH_REFRESH_TOKEN_DAYS", "365"))
AUTH_REFRESH_TOKEN_RETENTION_DAYS = int(os.getenv("AUTH_REFRESH_TOKEN_RETENTION_DAYS", "90"))

# API配置
API_TIMEOUT = 3
RETRY_TIMES = 3
RETRY_DELAY = 2
SOURCE_FAIL_THRESHOLD = int(os.getenv("SOURCE_FAIL_THRESHOLD", "3"))
SOURCE_COOLDOWN_SECONDS = int(os.getenv("SOURCE_COOLDOWN_SECONDS", "45"))
SEARCH_AGGREGATE_TIMEOUT_SECONDS = float(
    os.getenv("SEARCH_AGGREGATE_TIMEOUT_SECONDS", "1.8")
)
SEARCH_SOURCE_TIMEOUT_SECONDS = float(
    os.getenv("SEARCH_SOURCE_TIMEOUT_SECONDS", "1.2")
)

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
CACHE_STALE_TTL = int(os.getenv("CACHE_STALE_TTL", "300"))
ADMIN_READ_CACHE_TTL_SECONDS = int(os.getenv("ADMIN_READ_CACHE_TTL_SECONDS", "120"))

# 行情预取间隔（秒），设为小于 CACHE_TTL 以确保缓存永远不过期
PRELOAD_INTERVAL_SECONDS = int(os.getenv("PRELOAD_INTERVAL_SECONDS", "30"))

# 汇率配置
DEFAULT_FOREX_RATES = {
    "USD": 7.0,
    "HKD": 0.9,
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

# SMTP 邮件配置（用于运维告警等非登录场景）
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "咔咔记账")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() != "false"

# 限流存储后端（生产建议 Redis）
# 本地开发可用 memory://，生产建议：
# RATELIMIT_STORAGE_URL=redis://127.0.0.1:6379/0
RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")

# 运行指标接口鉴权（为空表示不鉴权；生产建议设置）
PRICE_HEALTH_TOKEN = os.getenv("PRICE_HEALTH_TOKEN", "").strip()

# 仅本机开发使用：允许本地回环地址直接访问 /api/admin/*（免登录）
# 生产环境务必保持 false
ALLOW_LOCAL_ADMIN_BYPASS = os.getenv("ALLOW_LOCAL_ADMIN_BYPASS", "false").lower() == "true"

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

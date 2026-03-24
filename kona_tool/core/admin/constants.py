"""
管理后台常量。
"""

from __future__ import annotations

from datetime import timedelta, timezone
from typing import Any, Dict, List


CONFIG_WHITELIST: Dict[str, Dict[str, Any]] = {
    "API_TIMEOUT": {
        "display_name": "接口超时秒数",
        "type": "int",
        "min": 1,
        "max": 30,
        "description": "上游接口超时（秒）",
    },
    "RETRY_TIMES": {
        "display_name": "失败重试次数",
        "type": "int",
        "min": 0,
        "max": 10,
        "description": "请求重试次数",
    },
    "RETRY_DELAY": {
        "display_name": "重试间隔秒数",
        "type": "int",
        "min": 0,
        "max": 10,
        "description": "每次重试等待秒数",
    },
    "CACHE_TTL": {
        "display_name": "缓存有效期",
        "type": "int",
        "min": 0,
        "max": 3600,
        "description": "价格缓存有效时长（秒）",
    },
    "CACHE_STALE_TTL": {
        "display_name": "兜底缓存有效期",
        "type": "int",
        "min": 0,
        "max": 86400,
        "description": "主缓存过期后可用的兜底缓存时长（秒）",
    },
    "SOURCE_FAIL_THRESHOLD": {
        "display_name": "熔断失败阈值",
        "type": "int",
        "min": 1,
        "max": 20,
        "description": "连续失败达到该次数后触发熔断",
    },
    "SOURCE_COOLDOWN_SECONDS": {
        "display_name": "熔断冷却时间",
        "type": "int",
        "min": 1,
        "max": 600,
        "description": "熔断后等待该秒数再尝试恢复",
    },
    "ENABLE_BACKGROUND_SNAPSHOT": {
        "display_name": "启用后台定时快照",
        "type": "bool",
        "description": "是否开启后台定时生成资产快照",
    },
    "ENABLE_STARTUP_SNAPSHOT": {
        "display_name": "启动时自动快照",
        "type": "bool",
        "description": "服务启动后是否立即补一次快照",
    },
    "LOG_LEVEL": {
        "display_name": "日志级别",
        "type": "str",
        "choices": ["DEBUG", "INFO", "WARNING", "ERROR"],
        "description": "系统日志输出级别",
    },
}

POLICY_LABELS: Dict[str, Dict[str, str]] = {
    "upstream.price": {
        "name": "行情数据通道",
        "impact": "关闭后，资产页中的股票价格将依赖缓存或显示异常。",
    },
    "upstream.rate": {
        "name": "汇率数据通道",
        "impact": "关闭后，跨币种资产折算可能使用默认汇率。",
    },
    "upstream.news": {
        "name": "快讯数据通道",
        "impact": "关闭后，资讯页将无法拉取最新快讯。",
    },
    "api.auth": {
        "name": "账号认证接口",
        "impact": "关闭后，登录、刷新会话、退出登录将不可用。",
    },
    "api.portfolio": {
        "name": "资产与持仓接口",
        "impact": "关闭后，资产列表、交易记录、统计接口将不可用。",
    },
    "api.news": {
        "name": "资讯接口",
        "impact": "关闭后，资讯相关查询与刷新不可用。",
    },
}

ACTION_LABELS: Dict[str, str] = {
    "admin.users.status": "修改用户状态",
    "admin.users.update": "更新用户信息",
    "admin.users.disable": "停用用户",
    "admin.users.enable": "启用用户",
    "admin.users.password.reset": "重置用户密码",
    "admin.users.sessions.revoke": "强制用户下线",
    "admin.users.ai_credits.grant": "调整用户AI积分",
    "admin.config.update": "更新系统配置",
    "admin.config.reset": "恢复系统配置默认值",
    "admin.data.snapshot.trigger": "手动触发快照",
    "admin.data.snapshot.cleanup_weekend": "清理周末日收益",
    "admin.data.snapshot.cleanup_market_closed": "清理休市日收益",
    "admin.data.backup": "创建数据库备份",
    "admin.data.restore": "恢复数据库备份",
    "admin.data.rebind.execute": "执行历史数据归属迁移",
    "admin.apis.smoke_test": "执行接口冒烟测试",
    "admin.apis.policies.update": "更新接口策略",
    "admin.apis.policies.batch_update": "批量更新接口策略",
    "admin.invites.generate": "生成邀请码",
    "admin.invites.revoke": "作废邀请码",
    "admin.ops.invite_acquire.update": "更新运营配置（邀请码获取页）",
    "admin.ops.user_group.update": "更新运营配置（用户群页）",
    "admin.ops.ios_qr.update": "更新运营配置（苹果版下载二维码）",
    "admin.ops.app_update.update": "更新运营配置（App检查更新）",
}

ERROR_LABELS: Dict[str, str] = {
    "Admin privileges required": "当前账号没有后台权限",
    "Invalid or expired token": "登录状态已过期，请重新登录",
    "Missing Authorization header": "登录状态已过期，请重新登录",
    "User not found": "用户不存在",
    "User is disabled": "账号已停用，请联系管理员",
    "Missing user_id": "缺少用户标识",
    "Invalid status": "状态值不合法",
    "Cannot disable current admin user": "不能停用当前登录管理员",
    "Cannot remove current admin role": "不能取消当前登录管理员权限",
    "No updatable fields": "没有可更新的字段",
    "No update payload": "缺少更新内容",
    "Local anonymous user is read-only": "本机匿名用户是只读用户，无法操作",
    "Missing scope_key": "缺少策略标识",
    "Missing target_user_id": "缺少目标用户标识",
    "Missing username": "缺少用户名",
    "Missing reason": "缺少调整原因",
    "Invite code not active or not found": "邀请码不存在或不可作废",
}

REGISTER_METHOD_LABELS: Dict[str, str] = {
    "password_invite": "账号密码 + 邀请码",
    "email": "邮箱验证码（历史）",
    "local_anonymous": "本机未登录用户",
}

STATUS_LABELS: Dict[str, str] = {
    "active": "正常",
    "disabled": "已停用",
    "used": "已使用",
    "revoked": "已作废",
}

POLICY_TYPE_LABELS: Dict[str, str] = {
    "upstream": "上游通道",
    "api_group": "业务接口组",
}

OPS_INVITE_ACQUIRE_TEXT_KEY = "ops.invite_acquire.text"
OPS_INVITE_ACQUIRE_IMAGE_URL_KEY = "ops.invite_acquire.image_url"
OPS_USER_GROUP_TEXT_KEY = "ops.user_group.text"
OPS_USER_GROUP_IMAGE_URL_KEY = "ops.user_group.image_url"
OPS_IOS_QR_TEXT_KEY = "ops.ios_qr.text"
OPS_IOS_QR_IMAGE_URL_KEY = "ops.ios_qr.image_url"
OPS_APP_UPDATE_TEXT_KEY = "ops.app_update.text"
OPS_APP_UPDATE_DOWNLOAD_URL_KEY = "ops.app_update.download_url"
OPS_INVITE_ACQUIRE_TEXT_MAX_LENGTH = 200
OPS_INVITE_ACQUIRE_IMAGE_URL_MAX_LENGTH = 2048
OPS_IOS_QR_TEXT_MAX_LENGTH = 200
OPS_IOS_QR_IMAGE_URL_MAX_LENGTH = 2048
OPS_APP_UPDATE_TEXT_MAX_LENGTH = 500
OPS_APP_UPDATE_DOWNLOAD_URL_MAX_LENGTH = 2048

API_TEST_CASES_MARKET: List[Dict[str, str]] = [
    {"name": "工商银行", "code": "sh601398", "asset_type": "a"},
    {"name": "比亚迪", "code": "sz002594", "asset_type": "a"},
    {"name": "腾讯控股", "code": "hk00700", "asset_type": "hk"},
    {"name": "美团-W", "code": "hk03690", "asset_type": "hk"},
    {"name": "苹果", "code": "gb_aapl", "asset_type": "us"},
    {"name": "特斯拉", "code": "gb_tsla", "asset_type": "us"},
    {"name": "自由现金流ETF", "code": "sz159201", "asset_type": "a"},
    {"name": "标普ETF", "code": "sz159655", "asset_type": "a"},
    {"name": "短融ETF", "code": "sh511360", "asset_type": "a"},
]

API_TEST_CASES_FUND: List[Dict[str, str]] = [
    {"name": "易方达增强回报债券A", "code": "f_110017", "asset_type": "fund"},
]

API_TEST_PROVIDER_LABELS: Dict[str, str] = {
    "sina_quote": "新浪财经行情",
    "tencent_quote": "腾讯财经行情",
    "eastmoney_quote": "东方财富行情",
    "forex_rate": "汇率",
}

API_TEST_PROVIDER_ALERT_LABELS: Dict[str, str] = {
    "sina_quote": "新浪行情告警",
    "eastmoney_quote": "东财行情告警",
    "tencent_quote": "腾讯行情告警",
    "forex_rate": "汇率行情告警",
}

PROVIDER_TEST_REPORT_TIMEZONE = timezone(timedelta(hours=8))
ADMIN_PORTFOLIO_CACHE_TTL_SECONDS = 24 * 60 * 60
PRICE_ALERT_ROUTE_NAME = "admin_apis_price_alerts"
PRICE_ALERT_DELTA_PCT_WARNING = 0.15
PRICE_ALERT_DELTA_PCT_CRITICAL = 0.5
PRICE_ALERT_REPORT_TIMEZONE = timezone(timedelta(hours=8))

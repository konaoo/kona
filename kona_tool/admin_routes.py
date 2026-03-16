"""
管理后台 API 路由
"""
from __future__ import annotations

import importlib.util
import csv
import io
import hashlib
import json
import logging
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request, g, current_app, make_response

import config
from core.auth import admin_required
from core.price import batch_get_prices, get_price_runtime_metrics, get_price_source_health, get_forex_rates, get_price
from core.fund import (
    get_fund_eastmoney_f10,
    get_fund_tiantian_price,
    get_fund_tencent_jj,
    get_fund_eastmoney_mobile,
    get_fund_overseas_html,
)
from core.stock import (
    get_blackrock_fund_price,
    get_marketscreener_fund_price,
    get_boursorama_fund_price,
    get_ft_fund_price,
    get_stock_price,
    get_tencent_stock_price,
    get_sina_direct_stock_price,
    get_eastmoney_stock_price,
    get_us_stock_price,
)
from core.snapshot import take_snapshot
from core.system import system_manager
from core.admin.user_admin import reset_user_password, revoke_user_sessions
from core.admin.policies import list_policies, update_policy, batch_update_policies
from core.policy_runtime import invalidate_policy_cache
from core.ip_region import normalize_region_text
from core.utils import monitored_http_get, safe_float
from core.asset_type import asset_type_label, infer_asset_type


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

_RUNTIME_CONFIG_OVERRIDES: Dict[str, Any] = {}
_DEFAULT_CONFIG_VALUES: Dict[str, Any] = {
    key: getattr(config, key, None) for key in CONFIG_WHITELIST
}
_ADMIN_READ_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_ADMIN_READ_CACHE_LOCK = threading.Lock()
_ADMIN_PORTFOLIO_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_ADMIN_PORTFOLIO_CACHE_LOCK = threading.Lock()
_ADMIN_DB = None
_ADMIN_LOGGER = logging.getLogger(__name__)
_API_TEST_CASES_MARKET: List[Dict[str, str]] = [
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
_API_TEST_CASES_FUND: List[Dict[str, str]] = [
    {"name": "易方达增强回报债券A", "code": "f_110017", "asset_type": "fund"},
]
_API_TEST_PROVIDER_LABELS: Dict[str, str] = {
    "sina_quote": "新浪财经行情",
    "tencent_quote": "腾讯财经行情",
    "eastmoney_quote": "东方财富行情",
    "forex_rate": "汇率",
}
_API_TEST_PROVIDER_ALERT_LABELS: Dict[str, str] = {
    "sina_quote": "新浪行情告警",
    "eastmoney_quote": "东财行情告警",
    "tencent_quote": "腾讯行情告警",
    "forex_rate": "汇率行情告警",
}
PROVIDER_TEST_REPORT_TIMEZONE = timezone(timedelta(hours=8))
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
ADMIN_PORTFOLIO_CACHE_TTL_SECONDS = 24 * 60 * 60
PRICE_ALERT_ROUTE_NAME = "admin_apis_price_alerts"
PRICE_ALERT_DELTA_PCT_WARNING = 0.15
PRICE_ALERT_DELTA_PCT_CRITICAL = 0.5
PRICE_ALERT_REPORT_TIMEZONE = timezone(timedelta(hours=8))


def _price_alert_exchange_candidates(code: str) -> List[str]:
    lower = str(code or "").strip().lower()
    if not lower.startswith("f_"):
        return []
    suffix = lower[2:].strip()
    if not suffix.isdigit() or len(suffix) != 6:
        return []
    if suffix.startswith("11") and not suffix.startswith(("511",)):
        return []
    if suffix.startswith(("15", "18")):
        return [f"sz{suffix}"]
    if suffix.startswith(("50", "51", "52", "56", "58", "511")):
        return [f"sh{suffix}"]
    return []


def _price_alert_abs_delta_pct(current: float, baseline: float) -> float:
    if current <= 0 or baseline <= 0:
        return 0.0
    return abs(current - baseline) / baseline * 100


def _price_alert_severity(delta_pct: float) -> str:
    if delta_pct >= PRICE_ALERT_DELTA_PCT_CRITICAL:
        return "critical"
    if delta_pct >= PRICE_ALERT_DELTA_PCT_WARNING:
        return "warning"
    return "info"


def _load_price_alert_holdings() -> List[Dict[str, Any]]:
    if _ADMIN_DB is None:
        raise RuntimeError("admin database is not initialized")
    conn = _ADMIN_DB.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT p.code, p.name, p.curr, p.user_id, u.username
            FROM portfolio p
            LEFT JOIN users u ON u.id = p.user_id
            WHERE ABS(COALESCE(p.qty, 0)) > 1e-9
            ORDER BY p.code ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        code = str(row["code"] or "").strip()
        if not code:
            continue
        item = grouped.setdefault(
            code,
            {
                "code": code,
                "name": str(row["name"] or "").strip() or code,
                "curr": str(row["curr"] or "").strip().upper() or "CNY",
                "usernames": [],
                "user_count": 0,
            },
        )
        username = str(row["username"] or "").strip() or "本地资产"
        if username not in item["usernames"]:
            item["usernames"].append(username)
    for item in grouped.values():
        item["user_count"] = len(item["usernames"])
    return list(grouped.values())


def _probe_price_alert_sources(code: str) -> Tuple[Tuple[float, float, float, float], List[Dict[str, Any]]]:
    current = get_price(code, use_cache=False)
    sources: List[Dict[str, Any]] = []
    lower = str(code or "").strip().lower()

    def add_source(source_key: str, source_label: str, quote: Tuple[float, float, float, float]) -> None:
        price, yclose, amt, chg = quote
        sources.append(
            {
                "source_key": source_key,
                "source_label": source_label,
                "price": float(price or 0.0),
                "yclose": float(yclose or 0.0),
                "amt": float(amt or 0.0),
                "chg": float(chg or 0.0),
            }
        )

    if lower.startswith("ft_"):
        isin = lower.replace("ft_", "").upper()
        add_source("blackrock_official", "贝莱德官方", get_blackrock_fund_price(isin))
        add_source("marketscreener", "MarketScreener", get_marketscreener_fund_price(isin))
        add_source("boursorama", "Boursorama", get_boursorama_fund_price(isin))
        add_source("financial_times", "Financial Times", get_ft_fund_price(isin))
        return current, sources

    if lower.startswith("f_"):
        clean_code = lower.replace("f_", "")
        exchange_candidates = _price_alert_exchange_candidates(lower)
        if exchange_candidates:
            for candidate in exchange_candidates:
                add_source(f"exchange:{candidate}", f"交易所 {candidate}", get_stock_price(candidate))
            return current, sources
        add_source("eastmoney_f10", "东财 F10", get_fund_eastmoney_f10(clean_code))
        if clean_code.startswith("968"):
            add_source("overseas_1234567", "海外基金页", get_fund_overseas_html(clean_code))
        add_source("eastmoney_mobile", "东财手机端", get_fund_eastmoney_mobile(clean_code))
        add_source("tiantian", "天天基金", get_fund_tiantian_price(lower))
        add_source("tencent_jj", "腾讯基金", get_fund_tencent_jj(clean_code))
        return current, sources

    asset_type = infer_asset_type(code)
    if asset_type in {"a", "hk"}:
        add_source("tencent_quote", "腾讯财经", get_tencent_stock_price(code))
        add_source("sina_quote", "新浪财经", get_sina_direct_stock_price(code))
        add_source("eastmoney_quote", "东方财富", get_eastmoney_stock_price(code))
        return current, sources

    if asset_type == "us":
        add_source("sina_us_quote", "新浪美股", get_sina_direct_stock_price(code))
        add_source("eastmoney_us_quote", "东方财富美股", get_eastmoney_stock_price(code))
        add_source("us_primary", "美股主链路", get_us_stock_price(code))
        return current, sources

    return current, sources


def _guess_probe_primary_source(current_price: float, source_rows: List[Dict[str, Any]]) -> str:
    for row in source_rows:
        price = float(row.get("price") or 0.0)
        if price <= 0:
            continue
        if _price_alert_abs_delta_pct(current_price, price) <= 0.001:
            return str(row.get("source_label") or row.get("source_key") or "")
    return ""


def _build_price_probe_payload(code: str) -> Dict[str, Any]:
    raw_code = str(code or "").strip()
    if not raw_code:
        raise ValueError("缺少资产代码")

    current, source_rows = _probe_price_alert_sources(raw_code)
    current_price = float(current[0] or 0.0)
    current_yclose = float(current[1] or 0.0)
    current_amt = float(current[2] or 0.0)
    current_chg = float(current[3] or 0.0)
    asset_type = infer_asset_type(raw_code)
    primary_source = _guess_probe_primary_source(current_price, source_rows)

    normalized_sources: List[Dict[str, Any]] = []
    valid_deltas: List[float] = []
    for row in source_rows:
        price = float(row.get("price") or 0.0)
        delta_pct = _price_alert_abs_delta_pct(current_price, price)
        if current_price > 0 and price > 0:
            valid_deltas.append(delta_pct)
        normalized_sources.append(
            {
                **row,
                "ok": price > 0,
                "delta_pct": round(delta_pct, 4),
            }
        )

    diagnosis_status = "ok"
    diagnosis_summary = "主价与各源基本一致。"
    if current_price <= 0:
        diagnosis_status = "critical"
        diagnosis_summary = "系统当前主价为空，这条资产需要优先排查。"
    elif not any(float(item.get("price") or 0.0) > 0 for item in normalized_sources):
        diagnosis_status = "warning"
        diagnosis_summary = "主价拿到了，但当前没有可用的多源对比结果。"
    elif valid_deltas:
        max_delta = max(valid_deltas)
        if max_delta >= PRICE_ALERT_DELTA_PCT_CRITICAL:
            diagnosis_status = "critical"
            diagnosis_summary = f"主价和备选源最大偏差 {max_delta:.2f}%，建议核对主链路。"
        elif max_delta >= PRICE_ALERT_DELTA_PCT_WARNING:
            diagnosis_status = "warning"
            diagnosis_summary = f"主价和备选源有轻微偏差，最大 {max_delta:.2f}%。"

    return {
        "code": raw_code,
        "asset_type": asset_type,
        "asset_type_label": asset_type_label(asset_type),
        "current": {
            "price": current_price,
            "yclose": current_yclose,
            "amt": current_amt,
            "chg": current_chg,
            "source_hint": primary_source,
        },
        "sources": normalized_sources,
        "diagnosis": {
            "status": diagnosis_status,
            "summary": diagnosis_summary,
        },
    }


def _build_price_alert_for_holding(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    code = str(item.get("code") or "").strip()
    if not code:
        return []
    lower = code.lower()
    exchange_candidates = _price_alert_exchange_candidates(lower)
    if lower.startswith("ft_"):
        pass
    elif lower.startswith("f_"):
        clean_code = lower.replace("f_", "")
        if not clean_code.startswith("968") and not exchange_candidates:
            return []
    else:
        return []

    current, source_rows = _probe_price_alert_sources(code)
    current_price = float(current[0] or 0.0)
    available = [row for row in source_rows if float(row.get("price") or 0.0) > 0]
    alerts: List[Dict[str, Any]] = []

    def append_alert(
        *,
        alert_type: str,
        reason: str,
        baseline: Dict[str, Any],
        suggestion: str,
    ) -> None:
        baseline_price = float(baseline.get("price") or 0.0)
        delta_pct = _price_alert_abs_delta_pct(current_price, baseline_price)
        alerts.append(
            {
                "code": code,
                "name": item.get("name") or code,
                "curr": item.get("curr") or "CNY",
                "user_count": int(item.get("user_count") or 0),
                "usernames": list(item.get("usernames") or []),
                "current_price": current_price,
                "current_yclose": float(current[1] or 0.0),
                "baseline_price": baseline_price,
                "baseline_yclose": float(baseline.get("yclose") or 0.0),
                "baseline_source": baseline.get("source_label") or baseline.get("source_key") or "",
                "baseline_source_key": baseline.get("source_key") or "",
                "delta_pct": round(delta_pct, 4),
                "severity": _price_alert_severity(delta_pct),
                "alert_type": alert_type,
                "reason": reason,
                "suggestion": suggestion,
                "sources": available,
            }
        )

    exchange_candidates = [
        row for row in available if str(row.get("source_key") or "").startswith("exchange:")
    ]
    if code.lower().startswith("f_") and exchange_candidates:
        baseline = exchange_candidates[0]
        exchange_code = str(baseline.get("source_key") or "").split("exchange:", 1)[-1]
        if exchange_code and exchange_code != code:
            append_alert(
                alert_type="normalization",
                reason=f"当前资产疑似场内基金误存为 {code}，应改走 {exchange_code} 场内行情。",
                baseline=baseline,
                suggestion=f"将资产代码标准化为 {exchange_code}，并优先使用交易所价格链路。",
            )
            return alerts

    trusted: Dict[str, Any] | None = None
    if lower.startswith("ft_"):
        for source_key in ("blackrock_official", "marketscreener", "boursorama", "financial_times"):
            trusted = next((row for row in available if row.get("source_key") == source_key), None)
            if trusted:
                break
    elif lower.startswith("f_"):
        clean_code = lower.replace("f_", "")
        preferred_order = (
            ("exchange:",) if exchange_candidates else ()
        )
        if clean_code.startswith("968"):
            order = ["overseas_1234567", "eastmoney_f10", "eastmoney_mobile", "tiantian", "tencent_jj"]
        else:
            order = ["eastmoney_f10", "eastmoney_mobile", "tiantian", "tencent_jj"]
        if preferred_order:
            trusted = exchange_candidates[0]
        if trusted is None:
            for source_key in order:
                trusted = next((row for row in available if row.get("source_key") == source_key), None)
                if trusted:
                    break

    if trusted and current_price > 0:
        delta_pct = _price_alert_abs_delta_pct(current_price, float(trusted.get("price") or 0.0))
        if delta_pct >= PRICE_ALERT_DELTA_PCT_WARNING:
            append_alert(
                alert_type="price_mismatch",
                reason=f"当前主价格与可信基准源 {trusted.get('source_label')} 偏差过大。",
                baseline=trusted,
                suggestion=f"检查 {trusted.get('source_label')} 是否应提升优先级，或将当前价格回退到该源。",
            )
    elif current_price <= 0 and trusted:
        append_alert(
            alert_type="missing_price",
            reason="当前主价格无返回，但存在可用备源。",
            baseline=trusted,
            suggestion=f"回退到 {trusted.get('source_label')}，避免前端显示空价。",
        )

    return alerts


def _load_price_alerts_payload() -> Dict[str, Any]:
    holdings = _load_price_alert_holdings()
    items: List[Dict[str, Any]] = []
    for holding in holdings:
        items.extend(_build_price_alert_for_holding(holding))

    items.sort(
        key=lambda row: (
            {"critical": 0, "warning": 1, "info": 2}.get(str(row.get("severity") or "info"), 9),
            -float(row.get("delta_pct") or 0.0),
            str(row.get("code") or ""),
        )
    )
    summary = {"critical": 0, "warning": 0, "info": 0}
    for row in items:
        severity = str(row.get("severity") or "info")
        summary[severity] = int(summary.get(severity, 0)) + 1

    return {
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_assets": len(holdings),
        "alert_count": len(items),
        "summary": summary,
        "items": items,
    }


def _save_price_alert_report_snapshot(payload: Dict[str, Any]) -> None:
    if _ADMIN_DB is None:
        return
    tested_at_utc = str(payload.get("tested_at_utc") or "").strip()
    if not tested_at_utc:
        return
    try:
        report_date = datetime.now(PRICE_ALERT_REPORT_TIMEZONE).date().isoformat()
        _ADMIN_DB.save_price_alert_report(
            report_date=report_date,
            tested_at_utc=tested_at_utc,
            total_assets=int(payload.get("total_assets") or 0),
            alert_count=int(payload.get("alert_count") or 0),
            summary=dict(payload.get("summary") or {}),
            items=list(payload.get("items") or []),
        )
    except Exception:
        current_app.logger.exception("save_price_alert_report failed")


def _provider_test_summary(providers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    degraded_keys = [
        provider_key
        for provider_key, payload in providers.items()
        if str((payload or {}).get("status") or "").lower() != "ok"
    ]
    if not degraded_keys:
        return {
            "status": "ok",
            "label": "正常",
            "alert_keys": [],
        }
    if len(degraded_keys) == 1:
        provider_key = degraded_keys[0]
        return {
            "status": "alert",
            "label": _API_TEST_PROVIDER_ALERT_LABELS.get(provider_key, "行情告警"),
            "alert_keys": degraded_keys,
        }
    return {
        "status": "alert",
        "label": "多源告警",
        "alert_keys": degraded_keys,
    }


def _normalize_provider_report(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    raw = dict(payload or {})
    summary = raw.get("summary")
    providers = raw.get("providers")
    tested_at_utc = str(raw.get("tested_at_utc") or "").strip()
    report_slot = str(raw.get("report_slot") or "").strip()
    updated_at = str(raw.get("updated_at") or "").strip()
    if not isinstance(summary, dict):
        summary = {}
    if not isinstance(providers, dict):
        providers = {}
    return {
        "report_slot": report_slot,
        "tested_at_utc": tested_at_utc,
        "updated_at": updated_at,
        "summary": summary,
        "providers": providers,
    }


def _save_provider_test_report_snapshot(payload: Dict[str, Any]) -> None:
    if _ADMIN_DB is None:
        return
    tested_at_utc = str(payload.get("tested_at_utc") or "").strip()
    if not tested_at_utc:
        return
    try:
        report_slot = datetime.now(PROVIDER_TEST_REPORT_TIMEZONE).strftime("%Y-%m-%dT%H")
        _ADMIN_DB.save_provider_test_report(
            report_slot=report_slot,
            tested_at_utc=tested_at_utc,
            summary=dict(payload.get("summary") or {}),
            providers=dict(payload.get("providers") or {}),
        )
    except Exception:
        _ADMIN_LOGGER.exception("save_provider_test_report failed")


def _get_latest_provider_test_report() -> Dict[str, Any] | None:
    if _ADMIN_DB is None:
        return None
    try:
        report = _ADMIN_DB.get_latest_provider_test_report()
    except Exception:
        _ADMIN_LOGGER.exception("get_latest_provider_test_report failed")
        return None
    if not report:
        return None
    return _normalize_provider_report(report)


def _list_price_alert_report_history(limit: int = 7) -> List[Dict[str, Any]]:
    if _ADMIN_DB is None:
        return []
    try:
        return _ADMIN_DB.list_price_alert_reports(limit=limit)
    except Exception:
        current_app.logger.exception("list_price_alert_reports failed")
        return []


def _get_latest_price_alert_report() -> Dict[str, Any] | None:
    if _ADMIN_DB is None:
        return None
    try:
        return _ADMIN_DB.get_latest_price_alert_report()
    except Exception:
        current_app.logger.exception("get_latest_price_alert_report failed")
        return None


def _make_invite_code(length: int = 10) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _load_script_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False
    raise ValueError("Invalid boolean value")


def _coerce_config_value(key: str, value: Any) -> Any:
    rule = CONFIG_WHITELIST[key]
    typ = rule["type"]
    if typ == "int":
        v = int(value)
        if "min" in rule and v < rule["min"]:
            raise ValueError(f"{key} must be >= {rule['min']}")
        if "max" in rule and v > rule["max"]:
            raise ValueError(f"{key} must be <= {rule['max']}")
        return v
    if typ == "bool":
        return _coerce_bool(value)
    if typ == "str":
        v = str(value).strip()
        choices = rule.get("choices", [])
        if choices and v not in choices:
            raise ValueError(f"{key} must be one of {choices}")
        return v
    raise ValueError(f"Unsupported config type: {typ}")


def _get_whitelist_configs() -> List[Dict[str, Any]]:
    items = []
    for key, rule in CONFIG_WHITELIST.items():
        value = _RUNTIME_CONFIG_OVERRIDES.get(key, getattr(config, key, None))
        default_value = _DEFAULT_CONFIG_VALUES.get(key)
        if "choices" in rule:
            recommended = " / ".join(str(v) for v in rule["choices"])
        elif "min" in rule and "max" in rule:
            recommended = f"{rule['min']} - {rule['max']}"
        elif "min" in rule:
            recommended = f">= {rule['min']}"
        else:
            recommended = "-"
        items.append({
            "key": key,
            "display_name": rule.get("display_name", key),
            "value": value,
            "default_value": default_value,
            "type": rule["type"],
            "description": rule["description"],
            "min": rule.get("min"),
            "max": rule.get("max"),
            "choices": rule.get("choices", []),
            "recommended": recommended,
        })
    return items


def _json_body() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _normalize_invite_acquire_text(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text or len(text) > OPS_INVITE_ACQUIRE_TEXT_MAX_LENGTH:
        raise ValueError(f"text must be 1-{OPS_INVITE_ACQUIRE_TEXT_MAX_LENGTH} characters")
    return text


def _normalize_invite_acquire_image_url(raw: Any) -> str:
    url = str(raw or "").strip()
    if not url:
        return ""
    if len(url) > OPS_INVITE_ACQUIRE_IMAGE_URL_MAX_LENGTH:
        raise ValueError(f"image_url must be <= {OPS_INVITE_ACQUIRE_IMAGE_URL_MAX_LENGTH} characters")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("image_url must start with http:// or https://")
    return url


def _normalize_ios_qr_text(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text or len(text) > OPS_IOS_QR_TEXT_MAX_LENGTH:
        raise ValueError(f"text must be 1-{OPS_IOS_QR_TEXT_MAX_LENGTH} characters")
    return text


def _normalize_ios_qr_image_url(raw: Any) -> str:
    url = str(raw or "").strip()
    if not url:
        return ""
    if len(url) > OPS_IOS_QR_IMAGE_URL_MAX_LENGTH:
        raise ValueError(f"image_url must be <= {OPS_IOS_QR_IMAGE_URL_MAX_LENGTH} characters")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("image_url must start with http:// or https://")
    return url


def _normalize_app_update_text(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text or len(text) > OPS_APP_UPDATE_TEXT_MAX_LENGTH:
        raise ValueError(f"text must be 1-{OPS_APP_UPDATE_TEXT_MAX_LENGTH} characters")
    return text


def _normalize_app_update_download_url(raw: Any) -> str:
    url = str(raw or "").strip()
    if not url:
        return ""
    if len(url) > OPS_APP_UPDATE_DOWNLOAD_URL_MAX_LENGTH:
        raise ValueError(
            f"download_url must be <= {OPS_APP_UPDATE_DOWNLOAD_URL_MAX_LENGTH} characters"
        )
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("download_url must start with http:// or https://")
    return url


def _load_invite_acquire_ops_config(db) -> Dict[str, str]:
    return _load_ops_text_image_config(
        db=db,
        text_key=OPS_INVITE_ACQUIRE_TEXT_KEY,
        image_url_key=OPS_INVITE_ACQUIRE_IMAGE_URL_KEY,
        default_text=str(config.INVITE_ACQUIRE_TEXT).strip() or "小红书被限制了，进微信群领邀请码。",
        default_image_url=str(config.INVITE_ACQUIRE_IMAGE_URL).strip(),
    )


def _load_user_group_ops_config(db) -> Dict[str, str]:
    return _load_ops_text_image_config(
        db=db,
        text_key=OPS_USER_GROUP_TEXT_KEY,
        image_url_key=OPS_USER_GROUP_IMAGE_URL_KEY,
        default_text=str(config.USER_GROUP_TEXT).strip() or "加入咔咔用户群",
        default_image_url=str(config.USER_GROUP_IMAGE_URL).strip(),
    )


def _load_ios_qr_ops_config(db) -> Dict[str, str]:
    return _load_ops_text_image_config(
        db=db,
        text_key=OPS_IOS_QR_TEXT_KEY,
        image_url_key=OPS_IOS_QR_IMAGE_URL_KEY,
        default_text=str(config.IOS_QR_TEXT).strip() or "扫码下载苹果版",
        default_image_url=str(config.IOS_QR_IMAGE_URL).strip(),
    )


def _load_app_update_ops_config(db) -> Dict[str, str]:
    text_raw = db.get_runtime_config(OPS_APP_UPDATE_TEXT_KEY)
    download_url_raw = db.get_runtime_config(OPS_APP_UPDATE_DOWNLOAD_URL_KEY)
    default_text = str(config.CLIENT_APP_RELEASE_NOTES).strip() or "更新内容"
    default_download_url = str(config.CLIENT_APP_DOWNLOAD_URL).strip()
    text = str(text_raw).strip() if text_raw is not None else default_text
    if not text:
        text = default_text
    download_url = (
        str(download_url_raw).strip()
        if download_url_raw is not None
        else default_download_url
    )
    return {"text": text, "download_url": download_url}


def _load_ops_text_image_config(
    db,
    *,
    text_key: str,
    image_url_key: str,
    default_text: str,
    default_image_url: str,
) -> Dict[str, str]:
    text_raw = db.get_runtime_config(text_key)
    image_url_raw = db.get_runtime_config(image_url_key)
    text = str(text_raw).strip() if text_raw is not None else default_text
    if not text:
        text = default_text
    image_url = str(image_url_raw).strip() if image_url_raw is not None else default_image_url
    return {"text": text, "image_url": image_url}


def _admin_cache_ttl_seconds() -> int:
    try:
        ttl = int(getattr(config, "ADMIN_READ_CACHE_TTL_SECONDS", 120))
    except Exception:
        ttl = 120
    return max(0, min(ttl, 3600))


def _admin_parse_force_arg() -> bool:
    raw = str(request.args.get("force", "") or "").strip()
    if not raw:
        return False
    return _coerce_bool(raw)


def _admin_cache_key(route_name: str, params: Dict[str, Any]) -> Tuple[str, str]:
    normalized = {
        str(k): str(v)
        for k, v in params.items()
        if str(k).strip().lower() != "force"
    }
    payload = json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha1(f"{route_name}|{payload}".encode("utf-8")).hexdigest()
    return f"{route_name}:{digest}", digest


def _admin_cache_clear() -> None:
    with _ADMIN_READ_CACHE_LOCK:
        _ADMIN_READ_CACHE.clear()
    with _ADMIN_PORTFOLIO_CACHE_LOCK:
        _ADMIN_PORTFOLIO_CACHE.clear()


def _admin_cached_payload(
    route_name: str,
    params: Dict[str, Any],
    force: bool,
    loader: Callable[[], Dict[str, Any]],
) -> Tuple[Dict[str, Any], str, str, int]:
    ttl = _admin_cache_ttl_seconds()
    cache_key, params_hash = _admin_cache_key(route_name, params)
    started = time.perf_counter()
    if not force and ttl > 0:
        now_ts = time.time()
        with _ADMIN_READ_CACHE_LOCK:
            hit = _ADMIN_READ_CACHE.get(cache_key)
            if hit and hit[0] > now_ts:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                return dict(hit[1]), "HIT", params_hash, elapsed_ms
            if hit:
                _ADMIN_READ_CACHE.pop(cache_key, None)

    payload = loader()
    if ttl > 0:
        expires_at = time.time() + ttl
        with _ADMIN_READ_CACHE_LOCK:
            _ADMIN_READ_CACHE[cache_key] = (expires_at, dict(payload))
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    cache_state = "BYPASS" if force or ttl <= 0 else "MISS"
    return payload, cache_state, params_hash, elapsed_ms


def _admin_log_read(route_name: str, cache_state: str, elapsed_ms: int, params_hash: str) -> None:
    try:
        current_app.logger.info(
            "admin_read route=%s cache=%s elapsed_ms=%s params_hash=%s",
            route_name,
            cache_state,
            elapsed_ms,
            params_hash,
        )
    except Exception:
        pass


def _admin_region_display(value: Any) -> str:
    normalized = normalize_region_text(value)
    return normalized or "未知"


def _iso_utc(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat()


def _to_cny(amount: Any, curr: Any, rates: Dict[str, Any]) -> float:
    value = safe_float(amount)
    if value == 0:
        return 0.0
    code = str(curr or "CNY").strip().upper() or "CNY"
    if code == "CNY":
        return float(value)
    rate = safe_float((rates or {}).get(code, 0))
    if rate <= 0:
        return 0.0
    return float(value * rate)


def _build_admin_portfolio_payload(db, user_id: str) -> Dict[str, Any]:
    portfolio = db.get_portfolio("all", user_id)
    cash_assets = db.get_cash_assets(user_id)
    other_assets = db.get_other_assets(user_id)
    liabilities = db.get_liabilities(user_id)
    rates = get_forex_rates() or {}

    codes = [str(item.get("code", "")).strip() for item in portfolio if str(item.get("code", "")).strip()]
    latest_prices = batch_get_prices(codes) if codes else {}

    items: List[Dict[str, Any]] = []
    for item in portfolio:
        code = str(item.get("code", ""))
        name = str(item.get("name", ""))
        qty = float(item.get("qty") or 0.0)
        cost_price = float(item.get("price") or 0.0)
        adjustment = float(item.get("adjustment") or 0.0)
        curr = str(item.get("curr", "") or "CNY")
        asset_type = str(item.get("asset_type", "") or "a")

        latest = latest_prices.get(code, (0, 0, 0, 0))
        latest_price = safe_float(latest[0] if isinstance(latest, tuple) and len(latest) > 0 else 0)
        yclose = safe_float(latest[1] if isinstance(latest, tuple) and len(latest) > 1 else 0)
        if latest_price > 0:
            effective_price = latest_price
        elif yclose > 0:
            effective_price = yclose
        elif cost_price > 0:
            effective_price = cost_price
        else:
            effective_price = 0.0

        cost_amount = cost_price * qty
        current_amount = effective_price * qty
        pnl_amount = current_amount - cost_amount + adjustment
        cost_amount_abs = abs(cost_amount)
        pnl_rate = (pnl_amount / cost_amount_abs * 100.0) if cost_amount_abs > 0 else 0.0

        items.append(
            {
                "code": code,
                "name": name,
                "qty": qty,
                "price": cost_price,
                "curr": curr,
                "asset_type": asset_type,
                "latest_price": round(float(effective_price), 6),
                "pnl_cny": round(float(_to_cny(pnl_amount, curr, rates)), 2),
                "pnl_rate": round(float(pnl_rate), 4),
                "type_label": asset_type_label(asset_type),
            }
        )

    cash_cny = round(sum(_to_cny(i.get("amount", 0), i.get("curr", "CNY"), rates) for i in cash_assets), 2)
    other_cny = round(sum(_to_cny(i.get("amount", 0), i.get("curr", "CNY"), rates) for i in other_assets), 2)
    liability_cny = round(sum(_to_cny(i.get("amount", 0), i.get("curr", "CNY"), rates) for i in liabilities), 2)

    now_utc = datetime.now(timezone.utc)
    expires_utc = now_utc + timedelta(seconds=ADMIN_PORTFOLIO_CACHE_TTL_SECONDS)
    cached_at = _iso_utc(now_utc)
    expires_at = _iso_utc(expires_utc)
    return {
        "user_id": user_id,
        "total": len(items),
        "summary": {
            "cash_cny": cash_cny,
            "other_cny": other_cny,
            "liability_cny": liability_cny,
            "as_of": cached_at,
        },
        "items": items,
        "cache": {
            "cached_at": cached_at,
            "expires_at": expires_at,
        },
    }


def _format_api_test_item(
    *,
    case: Dict[str, str],
    ok: bool,
    latency_ms: int,
    detail: str = "",
    status: str = "",
    price: float = 0.0,
    yclose: float = 0.0,
) -> Dict[str, Any]:
    change = (price - yclose) if yclose > 0 else 0.0
    change_pct = (change / yclose * 100) if yclose > 0 else 0.0
    item_status = str(status or ("ok" if ok else "error")).strip().lower() or "error"
    return {
        "name": str(case.get("name", "")),
        "code": str(case.get("code", "")),
        "asset_type": str(case.get("asset_type", "")),
        "ok": bool(ok),
        "status": item_status,
        "price": round(float(price or 0.0), 4),
        "yclose": round(float(yclose or 0.0), 4),
        "change": round(change, 4),
        "change_pct": round(change_pct, 4),
        "latency_ms": int(latency_ms),
        "detail": detail,
    }


def _to_sina_quote_code(raw_code: str) -> str:
    code = str(raw_code or "").strip().lower()
    if code.startswith("f_"):
        return code
    if code.startswith(("sh", "sz", "bj", "hk", "gb_", "s_")):
        return code
    if code.isdigit() and len(code) == 6:
        return ("sh" if code[0] in {"5", "6", "9"} else "sz") + code
    if code.isdigit() and len(code) == 5:
        return "hk" + code
    if ".hk" in code:
        return "hk" + code.replace(".hk", "")
    if code:
        return "gb_" + code
    return code


def _to_tencent_quote_code(raw_code: str) -> str:
    code = str(raw_code or "").strip()
    lower = code.lower()
    if lower.startswith("f_"):
        return lower
    if lower.startswith("gb_"):
        return f"us{lower.replace('gb_', '').upper()}"
    if lower.startswith("us."):
        return f"us{lower.replace('us.', '').upper()}"
    if lower.startswith(("sh", "sz", "bj", "hk", "s_")):
        return lower
    if lower.isdigit() and len(lower) == 6:
        return ("sh" if lower[0] in {"5", "6", "9"} else "sz") + lower
    if lower.isdigit() and len(lower) == 5:
        return "hk" + lower
    if ".hk" in lower:
        return "hk" + lower.replace(".hk", "")
    return f"us{code.upper()}" if code else lower


def _eastmoney_secid_candidates(raw_code: str) -> List[str]:
    code = str(raw_code or "").strip().lower()
    if code.startswith("f_"):
        return []
    if code.startswith("gb_"):
        symbol = code.replace("gb_", "").upper()
        return [f"105.{symbol}", f"106.{symbol}"]
    if code.startswith("hk"):
        digits = "".join(ch for ch in code[2:] if ch.isdigit())
        if digits:
            return [f"116.{digits.zfill(5)}"]
    if code.startswith("sh") and len(code) >= 8:
        return [f"1.{code[2:8]}"]
    if code.startswith(("sz", "bj")) and len(code) >= 8:
        return [f"0.{code[2:8]}"]
    if code.isdigit() and len(code) == 6:
        market = "1" if code[0] in {"5", "6", "9"} else "0"
        return [f"{market}.{code}"]
    return []


def _parse_sina_quote(raw_code: str, text: str) -> Tuple[float, float]:
    if '="' not in text:
        return 0.0, 0.0
    payload = text.split('="', 1)[1].split('"', 1)[0]
    data = payload.split(",")
    code = _to_sina_quote_code(raw_code)
    curr = 0.0
    yclose = 0.0
    if code.startswith("gb_"):
        curr = safe_float(data[1] if len(data) > 1 else 0)
        yclose = safe_float(data[26] if len(data) > 26 else 0)
        if curr <= 0:
            curr = safe_float(data[21] if len(data) > 21 else 0)
    elif code.startswith("hk"):
        curr = safe_float(data[6] if len(data) > 6 else 0)
        yclose = safe_float(data[3] if len(data) > 3 else 0)
    else:
        curr = safe_float(data[3] if len(data) > 3 else 0)
        yclose = safe_float(data[2] if len(data) > 2 else 0)
    if curr <= 0 and yclose > 0:
        curr = yclose
    return curr, yclose


def _test_sina_quote(code: str) -> Tuple[float, float]:
    sina_code = _to_sina_quote_code(code)
    if sina_code.startswith("f_"):
        raise ValueError("新浪行情暂不支持场外基金代码")
    url = config.API_ENDPOINTS["sina_stock"].format(code=sina_code)
    headers = dict(config.HEADERS or {})
    headers["Referer"] = "https://finance.sina.com.cn"
    resp = monitored_http_get(
        "admin_sina_quote_test",
        url,
        headers=headers,
        timeout=min(3.0, float(getattr(config, "API_TIMEOUT", 3))),
    )
    price, yclose = _parse_sina_quote(code, resp.text)
    if price <= 0:
        raise RuntimeError("新浪返回为空或解析失败")
    return price, yclose


def _test_tencent_quote(code: str) -> Tuple[float, float]:
    tencent_code = _to_tencent_quote_code(code)
    if tencent_code.startswith("f_"):
        raise ValueError("腾讯行情暂不支持场外基金代码")
    url = config.API_ENDPOINTS["tencent_stock"].format(code=tencent_code)
    resp = monitored_http_get(
        "admin_tencent_quote_test",
        url,
        timeout=min(3.0, float(getattr(config, "API_TIMEOUT", 3))),
    )
    text = resp.text
    if '="' not in text:
        raise RuntimeError("腾讯返回格式异常")
    payload = text.split('="', 1)[1].split('"', 1)[0]
    parts = payload.split("~")
    curr = safe_float(parts[3] if len(parts) > 3 else 0)
    yclose = safe_float(parts[4] if len(parts) > 4 else 0)
    if curr <= 0 and yclose > 0:
        curr = yclose
    if curr <= 0:
        raise RuntimeError("腾讯返回为空或解析失败")
    return curr, yclose


def _test_eastmoney_quote(code: str) -> Tuple[float, float]:
    lower = str(code or "").strip().lower()
    if lower.startswith("f_"):
        price, yclose, _, _ = get_fund_eastmoney_f10(lower.replace("f_", ""))
        if price <= 0:
            raise RuntimeError("东方财富基金净值接口无返回")
        return float(price), float(yclose)

    secids = _eastmoney_secid_candidates(lower)
    if not secids:
        raise ValueError("东方财富不支持该代码格式")

    base_url = str(config.API_ENDPOINTS.get("eastmoney_stock") or "").strip()
    if not base_url:
        base_url = "https://push2.eastmoney.com/api/qt/stock/get"

    for secid in secids:
        resp = monitored_http_get(
            "admin_eastmoney_quote_test",
            base_url,
            params={"invt": 2, "fltt": 2, "fields": "f43,f60", "secid": secid},
            headers={"User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0")},
            timeout=min(3.0, float(getattr(config, "API_TIMEOUT", 3))),
        )
        body = resp.json() if resp.status_code == 200 else {}
        data = body.get("data") if isinstance(body, dict) else {}
        if not isinstance(data, dict):
            continue
        curr = safe_float(data.get("f43"))
        yclose = safe_float(data.get("f60"))
        if curr > 10000 and yclose > 10000:
            curr = curr / 100.0
            yclose = yclose / 100.0
        if curr <= 0 and yclose > 0:
            curr = yclose
        if curr > 0:
            return curr, yclose
    raise RuntimeError("东方财富返回为空或解析失败")


def _run_market_provider_test(provider_key: str) -> Dict[str, Any]:
    tester_map = {
        "sina_quote": _test_sina_quote,
        "tencent_quote": _test_tencent_quote,
        "eastmoney_quote": _test_eastmoney_quote,
    }
    tester = tester_map.get(provider_key)
    if tester is None:
        raise ValueError("Unsupported provider_key")

    cases = list(_API_TEST_CASES_MARKET)
    if provider_key == "eastmoney_quote":
        cases.extend(_API_TEST_CASES_FUND)

    items: List[Dict[str, Any]] = []
    for case in cases:
        started = time.perf_counter()
        try:
            price, yclose = tester(str(case.get("code", "")))
            latency_ms = int((time.perf_counter() - started) * 1000)
            items.append(
                _format_api_test_item(
                    case=case,
                    ok=True,
                    status="ok",
                    latency_ms=latency_ms,
                    detail="ok",
                    price=price,
                    yclose=yclose,
                )
            )
        except Exception as e:
            latency_ms = int((time.perf_counter() - started) * 1000)
            detail = str(e)
            is_unsupported = isinstance(e, ValueError) and "暂不支持" in detail
            items.append(
                _format_api_test_item(
                    case=case,
                    ok=False,
                    status="unsupported" if is_unsupported else "error",
                    latency_ms=latency_ms,
                    detail=detail,
                )
            )

    status_values = {str(item.get("status") or "") for item in items}
    status = "ok" if status_values <= {"ok", "unsupported"} else "degraded"
    return {
        "provider_key": provider_key,
        "provider_label": _API_TEST_PROVIDER_LABELS.get(provider_key, provider_key),
        "status": status,
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }


def _run_forex_provider_test() -> Dict[str, Any]:
    started = time.perf_counter()
    rates = get_forex_rates()
    latency_ms = int((time.perf_counter() - started) * 1000)
    usd = safe_float((rates or {}).get("USD", 0))
    hkd = safe_float((rates or {}).get("HKD", 0))
    items = [
        {
            "name": "美元兑人民币",
            "code": "USD/CNY",
            "ok": usd > 0,
            "rate": round(usd, 6),
            "latency_ms": latency_ms,
            "detail": "ok" if usd > 0 else "无有效汇率",
        },
        {
            "name": "港币兑人民币",
            "code": "HKD/CNY",
            "ok": hkd > 0,
            "rate": round(hkd, 6),
            "latency_ms": latency_ms,
            "detail": "ok" if hkd > 0 else "无有效汇率",
        },
    ]
    return {
        "provider_key": "forex_rate",
        "provider_label": _API_TEST_PROVIDER_LABELS["forex_rate"],
        "status": "ok" if all(bool(item.get("ok")) for item in items) else "degraded",
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }


def _run_provider_test_report() -> Dict[str, Any]:
    providers_payload: Dict[str, Dict[str, Any]] = {}
    tested_times: List[datetime] = []
    for provider_key in ("sina_quote", "eastmoney_quote", "tencent_quote", "forex_rate"):
        payload = (
            _run_forex_provider_test()
            if provider_key == "forex_rate"
            else _run_market_provider_test(provider_key)
        )
        providers_payload[provider_key] = payload
        raw_tested_at = str(payload.get("tested_at_utc") or "").strip()
        if not raw_tested_at:
            continue
        try:
            tested_times.append(datetime.fromisoformat(raw_tested_at))
        except Exception:
            continue

    latest_tested_at = max(tested_times).isoformat() if tested_times else datetime.now(timezone.utc).isoformat()
    return {
        "tested_at_utc": latest_tested_at,
        "summary": _provider_test_summary(providers_payload),
        "providers": providers_payload,
    }


def run_provider_test_report_job() -> Dict[str, Any]:
    payload = _run_provider_test_report()
    _save_provider_test_report_snapshot(payload)
    return payload


def _real_user_where(alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return (
        "NOT ("
        f"COALESCE({prefix}is_admin, 0) = 1 "
        f"AND LOWER(COALESCE({prefix}username, '')) LIKE 'admin_local%'"
        ")"
    )


def _has_local_anonymous_user(cursor) -> bool:
    cursor.execute(
        """
        SELECT EXISTS(
            SELECT 1 FROM portfolio WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM cash_assets WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM other_assets WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM liabilities WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM transactions WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM daily_snapshots WHERE user_id IS NULL OR TRIM(user_id) = ''
        ) AS has_local_user
        """
    )
    row = cursor.fetchone()
    return bool((row["has_local_user"] if row else 0) or 0)


def _get_user_ops_metrics(cursor) -> Dict[str, Any]:
    now_local = datetime.now()
    today_start = datetime(now_local.year, now_local.month, now_local.day, 0, 0, 0)
    tomorrow_start = today_start + timedelta(days=1)
    start_7d = today_start - timedelta(days=6)
    start_30d = today_start - timedelta(days=29)
    cutoff_1d = now_local - timedelta(days=1)
    cutoff_7d = now_local - timedelta(days=7)
    cutoff_30d = now_local - timedelta(days=30)

    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS user_total,
            SUM(CASE WHEN COALESCE(u.created_at, '') >= ? AND COALESCE(u.created_at, '') < ? THEN 1 ELSE 0 END) AS new_today,
            SUM(CASE WHEN COALESCE(u.created_at, '') >= ? AND COALESCE(u.created_at, '') < ? THEN 1 ELSE 0 END) AS new_7d,
            SUM(CASE WHEN COALESCE(u.created_at, '') >= ? AND COALESCE(u.created_at, '') < ? THEN 1 ELSE 0 END) AS new_30d,
            SUM(CASE WHEN u.last_active_at IS NULL OR TRIM(u.last_active_at) = '' THEN 1 ELSE 0 END) AS never_login,
            SUM(CASE WHEN u.last_active_at IS NOT NULL AND TRIM(u.last_active_at) != '' AND u.last_active_at >= ? THEN 1 ELSE 0 END) AS within_1d,
            SUM(CASE WHEN u.last_active_at IS NOT NULL AND TRIM(u.last_active_at) != '' AND u.last_active_at < ? AND u.last_active_at >= ? THEN 1 ELSE 0 END) AS within_7d,
            SUM(CASE WHEN u.last_active_at IS NOT NULL AND TRIM(u.last_active_at) != '' AND u.last_active_at < ? AND u.last_active_at >= ? THEN 1 ELSE 0 END) AS within_30d,
            SUM(CASE WHEN u.last_active_at IS NOT NULL AND TRIM(u.last_active_at) != '' AND u.last_active_at < ? THEN 1 ELSE 0 END) AS over_30d
        FROM users u
        WHERE {_real_user_where('u')}
        """,
        (
            today_start.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
            start_7d.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
            start_30d.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_1d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_1d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_7d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_7d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_30d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_30d.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    row = cursor.fetchone() or {}
    cursor.execute(
        f"""
        SELECT
            SUM(CASE WHEN uda.activity_date = ? THEN 1 ELSE 0 END) AS dau,
            SUM(CASE WHEN uda.activity_date >= ? AND uda.activity_date <= ? THEN 1 ELSE 0 END) AS wau,
            SUM(CASE WHEN uda.activity_date >= ? AND uda.activity_date <= ? THEN 1 ELSE 0 END) AS mau
        FROM (
            SELECT DISTINCT uda.user_id, uda.activity_date
            FROM user_daily_activity uda
            INNER JOIN users u ON u.id = uda.user_id
            WHERE {_real_user_where('u')}
              AND uda.activity_date >= ?
              AND uda.activity_date <= ?
        ) uda
        """,
        (
            today_start.strftime("%Y-%m-%d"),
            start_7d.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
            start_30d.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
            start_30d.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
        ),
    )
    active_row = cursor.fetchone() or {}
    metrics = {
        "user_total": int(row["user_total"] or 0),
        "new_today": int(row["new_today"] or 0),
        "new_7d": int(row["new_7d"] or 0),
        "new_30d": int(row["new_30d"] or 0),
        "dau": int(active_row["dau"] or 0),
        "wau": int(active_row["wau"] or 0),
        "mau": int(active_row["mau"] or 0),
        "last_login_distribution": {
            "within_1d": int(row["within_1d"] or 0),
            "within_7d": int(row["within_7d"] or 0),
            "within_30d": int(row["within_30d"] or 0),
            "over_30d": int(row["over_30d"] or 0),
            "never_login": int(row["never_login"] or 0),
        },
    }
    if _has_local_anonymous_user(cursor):
        metrics["user_total"] += 1
        metrics["last_login_distribution"]["never_login"] += 1
    return metrics


def _get_user_retention_rows(cursor, days: int = 60) -> List[Dict[str, Any]]:
    window_days = max(1, int(days))
    today_local = datetime.now()
    today_start = datetime(today_local.year, today_local.month, today_local.day, 0, 0, 0)
    tomorrow_start = today_start + timedelta(days=1)
    start_day = today_start - timedelta(days=window_days - 1)

    cursor.execute(
        f"""
        SELECT
            SUBSTR(u.created_at, 1, 10) AS cohort_date,
            COUNT(*) AS new_users,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+1 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_1d_count,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+3 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_3d_count,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+7 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_7d_count,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+14 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_14d_count,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+30 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_30d_count
        FROM users u
        WHERE {_real_user_where('u')}
          AND COALESCE(u.created_at, '') >= ?
          AND COALESCE(u.created_at, '') < ?
        GROUP BY SUBSTR(u.created_at, 1, 10)
        """,
        (
            start_day.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    cohort_rows = cursor.fetchall()

    cohort_map: Dict[str, Dict[str, int]] = {}
    for row in cohort_rows:
        cohort_date = str((row["cohort_date"] if row else "") or "")
        if not cohort_date:
            continue
        cohort_map[cohort_date] = {
            "new_users": int(row["new_users"] or 0),
            "retained_1d_count": int(row["retained_1d_count"] or 0),
            "retained_3d_count": int(row["retained_3d_count"] or 0),
            "retained_7d_count": int(row["retained_7d_count"] or 0),
            "retained_14d_count": int(row["retained_14d_count"] or 0),
            "retained_30d_count": int(row["retained_30d_count"] or 0),
        }

    cursor.execute(
        f"""
        SELECT
            uda.activity_date AS active_date,
            COUNT(DISTINCT uda.user_id) AS active_users
        FROM user_daily_activity uda
        INNER JOIN users u ON u.id = uda.user_id
        WHERE {_real_user_where('u')}
          AND uda.activity_date >= ?
          AND uda.activity_date <= ?
        GROUP BY uda.activity_date
        """,
        (
            start_day.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
        ),
    )
    active_rows = cursor.fetchall()
    active_map = {
        str((row["active_date"] if row else "") or ""): int(row["active_users"] or 0)
        for row in active_rows
        if str((row["active_date"] if row else "") or "")
    }

    cursor.execute(
        f"""
        SELECT
            uda.activity_date AS cohort_date,
            COUNT(DISTINCT uda.user_id) AS active_users,
            COUNT(
                DISTINCT CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity next_uda
                        WHERE next_uda.user_id = uda.user_id
                          AND next_uda.activity_date = DATE(uda.activity_date, '+1 day')
                    ) THEN uda.user_id
                END
            ) AS retained_1d_count,
            COUNT(
                DISTINCT CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity next_uda
                        WHERE next_uda.user_id = uda.user_id
                          AND next_uda.activity_date = DATE(uda.activity_date, '+3 day')
                    ) THEN uda.user_id
                END
            ) AS retained_3d_count,
            COUNT(
                DISTINCT CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity next_uda
                        WHERE next_uda.user_id = uda.user_id
                          AND next_uda.activity_date = DATE(uda.activity_date, '+7 day')
                    ) THEN uda.user_id
                END
            ) AS retained_7d_count,
            COUNT(
                DISTINCT CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity next_uda
                        WHERE next_uda.user_id = uda.user_id
                          AND next_uda.activity_date = DATE(uda.activity_date, '+14 day')
                    ) THEN uda.user_id
                END
            ) AS retained_14d_count
        FROM user_daily_activity uda
        INNER JOIN users u ON u.id = uda.user_id
        WHERE {_real_user_where('u')}
          AND uda.activity_date >= ?
          AND uda.activity_date <= ?
        GROUP BY uda.activity_date
        """,
        (
            start_day.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
        ),
    )
    active_cohort_rows = cursor.fetchall()
    active_cohort_map: Dict[str, Dict[str, int]] = {}
    for row in active_cohort_rows:
        cohort_date = str((row["cohort_date"] if row else "") or "")
        if not cohort_date:
            continue
        active_cohort_map[cohort_date] = {
            "active_users": int(row["active_users"] or 0),
            "retained_1d_count": int(row["retained_1d_count"] or 0),
            "retained_3d_count": int(row["retained_3d_count"] or 0),
            "retained_7d_count": int(row["retained_7d_count"] or 0),
            "retained_14d_count": int(row["retained_14d_count"] or 0),
        }

    def _safe_rate(retained: int, new_users: int, age_days: int, threshold: int):
        if new_users <= 0 or age_days < threshold:
            return None
        return round(retained / new_users, 4)

    def _safe_active_rate(retained: int, active_users: int, age_days: int, threshold: int):
        if active_users <= 0 or age_days < threshold:
            return None
        return round(retained / active_users, 4)

    today = date.today()
    result: List[Dict[str, Any]] = []
    for i in range(window_days):
        current = today - timedelta(days=i)
        date_str = current.isoformat()
        cohort = cohort_map.get(date_str, {})
        active_cohort = active_cohort_map.get(date_str, {})
        new_users = int(cohort.get("new_users", 0) or 0)
        active_users = int(active_map.get(date_str, 0) or 0)
        age_days = i
        result.append(
            {
                "date": date_str,
                "new_users": new_users,
                "active_users": active_users,
                "retention_1d": _safe_rate(int(cohort.get("retained_1d_count", 0) or 0), new_users, age_days, 1),
                "retention_3d": _safe_rate(int(cohort.get("retained_3d_count", 0) or 0), new_users, age_days, 3),
                "retention_7d": _safe_rate(int(cohort.get("retained_7d_count", 0) or 0), new_users, age_days, 7),
                "retention_14d": _safe_rate(int(cohort.get("retained_14d_count", 0) or 0), new_users, age_days, 14),
                "retention_30d": _safe_rate(int(cohort.get("retained_30d_count", 0) or 0), new_users, age_days, 30),
                "active_retention_1d": _safe_active_rate(int(active_cohort.get("retained_1d_count", 0) or 0), active_users, age_days, 1),
                "active_retention_3d": _safe_active_rate(int(active_cohort.get("retained_3d_count", 0) or 0), active_users, age_days, 3),
                "active_retention_7d": _safe_active_rate(int(active_cohort.get("retained_7d_count", 0) or 0), active_users, age_days, 7),
                "active_retention_14d": _safe_active_rate(int(active_cohort.get("retained_14d_count", 0) or 0), active_users, age_days, 14),
            }
        )
    return result


def _sort_retention_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda item: str(item.get("date") or ""))


def _build_mini_bars(
    rows: List[Dict[str, Any]],
    key: str,
    *,
    points: int = 7,
    min_height: int = 24,
) -> List[Dict[str, Any]]:
    series = _sort_retention_rows(rows)
    if points > 0:
        series = series[-points:]

    values = [int(item.get(key) or 0) for item in series]
    max_value = max(values) if values else 1
    max_value = max(max_value, 1)

    bars: List[Dict[str, Any]] = []
    for idx, item in enumerate(series):
        value = int(item.get(key) or 0)
        height_pct = max(min_height, round((value / max_value) * 100))
        bars.append(
            {
                "date": str(item.get("date") or ""),
                "value": value,
                "height": f"{height_pct}%",
                "is_latest": idx == len(series) - 1,
            }
        )
    return bars


def _build_trend_text(
    rows: List[Dict[str, Any]],
    key: str,
    *,
    unit: str,
    empty_text: str,
    single_text: str,
) -> str:
    series = _sort_retention_rows(rows)
    if not series:
        return empty_text
    if len(series) == 1:
        return single_text
    current = int(series[-1].get(key) or 0)
    previous = int(series[-2].get(key) or 0)
    diff = current - previous
    if diff == 0:
        return "较昨日持平"
    return f"较昨日 +{diff}{unit}" if diff > 0 else f"较昨日 {diff}{unit}"


def _recent_admin_audits(cursor, limit: int = 20) -> List[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT
            a.id,
            a.admin_user_id,
            COALESCE(u.username, '') AS admin_username,
            a.action,
            a.target_type,
            a.target_id,
            a.method,
            a.path,
            a.status_code,
            a.result,
            a.error,
            a.created_at
        FROM admin_audit_logs a
        LEFT JOIN users u ON u.id = a.admin_user_id
        ORDER BY a.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _get_active_session_count(cursor, user_id: str) -> int:
    cursor.execute(
        """
        SELECT COUNT(1) AS c
        FROM auth_refresh_tokens
        WHERE user_id = ?
          AND revoked_at IS NULL
          AND DATETIME(expires_at) > DATETIME('now')
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    return int((row["c"] if row else 0) or 0)


def create_admin_blueprint(db, admin_write_audit):
    global _ADMIN_DB
    _ADMIN_DB = db
    bp = Blueprint("admin_routes", __name__, url_prefix="/api/admin")
    from admin_routes_dashboard import register_admin_dashboard_routes
    from admin_routes_apis import register_admin_api_routes
    from admin_routes_config_ops import register_admin_config_ops_routes
    from admin_routes_data import register_admin_data_routes
    from admin_routes_invites import register_admin_invite_routes
    from admin_routes_users import register_admin_user_read_routes
    from admin_routes_user_write import register_admin_user_write_routes

    @bp.after_request
    def _admin_after_request(response):
        # 管理后台写操作后统一清理读缓存，保证页面手动刷新可立即看到最新状态。
        if request.method.upper() != "GET" and int(getattr(response, "status_code", 500) or 500) < 400:
            _admin_cache_clear()
        return response

    register_admin_dashboard_routes(bp, db)
    register_admin_user_read_routes(bp, db)
    register_admin_user_write_routes(bp, db, admin_write_audit)
    register_admin_config_ops_routes(bp, db, admin_write_audit)
    register_admin_data_routes(bp, db, admin_write_audit)
    register_admin_api_routes(bp, db, admin_write_audit)
    register_admin_invite_routes(bp, db, admin_write_audit)

    return bp

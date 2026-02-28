"""
管理后台 API 路由
"""
from __future__ import annotations

import importlib.util
import csv
import io
import hashlib
import json
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, g, current_app, make_response

import config
from core.auth import admin_required
from core.price import get_price_runtime_metrics, get_price_source_health
from core.snapshot import take_snapshot
from core.system import system_manager
from core.admin.user_admin import reset_user_password, revoke_user_sessions
from core.admin.policies import list_policies, update_policy, batch_update_policies
from core.policy_runtime import invalidate_policy_cache


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
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND u.last_login >= ? AND u.last_login < ? THEN 1 ELSE 0 END) AS dau,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND u.last_login >= ? AND u.last_login < ? THEN 1 ELSE 0 END) AS wau,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND u.last_login >= ? AND u.last_login < ? THEN 1 ELSE 0 END) AS mau,
            SUM(CASE WHEN u.last_login IS NULL OR TRIM(u.last_login) = '' THEN 1 ELSE 0 END) AS never_login,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND u.last_login >= ? THEN 1 ELSE 0 END) AS within_1d,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND u.last_login < ? AND u.last_login >= ? THEN 1 ELSE 0 END) AS within_7d,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND u.last_login < ? AND u.last_login >= ? THEN 1 ELSE 0 END) AS within_30d,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND u.last_login < ? THEN 1 ELSE 0 END) AS over_30d
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
    metrics = {
        "user_total": int(row["user_total"] or 0),
        "new_today": int(row["new_today"] or 0),
        "new_7d": int(row["new_7d"] or 0),
        "new_30d": int(row["new_30d"] or 0),
        "dau": int(row["dau"] or 0),
        "wau": int(row["wau"] or 0),
        "mau": int(row["mau"] or 0),
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
                    WHEN u.last_login IS NOT NULL
                         AND TRIM(u.last_login) != ''
                         AND u.last_login >= DATETIME(u.created_at, '+1 day')
                    THEN 1 ELSE 0
                END
            ) AS retained_1d_count,
            SUM(
                CASE
                    WHEN u.last_login IS NOT NULL
                         AND TRIM(u.last_login) != ''
                         AND u.last_login >= DATETIME(u.created_at, '+3 day')
                    THEN 1 ELSE 0
                END
            ) AS retained_3d_count,
            SUM(
                CASE
                    WHEN u.last_login IS NOT NULL
                         AND TRIM(u.last_login) != ''
                         AND u.last_login >= DATETIME(u.created_at, '+7 day')
                    THEN 1 ELSE 0
                END
            ) AS retained_7d_count,
            SUM(
                CASE
                    WHEN u.last_login IS NOT NULL
                         AND TRIM(u.last_login) != ''
                         AND u.last_login >= DATETIME(u.created_at, '+14 day')
                    THEN 1 ELSE 0
                END
            ) AS retained_14d_count,
            SUM(
                CASE
                    WHEN u.last_login IS NOT NULL
                         AND TRIM(u.last_login) != ''
                         AND u.last_login >= DATETIME(u.created_at, '+30 day')
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
            SUBSTR(u.last_login, 1, 10) AS active_date,
            COUNT(*) AS active_users
        FROM users u
        WHERE {_real_user_where('u')}
          AND u.last_login IS NOT NULL
          AND TRIM(u.last_login) != ''
          AND u.last_login >= ?
          AND u.last_login < ?
        GROUP BY SUBSTR(u.last_login, 1, 10)
        """,
        (
            start_day.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    active_rows = cursor.fetchall()
    active_map = {
        str((row["active_date"] if row else "") or ""): int(row["active_users"] or 0)
        for row in active_rows
        if str((row["active_date"] if row else "") or "")
    }

    def _safe_rate(retained: int, new_users: int, age_days: int, threshold: int):
        if new_users <= 0 or age_days < threshold:
            return None
        return round(retained / new_users, 4)

    today = date.today()
    result: List[Dict[str, Any]] = []
    for i in range(window_days):
        current = today - timedelta(days=i)
        date_str = current.isoformat()
        cohort = cohort_map.get(date_str, {})
        new_users = int(cohort.get("new_users", 0) or 0)
        age_days = i
        result.append(
            {
                "date": date_str,
                "new_users": new_users,
                "active_users": int(active_map.get(date_str, 0) or 0),
                "retention_1d": _safe_rate(int(cohort.get("retained_1d_count", 0) or 0), new_users, age_days, 1),
                "retention_3d": _safe_rate(int(cohort.get("retained_3d_count", 0) or 0), new_users, age_days, 3),
                "retention_7d": _safe_rate(int(cohort.get("retained_7d_count", 0) or 0), new_users, age_days, 7),
                "retention_14d": _safe_rate(int(cohort.get("retained_14d_count", 0) or 0), new_users, age_days, 14),
                "retention_30d": _safe_rate(int(cohort.get("retained_30d_count", 0) or 0), new_users, age_days, 30),
            }
        )
    return result


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
    bp = Blueprint("admin_routes", __name__, url_prefix="/api/admin")

    @bp.after_request
    def _admin_after_request(response):
        # 管理后台写操作后统一清理读缓存，保证页面手动刷新可立即看到最新状态。
        if request.method.upper() != "GET" and int(getattr(response, "status_code", 500) or 500) < 400:
            _admin_cache_clear()
        return response

    @bp.route("/overview", methods=["GET"])
    @admin_required
    def admin_overview():
        try:
            force = _admin_parse_force_arg()
        except ValueError:
            return jsonify({"error": "Invalid force"}), 400

        def _load_overview_payload() -> Dict[str, Any]:
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                user_ops = _get_user_ops_metrics(cursor)
                retention_rows = _get_user_retention_rows(cursor, days=60)

                cursor.execute("SELECT COUNT(*) AS c FROM daily_snapshots")
                snapshot_total = int(cursor.fetchone()["c"])
                cursor.execute("SELECT MAX(date) AS latest_date FROM daily_snapshots")
                latest_row = cursor.fetchone()
                latest_snapshot_date = latest_row["latest_date"] if latest_row else None

                recent_audits = _recent_admin_audits(cursor, limit=20)

                return {
                    "dashboard": {
                        "new_users_today": user_ops["new_today"],
                        "active_users_today": user_ops["dau"],
                        "total_users": user_ops["user_total"],
                    },
                    "retention_rows": retention_rows,
                    "users": {
                        "total": user_ops["user_total"],
                    },
                    "user_ops": user_ops,
                    "snapshots": {
                        "total": snapshot_total,
                        "latest_date": latest_snapshot_date,
                    },
                    "recent_audits": recent_audits,
                }
            finally:
                conn.close()

        payload, cache_state, params_hash, elapsed_ms = _admin_cached_payload(
            route_name="admin_overview",
            params={"force": request.args.get("force", "")},
            force=force,
            loader=_load_overview_payload,
        )
        _admin_log_read("admin_overview", cache_state, elapsed_ms, params_hash)
        return jsonify(payload)

    @bp.route("/meta/dictionaries", methods=["GET"])
    @admin_required
    def admin_meta_dictionaries():
        policy_labels = {
            key: value["name"] for key, value in POLICY_LABELS.items()
        }
        policy_impacts = {
            key: value["impact"] for key, value in POLICY_LABELS.items()
        }
        config_labels = {
            key: rule.get("display_name", key)
            for key, rule in CONFIG_WHITELIST.items()
        }
        return jsonify(
            {
                "status_labels": STATUS_LABELS,
                "action_labels": ACTION_LABELS,
                "policy_labels": policy_labels,
                "policy_impacts": policy_impacts,
                "policy_type_labels": POLICY_TYPE_LABELS,
                "register_method_labels": REGISTER_METHOD_LABELS,
                "error_labels": ERROR_LABELS,
                "config_labels": config_labels,
            }
        )

    @bp.route("/summary/todo", methods=["GET"])
    @admin_required
    def admin_summary_todo():
        try:
            invite_threshold = int(request.args.get("invite_threshold", 200))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid invite_threshold"}), 400
        invite_threshold = max(1, min(invite_threshold, 100000))

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(1) AS c FROM invite_codes WHERE status = 'active'")
            active_invites = int((cursor.fetchone() or {"c": 0})["c"] or 0)

            cursor.execute(
                """
                SELECT COUNT(1) AS c
                FROM admin_audit_logs
                WHERE DATE(created_at, 'localtime') = DATE('now', 'localtime')
                  AND LOWER(COALESCE(result, '')) = 'failed'
                """
            )
            failed_audits_today = int((cursor.fetchone() or {"c": 0})["c"] or 0)

            cursor.execute(
                f"""
                SELECT COUNT(1) AS c
                FROM users u
                WHERE LOWER(COALESCE(NULLIF(u.status, ''), 'active')) = 'disabled'
                  AND {_real_user_where('u')}
                """
            )
            disabled_users = int((cursor.fetchone() or {"c": 0})["c"] or 0)
        finally:
            conn.close()

        policies = db.list_admin_api_policies(scope_type="all")
        disabled_policies = [
            p for p in policies if not bool(p.get("enabled"))
        ]
        upstream = system_manager.check_api_status()
        degraded_upstream = [
            key for key, item in (upstream or {}).items()
            if not bool((item or {}).get("ok"))
        ]

        todos: List[Dict[str, Any]] = []
        if active_invites < invite_threshold:
            todos.append(
                {
                    "code": "invite_low",
                    "level": "high",
                    "title": "待发放邀请码不足",
                    "description": f"当前可用邀请码 {active_invites} 个，低于阈值 {invite_threshold} 个。",
                    "suggestion": "请尽快补充生成邀请码并安排发放。",
                }
            )
        if disabled_policies:
            names = [POLICY_LABELS.get(p["scope_key"], {}).get("name", p["scope_key"]) for p in disabled_policies]
            todos.append(
                {
                    "code": "policy_disabled",
                    "level": "medium",
                    "title": "存在已停用策略",
                    "description": f"当前有 {len(disabled_policies)} 条策略为停用状态。",
                    "suggestion": f"请确认是否符合预期：{', '.join(names[:3])}{' 等' if len(names) > 3 else ''}",
                }
            )
        if degraded_upstream:
            names = [POLICY_LABELS.get(f"upstream.{k}", {}).get("name", k) for k in degraded_upstream]
            todos.append(
                {
                    "code": "upstream_degraded",
                    "level": "high",
                    "title": "上游数据通道异常",
                    "description": f"检测到 {len(degraded_upstream)} 个通道异常。",
                    "suggestion": f"建议优先排查：{', '.join(names)}",
                }
            )
        if failed_audits_today > 0:
            todos.append(
                {
                    "code": "audit_failed",
                    "level": "medium",
                    "title": "今日存在失败操作",
                    "description": f"今日后台失败写操作 {failed_audits_today} 次。",
                    "suggestion": "请进入“操作审计”查看失败原因并处理。",
                }
            )
        if disabled_users > 0:
            todos.append(
                {
                    "code": "users_disabled",
                    "level": "low",
                    "title": "当前有停用用户",
                    "description": f"当前停用用户 {disabled_users} 人。",
                    "suggestion": "请定期核查停用状态是否仍符合运营策略。",
                }
            )
        if not todos:
            todos.append(
                {
                    "code": "all_clear",
                    "level": "ok",
                    "title": "当前无待处理异常",
                    "description": "邀请码充足、策略正常、无失败写操作。",
                    "suggestion": "可继续日常巡检。",
                }
            )

        return jsonify(
            {
                "items": todos,
                "snapshot": {
                    "active_invites": active_invites,
                    "invite_threshold": invite_threshold,
                    "disabled_policies": len(disabled_policies),
                    "degraded_upstream": len(degraded_upstream),
                    "failed_audits_today": failed_audits_today,
                    "disabled_users": disabled_users,
                },
            }
        )

    @bp.route("/users", methods=["GET"])
    @admin_required
    def admin_users():
        q = request.args.get("q", "").strip()
        status = request.args.get("status", "all").strip().lower()
        include_local_raw = request.args.get("include_local", "1")
        try:
            include_local = _coerce_bool(include_local_raw)
        except ValueError:
            return jsonify({"error": "Invalid include_local"}), 400
        limit = max(1, min(request.args.get("limit", 100, type=int), 300))
        offset = max(0, request.args.get("offset", 0, type=int))

        where = []
        params: List[Any] = []
        if q:
            where.append(
                "(bu.username LIKE ? OR COALESCE(bu.nickname, '') LIKE ? OR COALESCE(bu.phone, '') LIKE ? OR CAST(COALESCE(bu.user_number, '') AS TEXT) LIKE ? OR bu.id LIKE ?)"
            )
            q_like = f"%{q}%"
            params.extend([q_like, q_like, q_like, q_like, q_like])
        if status in {"active", "disabled"}:
            where.append("LOWER(COALESCE(NULLIF(bu.status, ''), 'active')) = ?")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        local_exists_sql = (
            "EXISTS ("
            "SELECT 1 FROM portfolio WHERE user_id IS NULL OR TRIM(user_id) = '' "
            "UNION ALL SELECT 1 FROM cash_assets WHERE user_id IS NULL OR TRIM(user_id) = '' "
            "UNION ALL SELECT 1 FROM other_assets WHERE user_id IS NULL OR TRIM(user_id) = '' "
            "UNION ALL SELECT 1 FROM liabilities WHERE user_id IS NULL OR TRIM(user_id) = '' "
            "UNION ALL SELECT 1 FROM transactions WHERE user_id IS NULL OR TRIM(user_id) = '' "
            "UNION ALL SELECT 1 FROM daily_snapshots WHERE user_id IS NULL OR TRIM(user_id) = ''"
            ")"
        )
        local_union_sql = ""
        if include_local:
            local_union_sql = f"""
                    UNION ALL
                    SELECT
                        '__local__' AS id,
                        'local_user' AS username,
                        '本机未登录用户' AS nickname,
                        '' AS phone,
                        NULL AS user_number,
                        'local_anonymous' AS register_method,
                        0 AS is_admin,
                        0 AS must_change_password,
                        'active' AS status,
                        NULL AS created_at,
                        NULL AS last_login,
                        NULL AS last_active_at,
                        '' AS last_login_ip,
                        '' AS last_login_region,
                        0 AS active_sessions,
                        COALESCE(ls_local.total_asset, 0.0) AS total_asset_cny,
                        COALESCE(ls_local.total_invest, 0.0) AS total_invest_cny,
                        0 AS can_manage
                    FROM (SELECT 1) seed
                    LEFT JOIN latest_snapshots ls_local
                      ON ls_local.uid = '' AND ls_local.rn = 1
                    WHERE {local_exists_sql}
            """
        base_users_cte_sql = f"""
                WITH latest_snapshots AS (
                    SELECT
                        COALESCE(user_id, '') AS uid,
                        total_asset,
                        total_invest,
                        ROW_NUMBER() OVER (
                            PARTITION BY COALESCE(user_id, '')
                            ORDER BY date DESC, id DESC
                        ) AS rn
                    FROM daily_snapshots
                ),
                base_users AS (
                    SELECT
                        u.id,
                        u.username,
                        COALESCE(u.nickname, '') AS nickname,
                        u.phone,
                        u.user_number,
                        COALESCE(u.register_method, '') AS register_method,
                        COALESCE(u.is_admin, 0) AS is_admin,
                        COALESCE(u.must_change_password, 0) AS must_change_password,
                        LOWER(COALESCE(NULLIF(u.status, ''), 'active')) AS status,
                        u.created_at,
                        u.last_login,
                        u.last_active_at,
                        COALESCE(u.last_login_ip, '') AS last_login_ip,
                        COALESCE(u.last_login_region, '') AS last_login_region,
                        (
                            SELECT COUNT(1)
                            FROM auth_refresh_tokens rt
                            WHERE rt.user_id = u.id
                              AND rt.revoked_at IS NULL
                              AND DATETIME(rt.expires_at) > DATETIME('now')
                        ) AS active_sessions,
                        COALESCE(ls.total_asset, 0.0) AS total_asset_cny,
                        COALESCE(ls.total_invest, 0.0) AS total_invest_cny,
                        1 AS can_manage
                    FROM users u
                    LEFT JOIN latest_snapshots ls
                      ON ls.uid = u.id AND ls.rn = 1
                    WHERE {_real_user_where("u")}
                    {local_union_sql}
                )
        """
        try:
            force = _admin_parse_force_arg()
        except ValueError:
            return jsonify({"error": "Invalid force"}), 400

        def _load_users_payload() -> Dict[str, Any]:
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    f"""
                    {base_users_cte_sql}
                    SELECT
                        bu.id,
                        bu.username,
                        bu.nickname,
                        bu.phone,
                        bu.user_number,
                        bu.register_method,
                        bu.is_admin,
                        bu.must_change_password,
                        bu.status,
                        bu.created_at,
                        bu.last_login,
                        bu.last_active_at,
                        bu.last_login_ip,
                        bu.last_login_region,
                        bu.active_sessions,
                        bu.total_asset_cny,
                        bu.total_invest_cny,
                        bu.can_manage,
                        COUNT(1) OVER() AS __total_count
                    FROM base_users bu
                    {where_sql}
                    ORDER BY COALESCE(bu.last_login, bu.created_at, '') DESC, bu.id DESC
                    LIMIT ? OFFSET ?
                    """,
                    tuple(params + [limit, offset]),
                )
                rows = cursor.fetchall()
                users: List[Dict[str, Any]] = []
                total = 0
                for row in rows:
                    item = dict(row)
                    if total <= 0:
                        total = int(item.get("__total_count") or 0)
                    item.pop("__total_count", None)
                    users.append(item)
                if not rows:
                    cursor.execute(
                        f"""
                        {base_users_cte_sql}
                        SELECT COUNT(*) AS c
                        FROM base_users bu
                        {where_sql}
                        """,
                        tuple(params),
                    )
                    total = int((cursor.fetchone() or {"c": 0})["c"] or 0)
                return {"items": users, "limit": limit, "offset": offset, "total": total}
            finally:
                conn.close()

        payload, cache_state, params_hash, elapsed_ms = _admin_cached_payload(
            route_name="admin_users",
            params={
                "q": q,
                "status": status,
                "include_local": int(include_local),
                "limit": limit,
                "offset": offset,
                "force": request.args.get("force", ""),
            },
            force=force,
            loader=_load_users_payload,
        )
        _admin_log_read("admin_users", cache_state, elapsed_ms, params_hash)
        return jsonify(payload)

    @bp.route("/users/metrics", methods=["GET"])
    @admin_required
    def admin_users_metrics():
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            metrics = _get_user_ops_metrics(cursor)
            metrics["as_of"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return jsonify(metrics)
        finally:
            conn.close()

    @bp.route("/users/<user_id>", methods=["GET"])
    @admin_required
    def admin_user_detail(user_id: str):
        uid = str(user_id or "").strip()
        if not uid:
            return jsonify({"error": "Missing user_id"}), 400
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            if uid == "__local__":
                if _has_local_anonymous_user(cursor):
                    return jsonify({
                        "id": "__local__",
                        "username": "local_user",
                        "nickname": "本机未登录用户",
                        "phone": "",
                        "user_number": None,
                        "register_method": "local_anonymous",
                        "is_admin": 0,
                        "must_change_password": 0,
                        "status": "active",
                        "created_at": None,
                        "last_login": None,
                        "last_active_at": None,
                        "last_login_ip": "",
                        "last_login_region": "",
                        "active_sessions": 0,
                        "can_manage": 0,
                    })
                return jsonify({"error": "User not found"}), 404
            cursor.execute(
                f"""
                SELECT
                    u.id,
                    u.username,
                    COALESCE(u.nickname, '') AS nickname,
                    COALESCE(u.phone, '') AS phone,
                    u.user_number,
                    COALESCE(u.register_method, '') AS register_method,
                    COALESCE(u.is_admin, 0) AS is_admin,
                    COALESCE(u.must_change_password, 0) AS must_change_password,
                    LOWER(COALESCE(NULLIF(u.status, ''), 'active')) AS status,
                    u.created_at,
                    u.last_login,
                    u.last_active_at,
                    COALESCE(u.last_login_ip, '') AS last_login_ip,
                    COALESCE(u.last_login_region, '') AS last_login_region,
                    (
                        SELECT COUNT(1)
                        FROM auth_refresh_tokens rt
                        WHERE rt.user_id = u.id
                          AND rt.revoked_at IS NULL
                          AND DATETIME(rt.expires_at) > DATETIME('now')
                    ) AS active_sessions,
                    1 AS can_manage
                FROM users u
                WHERE u.id = ? AND {_real_user_where("u")}
                LIMIT 1
                """,
                (uid,),
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "User not found"}), 404
            return jsonify(dict(row))
        finally:
            conn.close()

    @bp.route("/users/<user_id>/portfolio", methods=["GET"])
    @admin_required
    def admin_user_portfolio(user_id: str):
        uid = str(user_id or "").strip()
        if not uid:
            return jsonify({"error": "Missing user_id"}), 400
        if uid == "__local__":
            return jsonify({"error": "Local anonymous user is read-only"}), 400

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT 1
                FROM users u
                WHERE u.id = ? AND {_real_user_where("u")}
                LIMIT 1
                """,
                (uid,),
            )
            if not cursor.fetchone():
                return jsonify({"error": "User not found"}), 404
        finally:
            conn.close()

        portfolio = db.get_portfolio("all", uid)
        return jsonify(
            {
                "user_id": uid,
                "total": len(portfolio),
                "items": [
                    {
                        "code": str(item.get("code", "")),
                        "name": str(item.get("name", "")),
                        "qty": float(item.get("qty") or 0.0),
                        "price": float(item.get("price") or 0.0),
                        "curr": str(item.get("curr", "")),
                        "asset_type": str(item.get("asset_type", "")),
                    }
                    for item in portfolio
                ],
            }
        )

    @bp.route("/users/status", methods=["POST"])
    @admin_write_audit(action="admin.users.status", target_type="user")
    @admin_required
    def admin_users_status():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        status = str(data.get("status", "")).strip().lower()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if user_id == "__local__":
            return jsonify({"error": "Local anonymous user is read-only"}), 400
        if status not in {"active", "disabled"}:
            return jsonify({"error": "Invalid status"}), 400
        if status == "disabled" and user_id == g.user_id:
            return jsonify({"error": "Cannot disable current admin user"}), 400

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                UPDATE users
                SET status = ?
                WHERE id = ? AND {_real_user_where()}
                """,
                (status, user_id),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return jsonify({"error": "User not found"}), 404
            conn.commit()
            return jsonify({"status": "ok", "user_id": user_id, "new_status": status})
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @bp.route("/users/update", methods=["POST"])
    @admin_write_audit(action="admin.users.update", target_type="user")
    @admin_required
    def admin_users_update():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        updates = []
        params: List[Any] = []

        if "is_admin" in data:
            try:
                is_admin_value = 1 if _coerce_bool(data.get("is_admin")) else 0
            except ValueError:
                return jsonify({"error": "Invalid is_admin"}), 400
            if user_id == g.user_id and is_admin_value == 0:
                return jsonify({"error": "Cannot remove current admin role"}), 400
            updates.append("is_admin = ?")
            params.append(is_admin_value)

        if "status" in data:
            status = str(data.get("status", "")).strip().lower()
            if status not in {"active", "disabled"}:
                return jsonify({"error": "Invalid status"}), 400
            if status == "disabled" and user_id == g.user_id:
                return jsonify({"error": "Cannot disable current admin user"}), 400
            updates.append("status = ?")
            params.append(status)

        if not updates:
            return jsonify({"error": "No updatable fields"}), 400

        params.append(user_id)
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ? AND {_real_user_where()}",
                tuple(params),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return jsonify({"error": "User not found"}), 404
            conn.commit()
            cursor.execute(
                f"""
                SELECT id, username, nickname, phone, user_number, is_admin, must_change_password, status, created_at, last_login
                FROM users
                WHERE id = ? AND {_real_user_where()}
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            payload = dict(row) if row else {}
            if payload:
                payload["is_admin"] = bool(payload["is_admin"])
                payload["must_change_password"] = bool(payload.get("must_change_password"))
            return jsonify({"status": "ok", "user": payload})
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @bp.route("/users/disable", methods=["POST"])
    @admin_write_audit(action="admin.users.disable", target_type="user")
    @admin_required
    def admin_users_disable():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if user_id == g.user_id:
            return jsonify({"error": "Cannot disable current admin user"}), 400
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"UPDATE users SET status = 'disabled' WHERE id = ? AND {_real_user_where()}",
                (user_id,),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return jsonify({"error": "User not found"}), 404
            conn.commit()
            return jsonify({"status": "ok", "user_id": user_id, "new_status": "disabled"})
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @bp.route("/users/enable", methods=["POST"])
    @admin_write_audit(action="admin.users.enable", target_type="user")
    @admin_required
    def admin_users_enable():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"UPDATE users SET status = 'active' WHERE id = ? AND {_real_user_where()}",
                (user_id,),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return jsonify({"error": "User not found"}), 404
            conn.commit()
            return jsonify({"status": "ok", "user_id": user_id, "new_status": "active"})
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @bp.route("/users/password/reset", methods=["POST"])
    @admin_write_audit(action="admin.users.password.reset", target_type="user")
    @admin_required
    def admin_users_password_reset():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if user_id == "__local__":
            return jsonify({"error": "Local anonymous user is read-only"}), 400
        force_change = True
        if "force_change" in data:
            try:
                force_change = _coerce_bool(data.get("force_change"))
            except ValueError:
                return jsonify({"error": "Invalid force_change"}), 400
        temp_password = str(data.get("temp_password", "")).strip() or None
        payload, code = reset_user_password(
            db=db,
            user_id=user_id,
            admin_user_id=getattr(g, "user_id", "") or "",
            temp_password=temp_password,
            force_change=force_change,
        )
        return jsonify(payload), code

    @bp.route("/users/sessions/revoke", methods=["POST"])
    @admin_write_audit(action="admin.users.sessions.revoke", target_type="user")
    @admin_required
    def admin_users_sessions_revoke():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if user_id == "__local__":
            return jsonify({"error": "Local anonymous user is read-only"}), 400
        payload, code = revoke_user_sessions(db=db, user_id=user_id)
        return jsonify(payload), code

    @bp.route("/users/sessions/count", methods=["GET"])
    @admin_required
    def admin_users_sessions_count():
        user_id = request.args.get("user_id", "").strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if user_id == "__local__":
            return jsonify({"user_id": user_id, "active_sessions": 0})
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            active_sessions = _get_active_session_count(cursor, user_id)
            return jsonify({"user_id": user_id, "active_sessions": active_sessions})
        finally:
            conn.close()

    @bp.route("/config", methods=["GET"])
    @admin_required
    def admin_config():
        return jsonify({"items": _get_whitelist_configs()})

    @bp.route("/config/update", methods=["POST"])
    @admin_write_audit(action="admin.config.update", target_type="config")
    @admin_required
    def admin_config_update():
        data = _json_body()
        updates: List[Tuple[str, Any]] = []
        if isinstance(data.get("items"), list):
            for item in data["items"]:
                if not isinstance(item, dict):
                    continue
                updates.append((str(item.get("key", "")).strip(), item.get("value")))
        else:
            updates.append((str(data.get("key", "")).strip(), data.get("value")))

        if not updates:
            return jsonify({"error": "No update payload"}), 400

        updated_items = []
        for key, value in updates:
            if key not in CONFIG_WHITELIST:
                return jsonify({"error": f"Key not allowed: {key}"}), 400
            try:
                coerced = _coerce_config_value(key, value)
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            setattr(config, key, coerced)
            _RUNTIME_CONFIG_OVERRIDES[key] = coerced
            updated_items.append({"key": key, "value": coerced})

        return jsonify({"status": "ok", "updated": updated_items})

    @bp.route("/config/reset", methods=["POST"])
    @admin_write_audit(action="admin.config.reset", target_type="config")
    @admin_required
    def admin_config_reset():
        data = _json_body()
        key = str(data.get("key", "")).strip()
        if key and key not in CONFIG_WHITELIST:
            return jsonify({"error": f"Key not allowed: {key}"}), 400
        keys = [key] if key else list(CONFIG_WHITELIST.keys())
        updated_items = []
        for cfg_key in keys:
            default_value = _DEFAULT_CONFIG_VALUES.get(cfg_key)
            setattr(config, cfg_key, default_value)
            _RUNTIME_CONFIG_OVERRIDES.pop(cfg_key, None)
            updated_items.append({"key": cfg_key, "value": default_value})
        return jsonify({"status": "ok", "updated": updated_items})

    @bp.route("/data/snapshots", methods=["GET"])
    @admin_required
    def admin_data_snapshots():
        user_id = request.args.get("user_id", "").strip()
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        limit = max(1, min(request.args.get("limit", 100, type=int), 500))
        offset = max(0, request.args.get("offset", 0, type=int))

        where = []
        params: List[Any] = []
        if user_id:
            where.append("ds.user_id = ?")
            params.append(user_id)
        if start_date:
            where.append("ds.date >= ?")
            params.append(start_date)
        if end_date:
            where.append("ds.date <= ?")
            params.append(end_date)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT
                    ds.id,
                    ds.date,
                    ds.user_id,
                    COALESCE(u.username, '') AS username,
                    u.user_number AS user_number,
                    ds.total_asset,
                    ds.total_invest,
                    ds.total_cash,
                    ds.total_other,
                    ds.total_liability,
                    ds.total_pnl,
                    ds.day_pnl,
                    ds.updated_at
                FROM daily_snapshots ds
                LEFT JOIN users u ON u.id = ds.user_id
                {where_sql}
                ORDER BY ds.date DESC, ds.user_id ASC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [limit, offset]),
            )
            items = [dict(row) for row in cursor.fetchall()]
            return jsonify({"items": items, "limit": limit, "offset": offset})
        finally:
            conn.close()

    @bp.route("/data/snapshot/trigger", methods=["POST"])
    @admin_write_audit(action="admin.data.snapshot.trigger", target_type="snapshot")
    @admin_required
    def admin_data_snapshot_trigger():
        success = take_snapshot()
        if success:
            return jsonify({"status": "ok", "message": "Snapshot taken successfully"})
        return jsonify({"error": "Failed to take snapshot"}), 500

    def _parse_cleanup_markets(data: Dict[str, Any]) -> List[str]:
        raw = data.get("markets", ["a", "hk", "us", "fund"])
        if isinstance(raw, str):
            values = [part.strip() for part in raw.split(",")]
        elif isinstance(raw, list):
            values = [str(item).strip() for item in raw]
        else:
            values = []
        allowed = {"a", "hk", "us", "fund"}
        result: List[str] = []
        for value in values:
            market = value.lower()
            if market in allowed and market not in result:
                result.append(market)
        return result or ["a", "hk", "us", "fund"]

    @bp.route("/data/snapshot/cleanup_weekend", methods=["POST"])
    @admin_write_audit(action="admin.data.snapshot.cleanup_weekend", target_type="snapshot")
    @admin_required
    def admin_data_snapshot_cleanup_weekend():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        start_date = str(data.get("start_date", "")).strip()
        end_date = str(data.get("end_date", "")).strip()

        sql = """
            UPDATE daily_snapshots
            SET day_pnl = 0, updated_at = CURRENT_TIMESTAMP
            WHERE CAST(strftime('%w', date) AS INTEGER) IN (0, 6)
        """
        params: List[Any] = []
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, tuple(params))
            cleaned = cursor.rowcount
            conn.commit()
            return jsonify({"status": "ok", "cleaned": cleaned})
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @bp.route("/data/snapshot/cleanup_weekend/preview", methods=["POST"])
    @admin_required
    def admin_data_snapshot_cleanup_weekend_preview():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        start_date = str(data.get("start_date", "")).strip()
        end_date = str(data.get("end_date", "")).strip()
        sql = """
            SELECT COUNT(1) AS c
            FROM daily_snapshots
            WHERE CAST(strftime('%w', date) AS INTEGER) IN (0, 6)
        """
        params: List[Any] = []
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, tuple(params))
            row = cursor.fetchone()
            return jsonify({"status": "ok", "affected": int((row["c"] if row else 0) or 0)})
        finally:
            conn.close()

    @bp.route("/data/snapshot/cleanup_market_closed/preview", methods=["POST"])
    @admin_required
    def admin_data_snapshot_cleanup_market_closed_preview():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        start_date = str(data.get("start_date", "")).strip()
        end_date = str(data.get("end_date", "")).strip()
        markets = _parse_cleanup_markets(data)
        affected = db.preview_cleanup_market_closed(
            markets=markets,
            user_id=user_id or None,
            start_date=start_date,
            end_date=end_date,
        )
        return jsonify({"status": "ok", "affected": int(affected or 0), "markets": markets})

    @bp.route("/data/snapshot/cleanup_market_closed", methods=["POST"])
    @admin_write_audit(action="admin.data.snapshot.cleanup_market_closed", target_type="snapshot")
    @admin_required
    def admin_data_snapshot_cleanup_market_closed():
        data = _json_body()
        user_id = str(data.get("user_id", "")).strip()
        start_date = str(data.get("start_date", "")).strip()
        end_date = str(data.get("end_date", "")).strip()
        markets = _parse_cleanup_markets(data)
        cleaned = db.cleanup_market_closed_day_pnl(
            markets=markets,
            user_id=user_id or None,
            start_date=start_date,
            end_date=end_date,
        )
        return jsonify({"status": "ok", "cleaned": int(cleaned or 0), "markets": markets})

    @bp.route("/data/backup", methods=["POST"])
    @admin_write_audit(action="admin.data.backup", target_type="backup")
    @admin_required
    def admin_data_backup():
        data = _json_body()
        backup_dir = str(data.get("backup_dir", "")).strip() or str(config.BASE_DIR / "archive" / "backups")
        try:
            retention_days = int(data.get("retention_days", 14))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid retention_days"}), 400
        if retention_days < 1:
            return jsonify({"error": "retention_days must be >= 1"}), 400

        script = _load_script_module(config.BASE_DIR / "scripts" / "backup_portfolio_db.py", "backup_portfolio_db")
        backup_file = script.create_backup(str(config.DATABASE_PATH), backup_dir)
        deleted = script.prune_old_backups(backup_dir, retention_days)

        return jsonify({
            "status": "ok",
            "backup_file": backup_file,
            "backup_dir": backup_dir,
            "retention_days": retention_days,
            "deleted_count": len(deleted),
            "deleted": deleted,
        })

    @bp.route("/data/backup/latest", methods=["GET"])
    @admin_required
    def admin_data_backup_latest():
        backup_dir = request.args.get("backup_dir", "").strip() or str(config.BASE_DIR / "archive" / "backups")
        script = _load_script_module(config.BASE_DIR / "scripts" / "restore_portfolio_db.py", "restore_portfolio_db")
        try:
            latest = script.find_latest_backup(backup_dir)
            latest_path = Path(latest)
            return jsonify(
                {
                    "status": "ok",
                    "backup_file": latest,
                    "backup_dir": backup_dir,
                    "modified_at": datetime.fromtimestamp(
                        latest_path.stat().st_mtime, timezone.utc
                    ).isoformat(),
                    "size_bytes": latest_path.stat().st_size,
                }
            )
        except FileNotFoundError:
            return jsonify({"status": "ok", "backup_file": "", "backup_dir": backup_dir})

    @bp.route("/data/restore", methods=["POST"])
    @admin_write_audit(action="admin.data.restore", target_type="backup")
    @admin_required
    def admin_data_restore():
        data = _json_body()
        backup_dir = str(data.get("backup_dir", "")).strip() or str(config.BASE_DIR / "archive" / "backups")
        backup_file = str(data.get("backup_file", "")).strip()

        script = _load_script_module(config.BASE_DIR / "scripts" / "restore_portfolio_db.py", "restore_portfolio_db")
        try:
            if not backup_file:
                backup_file = script.find_latest_backup(backup_dir)
            result = script.restore_backup(str(config.DATABASE_PATH), backup_file)
            return jsonify(result)
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/apis/health", methods=["GET"])
    @admin_required
    def admin_apis_health():
        db_ok = True
        db_error = ""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        except Exception as e:
            db_ok = False
            db_error = str(e)
        finally:
            conn.close()

        upstream = system_manager.check_api_status()
        upstream_ok = all(item.get("ok") for item in upstream.values()) if upstream else True
        policies = db.list_admin_api_policies(scope_type="all")
        for policy in policies:
            policy["enabled"] = bool(policy.get("enabled"))
            scope_key = str(policy.get("scope_key", ""))
            policy["display_name"] = POLICY_LABELS.get(scope_key, {}).get("name", scope_key)
            policy["impact"] = POLICY_LABELS.get(scope_key, {}).get("impact", "")
            policy["scope_type_label"] = POLICY_TYPE_LABELS.get(
                str(policy.get("scope_type", "")), str(policy.get("scope_type", ""))
            )

        payload = {
            "status": "ok" if (db_ok and upstream_ok) else "degraded",
            "server_time_utc": datetime.now(timezone.utc).isoformat(),
            "db": {"ok": db_ok, "error": db_error},
            "upstream": upstream,
            "policies": policies,
            "runtime": get_price_runtime_metrics(),
            "sources": get_price_source_health(),
            "version_info": system_manager.get_version_info(),
        }
        return jsonify(payload)

    @bp.route("/apis/policies", methods=["GET"])
    @admin_required
    def admin_apis_policies():
        scope_type = request.args.get("scope_type", "all").strip().lower()
        payload = list_policies(db, scope_type=scope_type)
        for item in payload.get("items", []):
            scope_key = str(item.get("scope_key", ""))
            item["display_name"] = POLICY_LABELS.get(scope_key, {}).get("name", scope_key)
            item["impact"] = POLICY_LABELS.get(scope_key, {}).get("impact", "")
            item["scope_type_label"] = POLICY_TYPE_LABELS.get(
                str(item.get("scope_type", "")), str(item.get("scope_type", ""))
            )
        return jsonify(payload)

    @bp.route("/apis/policies/update", methods=["POST"])
    @admin_write_audit(action="admin.apis.policies.update", target_type="policy")
    @admin_required
    def admin_apis_policies_update():
        data = _json_body()
        scope_key = str(data.get("scope_key", "")).strip()
        if not scope_key:
            return jsonify({"error": "Missing scope_key"}), 400
        payload, code = update_policy(
            db=db,
            scope_key=scope_key,
            payload=data,
            updated_by=getattr(g, "user_id", "") or "",
        )
        if code == 200:
            invalidate_policy_cache(scope_key)
        return jsonify(payload), code

    @bp.route("/apis/policies/batch_update", methods=["POST"])
    @admin_write_audit(action="admin.apis.policies.batch_update", target_type="policy")
    @admin_required
    def admin_apis_policies_batch_update():
        data = _json_body()
        items = data.get("items")
        payload, code = batch_update_policies(
            db=db,
            items=items if isinstance(items, list) else [],
            updated_by=getattr(g, "user_id", "") or "",
        )
        if code == 200:
            invalidate_policy_cache()
        return jsonify(payload), code

    @bp.route("/apis/smoke_test", methods=["POST"])
    @admin_write_audit(action="admin.apis.smoke_test", target_type="system")
    @admin_required
    def admin_apis_smoke_test():
        results: List[Dict[str, Any]] = []

        def run_case(name: str, fn):
            try:
                detail = fn()
                results.append({"name": name, "ok": True, "detail": detail})
            except Exception as e:
                results.append({"name": name, "ok": False, "error": str(e)})

        def _health_case():
            with current_app.test_client() as client:
                resp = client.get("/health")
                if resp.status_code != 200:
                    raise RuntimeError(f"health status_code={resp.status_code}")
                body = resp.get_json(silent=True) or {}
                if body.get("status") != "ok":
                    raise RuntimeError(f"health payload={body}")
                return {"status_code": resp.status_code, "payload": body}

        def _db_case():
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) AS c FROM users")
                row = cursor.fetchone()
                return {"users_count": int(row["c"])}
            finally:
                conn.close()

        def _upstream_case():
            return system_manager.check_api_status()

        def _runtime_case():
            return {"runtime": get_price_runtime_metrics(), "sources": get_price_source_health()}

        run_case("health", _health_case)
        run_case("db", _db_case)
        run_case("upstream", _upstream_case)
        run_case("runtime", _runtime_case)

        all_ok = all(item.get("ok") for item in results)
        return jsonify({"status": "ok" if all_ok else "degraded", "items": results})

    @bp.route("/invites/generate", methods=["POST"])
    @admin_write_audit(action="admin.invites.generate", target_type="invite")
    @admin_required
    def admin_invites_generate():
        data = _json_body()
        try:
            count = int(data.get("count", 1000))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid count"}), 400
        if count < 1 or count > 10000:
            return jsonify({"error": "count must be 1-10000"}), 400
        batch_id = str(data.get("batch_id", "")).strip() or datetime.now().strftime("batch-%Y%m%d-%H%M%S")
        note = str(data.get("note", "")).strip()[:200]

        target = count
        inserted_total = 0
        generated_all: List[str] = []
        safety_rounds = 0
        while inserted_total < target and safety_rounds < 8:
            missing = target - inserted_total
            generated = []
            seen = set()
            while len(generated) < missing:
                code = _make_invite_code(10)
                if code in seen:
                    continue
                seen.add(code)
                generated.append(code)
            inserted = db.insert_invite_codes(
                generated,
                batch_id=batch_id,
                created_by=getattr(g, "user_id", "") or "",
                note=note,
            )
            inserted_total += inserted
            generated_all.extend(generated[:inserted])
            safety_rounds += 1

        return jsonify({
            "status": "ok",
            "batch_id": batch_id,
            "requested": target,
            "inserted": inserted_total,
            "codes": generated_all[:inserted_total],
        })

    @bp.route("/invites", methods=["GET"])
    @admin_required
    def admin_invites_list():
        status = request.args.get("status", "all").strip().lower()
        batch_id = request.args.get("batch_id", "").strip()
        limit = max(1, min(request.args.get("limit", 200, type=int), 2000))
        offset = max(0, request.args.get("offset", 0, type=int))
        try:
            force = _admin_parse_force_arg()
        except ValueError:
            return jsonify({"error": "Invalid force"}), 400

        payload, cache_state, params_hash, elapsed_ms = _admin_cached_payload(
            route_name="admin_invites",
            params={
                "status": status,
                "batch_id": batch_id,
                "limit": limit,
                "offset": offset,
                "force": request.args.get("force", ""),
            },
            force=force,
            loader=lambda: db.list_invite_codes(status=status, batch_id=batch_id, limit=limit, offset=offset),
        )
        _admin_log_read("admin_invites", cache_state, elapsed_ms, params_hash)
        return jsonify(payload)

    @bp.route("/invites/stats", methods=["GET"])
    @admin_required
    def admin_invites_stats():
        batch_id = request.args.get("batch_id", "").strip()
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            params: List[Any] = []
            where = ""
            if batch_id:
                where = "WHERE batch_id = ?"
                params.append(batch_id)
            cursor.execute(
                f"""
                SELECT
                    COUNT(1) AS total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
                    SUM(CASE WHEN status = 'used' THEN 1 ELSE 0 END) AS used,
                    SUM(CASE WHEN status = 'revoked' THEN 1 ELSE 0 END) AS revoked
                FROM invite_codes
                {where}
                """,
                tuple(params),
            )
            row = cursor.fetchone() or {}
            return jsonify(
                {
                    "total": int(row["total"] or 0),
                    "active": int(row["active"] or 0),
                    "used": int(row["used"] or 0),
                    "revoked": int(row["revoked"] or 0),
                    "batch_id": batch_id,
                }
            )
        finally:
            conn.close()

    @bp.route("/invites/revoke", methods=["POST"])
    @admin_write_audit(action="admin.invites.revoke", target_type="invite")
    @admin_required
    def admin_invites_revoke():
        data = _json_body()
        code = str(data.get("code", "")).strip().upper()
        if not code:
            return jsonify({"error": "Missing code"}), 400
        if not db.revoke_invite_code(code):
            return jsonify({"error": "Invite code not active or not found"}), 404
        return jsonify({"status": "ok", "code": code})

    @bp.route("/invites/export", methods=["GET"])
    @admin_required
    def admin_invites_export():
        status = request.args.get("status", "all").strip().lower()
        batch_id = request.args.get("batch_id", "").strip()
        payload = db.list_invite_codes(status=status, batch_id=batch_id, limit=50000, offset=0)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "邀请码",
                "批次标识",
                "状态",
                "创建人",
                "创建时间",
                "使用用户名",
                "使用用户编号",
                "使用用户内部ID",
                "使用时间",
                "备注",
            ]
        )
        for item in payload.get("items", []):
            writer.writerow([
                item.get("code", ""),
                item.get("batch_id", ""),
                STATUS_LABELS.get(str(item.get("status", "")).lower(), item.get("status", "")),
                item.get("created_by", ""),
                item.get("created_at", ""),
                item.get("used_by_username", ""),
                item.get("used_by_user_number", ""),
                item.get("used_by_user_id", ""),
                item.get("used_at", ""),
                item.get("note", ""),
            ])
        csv_content = output.getvalue()
        resp = make_response(csv_content)
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        filename = batch_id or "all"
        resp.headers["Content-Disposition"] = f"attachment; filename=invites-{filename}.csv"
        return resp

    @bp.route("/data/rebind/preview", methods=["GET"])
    @admin_required
    def admin_data_rebind_preview():
        target_user_id = request.args.get("target_user_id", "").strip()
        if not target_user_id:
            return jsonify({"error": "Missing target_user_id"}), 400
        payload = db.preview_rebind_to_user(target_user_id)
        if payload.get("error"):
            return jsonify(payload), 404
        return jsonify(payload)

    @bp.route("/data/rebind/execute", methods=["POST"])
    @admin_write_audit(action="admin.data.rebind.execute", target_type="user")
    @admin_required
    def admin_data_rebind_execute():
        data = _json_body()
        target_user_id = str(data.get("target_user_id", "")).strip()
        if not target_user_id:
            return jsonify({"error": "Missing target_user_id"}), 400
        payload = db.execute_rebind_to_user(target_user_id)
        if payload.get("error"):
            return jsonify(payload), 400
        return jsonify({"status": "ok", "result": payload})

    @bp.route("/audit/logs", methods=["GET"])
    @admin_required
    def admin_audit_logs():
        action = request.args.get("action", "").strip()
        admin_user_id = request.args.get("admin_user_id", "").strip()
        result_filter = request.args.get("result", "").strip().lower()
        start_time = request.args.get("start_time", "").strip()
        end_time = request.args.get("end_time", "").strip()
        limit = max(1, min(request.args.get("limit", 100, type=int), 500))
        offset = max(0, request.args.get("offset", 0, type=int))

        where = []
        params: List[Any] = []
        if action:
            where.append("a.action = ?")
            params.append(action)
        if admin_user_id:
            where.append("a.admin_user_id = ?")
            params.append(admin_user_id)
        if result_filter in {"success", "failed"}:
            where.append("LOWER(COALESCE(a.result, '')) = ?")
            params.append(result_filter)
        if start_time:
            where.append("DATETIME(a.created_at) >= DATETIME(?)")
            params.append(start_time)
        if end_time:
            where.append("DATETIME(a.created_at) <= DATETIME(?)")
            params.append(end_time)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        try:
            force = _admin_parse_force_arg()
        except ValueError:
            return jsonify({"error": "Invalid force"}), 400

        def _load_audit_payload() -> Dict[str, Any]:
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    f"""
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
                        a.request_body,
                        a.created_at,
                        COUNT(1) OVER() AS __total_count
                    FROM admin_audit_logs a
                    LEFT JOIN users u ON u.id = a.admin_user_id
                    {where_sql}
                    ORDER BY a.id DESC
                    LIMIT ? OFFSET ?
                    """,
                    tuple(params + [limit, offset]),
                )
                rows = cursor.fetchall()
                total = 0
                items: List[Dict[str, Any]] = []
                for row in rows:
                    item = dict(row)
                    if total <= 0:
                        total = int(item.get("__total_count") or 0)
                    item.pop("__total_count", None)
                    items.append(item)
                if not rows:
                    cursor.execute(
                        f"""
                        SELECT COUNT(1) AS c
                        FROM admin_audit_logs a
                        {where_sql}
                        """,
                        tuple(params),
                    )
                    total = int((cursor.fetchone() or {"c": 0})["c"] or 0)
                return {"items": items, "limit": limit, "offset": offset, "total": total}
            finally:
                conn.close()

        payload, cache_state, params_hash, elapsed_ms = _admin_cached_payload(
            route_name="admin_audit_logs",
            params={
                "action": action,
                "admin_user_id": admin_user_id,
                "result": result_filter,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit,
                "offset": offset,
                "force": request.args.get("force", ""),
            },
            force=force,
            loader=_load_audit_payload,
        )
        _admin_log_read("admin_audit_logs", cache_state, elapsed_ms, params_hash)
        return jsonify(payload)

    @bp.route("/audit/export", methods=["GET"])
    @admin_required
    def admin_audit_export():
        action = request.args.get("action", "").strip()
        admin_user_id = request.args.get("admin_user_id", "").strip()
        result_filter = request.args.get("result", "").strip().lower()
        start_time = request.args.get("start_time", "").strip()
        end_time = request.args.get("end_time", "").strip()

        where = []
        params: List[Any] = []
        if action:
            where.append("a.action = ?")
            params.append(action)
        if admin_user_id:
            where.append("a.admin_user_id = ?")
            params.append(admin_user_id)
        if result_filter in {"success", "failed"}:
            where.append("LOWER(COALESCE(a.result, '')) = ?")
            params.append(result_filter)
        if start_time:
            where.append("DATETIME(a.created_at) >= DATETIME(?)")
            params.append(start_time)
        if end_time:
            where.append("DATETIME(a.created_at) <= DATETIME(?)")
            params.append(end_time)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT
                    a.id,
                    a.created_at,
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
                    a.request_body
                FROM admin_audit_logs a
                LEFT JOIN users u ON u.id = a.admin_user_id
                {where_sql}
                ORDER BY a.id DESC
                LIMIT 10000
                """,
                tuple(params),
            )
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "时间",
                "操作人",
                "操作人内部ID",
                "操作内容",
                "对象类型",
                "对象标识",
                "结果",
                "失败原因",
                "请求方法",
                "请求路径",
                "状态码",
                "请求体",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.get("created_at", ""),
                    row.get("admin_username", ""),
                    row.get("admin_user_id", ""),
                    ACTION_LABELS.get(row.get("action", ""), row.get("action", "")),
                    row.get("target_type", ""),
                    row.get("target_id", ""),
                    "成功" if str(row.get("result", "")).lower() == "success" else "失败",
                    row.get("error", ""),
                    row.get("method", ""),
                    row.get("path", ""),
                    row.get("status_code", ""),
                    row.get("request_body", ""),
                ]
            )
        resp = make_response(output.getvalue())
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = (
            f"attachment; filename=audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        )
        return resp

    return bp

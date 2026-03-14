"""请求运行时基础设施。

负责承接：
- 认证安全审计
- API 分组策略与限流
- 用户活跃打点
- 后台写操作审计
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict

from flask import Flask, g, jsonify, make_response, request


_PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/api/auth/password/change",
    "/api/auth/logout",
    "/api/auth/me",
}
_ACTIVITY_TOUCH_STALE_SECONDS = 3600.0


class RequestRuntime:
    """承接 Flask 请求前后钩子和审计逻辑。"""

    def __init__(
        self,
        *,
        db: Any,
        logger: logging.Logger,
        client_ip_getter: Callable[[], str],
        resolve_ip_region: Callable[[str], str],
        verify_token: Callable[[str], tuple[bool, Dict[str, Any]]],
        is_policy_enabled: Callable[..., bool],
        get_policy_limit_per_min: Callable[[str], int],
        time_getter: Callable[[], float] | None = None,
        activity_touch_interval_seconds: float = 30.0,
    ) -> None:
        self.db = db
        self.logger = logger
        self.client_ip_getter = client_ip_getter
        self.resolve_ip_region = resolve_ip_region
        self.verify_token = verify_token
        self.is_policy_enabled = is_policy_enabled
        self.get_policy_limit_per_min = get_policy_limit_per_min
        self.time_getter = time_getter or time.time
        self.activity_touch_interval_seconds = activity_touch_interval_seconds

        self._policy_rate_lock = threading.Lock()
        self._policy_rate_counters: Dict[tuple[str, str, int], int] = defaultdict(int)
        self._activity_touch_lock = threading.Lock()
        self._activity_touch_last_ts: Dict[str, float] = {}

    def register_hooks(self, app: Flask) -> None:
        app.before_request(self.enforce_api_group_policy)
        app.after_request(self.mark_user_recent_activity)

    def mask_username(self, username: str) -> str:
        """用户名脱敏，避免日志暴露完整标识。"""
        value = (username or "").strip().lower()
        if not value:
            return ""
        if len(value) <= 2:
            return f"{value[0]}*"
        return f"{value[:2]}***"

    def auth_audit(
        self,
        event: str,
        outcome: str,
        username: str = "",
        reason: str = "",
        level: str = "info",
    ) -> None:
        """认证相关安全审计日志。"""
        message = (
            f"SECURITY event={event} outcome={outcome} "
            f"ip={self.client_ip_getter()} username={self.mask_username(username)} reason={reason} "
            f"path={request.path} ua={request.headers.get('User-Agent', '-')[:120]}"
        )
        if level == "warning":
            self.logger.warning(message)
            return
        self.logger.info(message)

    def resolve_api_policy_scope(self, path: str) -> str:
        value = (path or "").strip()
        if value.startswith("/api/auth/"):
            return "api.auth"
        if value.startswith("/api/news"):
            return "api.news"
        if value.startswith(
            (
                "/api/portfolio",
                "/api/cash_assets",
                "/api/other_assets",
                "/api/liabilities",
                "/api/transactions",
                "/api/history",
                "/api/analysis",
                "/api/snapshot",
            )
        ):
            return "api.portfolio"
        return ""

    def apply_policy_rate_limit(self, scope_key: str, limit_per_min: int) -> bool:
        if limit_per_min <= 0:
            return True
        now_minute = int(self.time_getter() // 60)
        key = (scope_key, self.client_ip_getter(), now_minute)
        with self._policy_rate_lock:
            stale_keys = [item for item in self._policy_rate_counters.keys() if item[2] < now_minute - 1]
            for stale_key in stale_keys:
                self._policy_rate_counters.pop(stale_key, None)
            self._policy_rate_counters[key] += 1
            return self._policy_rate_counters[key] <= limit_per_min

    def should_touch_user_activity(self, user_id: str) -> bool:
        value = str(user_id or "").strip()
        if not value:
            return False
        now_ts = self.time_getter()
        with self._activity_touch_lock:
            stale_keys = [
                uid
                for uid, last_ts in self._activity_touch_last_ts.items()
                if (now_ts - last_ts) > _ACTIVITY_TOUCH_STALE_SECONDS
            ]
            for stale_key in stale_keys:
                self._activity_touch_last_ts.pop(stale_key, None)
            last_ts = self._activity_touch_last_ts.get(value, 0.0)
            if (now_ts - last_ts) < self.activity_touch_interval_seconds:
                return False
            self._activity_touch_last_ts[value] = now_ts
            return True

    def enforce_api_group_policy(self):
        path = request.path or ""
        if not path.startswith("/api/"):
            return None
        if path.startswith("/api/admin/"):
            return None

        scope_key = self.resolve_api_policy_scope(path)
        if not scope_key:
            return None

        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            valid, payload = self.verify_token(parts[1])
            if valid and payload and payload.get("user_id"):
                user = self.db.get_user_by_id(payload.get("user_id"))
                if user and str(user.get("status") or "active").lower() != "active":
                    return jsonify({"error": "账号已停用，请联系管理员"}), 403
                if user and bool(user.get("must_change_password")) and path not in _PASSWORD_CHANGE_ALLOWED_PATHS:
                    return (
                        jsonify(
                            {
                                "error": "需要先修改密码后再继续操作",
                                "code": "PASSWORD_CHANGE_REQUIRED",
                            }
                        ),
                        403,
                    )

        if not self.is_policy_enabled(scope_key, default=True):
            return (
                jsonify(
                    {
                        "error": "Service temporarily disabled",
                        "code": "API_SCOPE_DISABLED",
                        "scope_key": scope_key,
                    }
                ),
                503,
            )

        limit_per_min = self.get_policy_limit_per_min(scope_key)
        if limit_per_min and not self.apply_policy_rate_limit(scope_key, limit_per_min):
            return (
                jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "code": "API_SCOPE_RATE_LIMITED",
                        "scope_key": scope_key,
                    }
                ),
                429,
            )
        return None

    def mark_user_recent_activity(self, response):
        try:
            path = request.path or ""
            if not path.startswith("/api/") or path.startswith("/api/admin/"):
                return response
            if request.method == "OPTIONS":
                return response
            user_id = str(getattr(g, "user_id", "") or "").strip()
            if not user_id:
                return response
            if self.should_touch_user_activity(user_id):
                active_ip = self.client_ip_getter()
                self.db.update_last_active(
                    user_id,
                    active_ip=active_ip,
                    active_region=self.resolve_ip_region(active_ip),
                )
        except Exception as exc:
            self.logger.debug("update last active failed: %s", exc)
        return response

    def record_admin_audit(
        self,
        *,
        action: str,
        status_code: int,
        result: str,
        target_type: str = "",
        target_id: str = "",
        error: str = "",
    ) -> None:
        """写入后台审计日志。"""
        try:
            payload = request.get_json(silent=True)
            request_body = json.dumps(payload, ensure_ascii=False)[:4000] if payload is not None else ""
            admin_user_id = getattr(g, "user_id", "") or ""
            self.db.add_admin_audit_log(
                admin_user_id=admin_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                method=request.method,
                path=request.path,
                ip=self.client_ip_getter(),
                request_body=request_body,
                status_code=status_code,
                result=result,
                error=(error or "")[:500],
            )
        except Exception as exc:
            self.logger.error("Failed to record admin audit: %s", exc)

    def admin_write_audit(self, action: str, target_type: str = ""):
        """后台写操作审计装饰器。"""

        def decorator(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                payload = request.get_json(silent=True) or {}
                target_id = ""
                if isinstance(payload, dict):
                    for key in ("id", "user_id", "key", "date"):
                        if payload.get(key) is not None:
                            target_id = str(payload.get(key))[:128]
                            break
                try:
                    response = func(*args, **kwargs)
                    flask_response = make_response(response)
                    status_code = flask_response.status_code
                    result = "success" if 200 <= status_code < 400 else "failed"
                    error = ""
                    if status_code >= 400:
                        body = flask_response.get_json(silent=True) or {}
                        if isinstance(body, dict):
                            error = str(body.get("error", ""))[:500]
                    self.record_admin_audit(
                        action=action,
                        target_type=target_type,
                        target_id=target_id,
                        status_code=status_code,
                        result=result,
                        error=error,
                    )
                    return response
                except Exception as exc:
                    self.record_admin_audit(
                        action=action,
                        target_type=target_type,
                        target_id=target_id,
                        status_code=500,
                        result="failed",
                        error=str(exc),
                    )
                    raise

            return wrapped

        return decorator


def create_request_runtime(**kwargs) -> RequestRuntime:
    return RequestRuntime(**kwargs)

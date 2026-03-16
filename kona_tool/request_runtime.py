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
import uuid
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict

try:  # pragma: no cover - 运行时可选依赖
    import redis
except Exception:  # pragma: no cover
    redis = None

from flask import Flask, g, jsonify, make_response, request


_PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/api/auth/password/change",
    "/api/auth/logout",
    "/api/auth/me",
}
_ACTIVITY_TOUCH_STALE_SECONDS = 3600.0
_POLICY_RATE_TTL_SECONDS = 120
_DEFAULT_STORAGE_PREFIX = "kona:req"


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
        storage_url: str = "memory://",
        storage_prefix: str = _DEFAULT_STORAGE_PREFIX,
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
        self._metrics_lock = threading.Lock()
        self._metrics: Dict[str, Any] = {
            "policy_rate_allowed": 0,
            "policy_rate_limited": 0,
            "policy_rate_errors": 0,
            "activity_touch_write": 0,
            "activity_touch_skipped": 0,
            "activity_touch_errors": 0,
            "storage_errors": 0,
            "last_error": "",
            "last_error_at": None,
        }

        self.storage_url = str(storage_url or "memory://").strip() or "memory://"
        self.storage_prefix = str(storage_prefix or _DEFAULT_STORAGE_PREFIX).strip() or _DEFAULT_STORAGE_PREFIX
        self._storage_backend = "memory"
        self._redis_client = None
        self._activity_touch_script = None
        self._init_shared_storage()

    def register_hooks(self, app: Flask) -> None:
        app.before_request(self.attach_request_trace_context)
        app.before_request(self.enforce_api_group_policy)
        app.after_request(self.mark_user_recent_activity)
        app.after_request(self.finalize_request_trace)

    def _normalize_request_id(self, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        safe = "".join(ch for ch in text if ch.isalnum() or ch in ("-", "_", ".", ":"))
        return safe[:80]

    def _new_request_id(self) -> str:
        return f"req-{uuid.uuid4().hex[:20]}"

    def current_request_id(self) -> str:
        return str(getattr(g, "request_id", "") or "").strip()

    def attach_request_trace_context(self):
        incoming = self._normalize_request_id(
            request.headers.get("X-Request-Id") or request.headers.get("X-Request-ID") or ""
        )
        g.request_id = incoming or self._new_request_id()
        g.request_started_at = self.time_getter()
        return None

    def _init_shared_storage(self) -> None:
        url = self.storage_url
        if not url or url == "memory://":
            return
        if not (url.startswith("redis://") or url.startswith("rediss://")):
            self.logger.info("request runtime storage fallback: unsupported url=%s", url)
            return
        if redis is None:
            self.logger.warning("request runtime storage fallback: redis library not available")
            self._metric_inc("storage_errors")
            return
        try:
            client = redis.Redis.from_url(url, decode_responses=True)
            client.ping()
        except Exception as exc:  # pragma: no cover
            self.logger.warning("request runtime storage fallback: redis unavailable: %s", exc)
            self._metric_error("storage_errors", exc)
            return
        self._redis_client = client
        self._storage_backend = "redis"

    def _metric_inc(self, key: str, inc: int = 1) -> None:
        with self._metrics_lock:
            self._metrics[key] = int(self._metrics.get(key, 0)) + inc

    def _metric_error(self, key: str, exc: Exception | None = None) -> None:
        self._metric_inc(key)
        if exc is None:
            return
        with self._metrics_lock:
            self._metrics["last_error"] = str(exc)
            self._metrics["last_error_at"] = self.time_getter()

    def _policy_rate_key(self, scope_key: str, ip: str, minute: int) -> str:
        return f"{self.storage_prefix}:policy:{scope_key}:{ip}:{minute}"

    def _activity_touch_key(self, user_id: str) -> str:
        return f"{self.storage_prefix}:active:{user_id}"

    def _touch_user_activity_redis(self, user_id: str) -> bool | None:
        if self._redis_client is None:
            return None
        now_ts = int(self.time_getter())
        ttl_seconds = int(
            max(_ACTIVITY_TOUCH_STALE_SECONDS, self.activity_touch_interval_seconds * 2)
        )
        if self._activity_touch_script is None:
            script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local interval = tonumber(ARGV[2])
            local ttl = tonumber(ARGV[3])
            local last = redis.call("GET", key)
            if not last then
                redis.call("SET", key, now, "EX", ttl)
                return 1
            end
            if (now - tonumber(last)) >= interval then
                redis.call("SET", key, now, "EX", ttl)
                return 1
            end
            return 0
            """
            self._activity_touch_script = self._redis_client.register_script(script)
        try:
            result = self._activity_touch_script(
                keys=[self._activity_touch_key(user_id)],
                args=[now_ts, self.activity_touch_interval_seconds, ttl_seconds],
            )
            return bool(int(result))
        except Exception as exc:
            self._metric_error("activity_touch_errors", exc)
            self.logger.debug("activity touch redis failed: %s", exc)
            return None

    def get_runtime_metrics(self) -> Dict[str, Any]:
        with self._metrics_lock:
            metrics = dict(self._metrics)
        metrics["storage"] = {
            "backend": self._storage_backend,
            "shared": self._storage_backend == "redis",
        }
        metrics["activity_touch_interval_seconds"] = self.activity_touch_interval_seconds
        metrics["policy_rate_ttl_seconds"] = _POLICY_RATE_TTL_SECONDS
        return metrics

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
            f"path={request.path} request_id={self.current_request_id() or '-'} "
            f"ua={request.headers.get('User-Agent', '-')[:120]}"
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
        client_ip = self.client_ip_getter()

        if self._storage_backend == "redis" and self._redis_client is not None:
            redis_key = self._policy_rate_key(scope_key, client_ip, now_minute)
            try:
                current = self._redis_client.incr(redis_key)
                if current == 1:
                    self._redis_client.expire(redis_key, _POLICY_RATE_TTL_SECONDS)
                allowed = current <= limit_per_min
                if allowed:
                    self._metric_inc("policy_rate_allowed")
                else:
                    self._metric_inc("policy_rate_limited")
                return allowed
            except Exception as exc:
                self._metric_error("policy_rate_errors", exc)
                self.logger.debug("policy rate redis failed: %s", exc)

        key = (scope_key, client_ip, now_minute)
        with self._policy_rate_lock:
            stale_keys = [item for item in self._policy_rate_counters.keys() if item[2] < now_minute - 1]
            for stale_key in stale_keys:
                self._policy_rate_counters.pop(stale_key, None)
            self._policy_rate_counters[key] += 1
            allowed = self._policy_rate_counters[key] <= limit_per_min
            if allowed:
                self._metric_inc("policy_rate_allowed")
            else:
                self._metric_inc("policy_rate_limited")
            return allowed

    def should_touch_user_activity(self, user_id: str) -> bool:
        value = str(user_id or "").strip()
        if not value:
            return False
        if self._storage_backend == "redis" and self._redis_client is not None:
            touched = self._touch_user_activity_redis(value)
            if touched is not None:
                if touched:
                    self._metric_inc("activity_touch_write")
                else:
                    self._metric_inc("activity_touch_skipped")
                return touched

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
                self._metric_inc("activity_touch_skipped")
                return False
            self._activity_touch_last_ts[value] = now_ts
            self._metric_inc("activity_touch_write")
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

    def finalize_request_trace(self, response):
        request_id = self.current_request_id() or self._new_request_id()
        response.headers["X-Request-Id"] = request_id

        path = request.path or ""
        if not path.startswith("/api/"):
            return response

        started_at = float(getattr(g, "request_started_at", self.time_getter()) or self.time_getter())
        duration_ms = max(0, int(round((self.time_getter() - started_at) * 1000)))
        user_id = str(getattr(g, "user_id", "") or "").strip() or "-"
        self.logger.info(
            "REQUEST request_id=%s method=%s path=%s status=%s duration_ms=%s user_id=%s ip=%s",
            request_id,
            request.method,
            path,
            int(getattr(response, "status_code", 0) or 0),
            duration_ms,
            user_id,
            self.client_ip_getter(),
        )
        return response

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

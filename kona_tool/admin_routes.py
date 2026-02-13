"""
管理后台 API 路由
"""
from __future__ import annotations

import importlib.util
import csv
import io
import secrets
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g, current_app, make_response

import config
from core.auth import admin_required
from core.price import get_price_runtime_metrics, get_price_source_health
from core.snapshot import take_snapshot
from core.system import system_manager


CONFIG_WHITELIST: Dict[str, Dict[str, Any]] = {
    "API_TIMEOUT": {"type": "int", "min": 1, "max": 30, "description": "上游接口超时（秒）"},
    "RETRY_TIMES": {"type": "int", "min": 0, "max": 10, "description": "请求重试次数"},
    "RETRY_DELAY": {"type": "int", "min": 0, "max": 10, "description": "重试间隔（秒）"},
    "CACHE_TTL": {"type": "int", "min": 0, "max": 3600, "description": "价格缓存 TTL（秒）"},
    "CACHE_STALE_TTL": {"type": "int", "min": 0, "max": 86400, "description": "过期缓存兜底 TTL（秒）"},
    "SOURCE_FAIL_THRESHOLD": {"type": "int", "min": 1, "max": 20, "description": "数据源熔断失败阈值"},
    "SOURCE_COOLDOWN_SECONDS": {"type": "int", "min": 1, "max": 600, "description": "数据源熔断冷却秒数"},
    "ENABLE_BACKGROUND_SNAPSHOT": {"type": "bool", "description": "是否启用后台定时快照"},
    "ENABLE_STARTUP_SNAPSHOT": {"type": "bool", "description": "是否启用启动快照"},
    "LOG_LEVEL": {"type": "str", "choices": ["DEBUG", "INFO", "WARNING", "ERROR"], "description": "日志级别"},
}

_RUNTIME_CONFIG_OVERRIDES: Dict[str, Any] = {}


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
        items.append({
            "key": key,
            "value": value,
            "type": rule["type"],
            "description": rule["description"],
        })
    return items


def _json_body() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


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
    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS user_total,
            SUM(CASE WHEN DATE(u.created_at, 'localtime') = DATE('now', 'localtime') THEN 1 ELSE 0 END) AS new_today,
            SUM(CASE WHEN DATE(u.created_at, 'localtime') >= DATE('now', 'localtime', '-6 day') THEN 1 ELSE 0 END) AS new_7d,
            SUM(CASE WHEN DATE(u.created_at, 'localtime') >= DATE('now', 'localtime', '-29 day') THEN 1 ELSE 0 END) AS new_30d,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND DATE(u.last_login, 'localtime') = DATE('now', 'localtime') THEN 1 ELSE 0 END) AS dau,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND DATE(u.last_login, 'localtime') >= DATE('now', 'localtime', '-6 day') THEN 1 ELSE 0 END) AS wau,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND DATE(u.last_login, 'localtime') >= DATE('now', 'localtime', '-29 day') THEN 1 ELSE 0 END) AS mau,
            SUM(CASE WHEN u.last_login IS NULL OR TRIM(u.last_login) = '' THEN 1 ELSE 0 END) AS never_login,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND DATETIME(u.last_login, 'localtime') >= DATETIME('now', 'localtime', '-1 day') THEN 1 ELSE 0 END) AS within_1d,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND DATETIME(u.last_login, 'localtime') < DATETIME('now', 'localtime', '-1 day') AND DATETIME(u.last_login, 'localtime') >= DATETIME('now', 'localtime', '-7 day') THEN 1 ELSE 0 END) AS within_7d,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND DATETIME(u.last_login, 'localtime') < DATETIME('now', 'localtime', '-7 day') AND DATETIME(u.last_login, 'localtime') >= DATETIME('now', 'localtime', '-30 day') THEN 1 ELSE 0 END) AS within_30d,
            SUM(CASE WHEN u.last_login IS NOT NULL AND TRIM(u.last_login) != '' AND DATETIME(u.last_login, 'localtime') < DATETIME('now', 'localtime', '-30 day') THEN 1 ELSE 0 END) AS over_30d
        FROM users u
        WHERE {_real_user_where('u')}
        """
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


def create_admin_blueprint(db, admin_write_audit):
    bp = Blueprint("admin_routes", __name__, url_prefix="/api/admin")

    @bp.route("/overview", methods=["GET"])
    @admin_required
    def admin_overview():
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            user_ops = _get_user_ops_metrics(cursor)

            cursor.execute("SELECT COUNT(*) AS c FROM daily_snapshots")
            snapshot_total = int(cursor.fetchone()["c"])
            cursor.execute("SELECT MAX(date) AS latest_date FROM daily_snapshots")
            latest_row = cursor.fetchone()
            latest_snapshot_date = latest_row["latest_date"] if latest_row else None

            cursor.execute(
                """
                SELECT id, admin_user_id, action, target_type, target_id,
                       method, path, status_code, result, created_at
                FROM admin_audit_logs
                ORDER BY id DESC
                LIMIT 20
                """
            )
            recent_audits = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "users": {
                    "total": user_ops["user_total"],
                },
                "user_ops": user_ops,
                "snapshots": {
                    "total": snapshot_total,
                    "latest_date": latest_snapshot_date,
                },
                "recent_audits": recent_audits,
            })
        finally:
            conn.close()

    @bp.route("/users", methods=["GET"])
    @admin_required
    def admin_users():
        q = request.args.get("q", "").strip()
        status = request.args.get("status", "all").strip().lower()
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
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                WITH base_users AS (
                    SELECT
                        u.id,
                        u.username,
                        COALESCE(u.nickname, '') AS nickname,
                        u.phone,
                        u.user_number,
                        COALESCE(u.register_method, '') AS register_method,
                        LOWER(COALESCE(NULLIF(u.status, ''), 'active')) AS status,
                        u.created_at,
                        u.last_login,
                        1 AS can_manage
                    FROM users u
                    WHERE {_real_user_where("u")}
                    UNION ALL
                    SELECT
                        '__local__' AS id,
                        'local_user' AS username,
                        '本机未登录用户' AS nickname,
                        '' AS phone,
                        NULL AS user_number,
                        'local_anonymous' AS register_method,
                        'active' AS status,
                        NULL AS created_at,
                        NULL AS last_login,
                        0 AS can_manage
                    WHERE EXISTS (
                        SELECT 1 FROM portfolio WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM cash_assets WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM other_assets WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM liabilities WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM transactions WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM daily_snapshots WHERE user_id IS NULL OR TRIM(user_id) = ''
                    )
                )
                SELECT COUNT(*) AS c
                FROM base_users bu
                {where_sql}
                """,
                tuple(params),
            )
            total = int((cursor.fetchone() or {"c": 0})["c"])

            cursor.execute(
                f"""
                WITH base_users AS (
                    SELECT
                        u.id,
                        u.username,
                        COALESCE(u.nickname, '') AS nickname,
                        u.phone,
                        u.user_number,
                        COALESCE(u.register_method, '') AS register_method,
                        LOWER(COALESCE(NULLIF(u.status, ''), 'active')) AS status,
                        u.created_at,
                        u.last_login,
                        1 AS can_manage
                    FROM users u
                    WHERE {_real_user_where("u")}
                    UNION ALL
                    SELECT
                        '__local__' AS id,
                        'local_user' AS username,
                        '本机未登录用户' AS nickname,
                        '' AS phone,
                        NULL AS user_number,
                        'local_anonymous' AS register_method,
                        'active' AS status,
                        NULL AS created_at,
                        NULL AS last_login,
                        0 AS can_manage
                    WHERE EXISTS (
                        SELECT 1 FROM portfolio WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM cash_assets WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM other_assets WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM liabilities WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM transactions WHERE user_id IS NULL OR TRIM(user_id) = ''
                        UNION ALL SELECT 1 FROM daily_snapshots WHERE user_id IS NULL OR TRIM(user_id) = ''
                    )
                )
                SELECT
                    bu.id,
                    bu.username,
                    bu.nickname,
                    bu.phone,
                    bu.user_number,
                    bu.register_method,
                    bu.status,
                    bu.created_at,
                    bu.last_login,
                    bu.can_manage
                FROM base_users bu
                {where_sql}
                ORDER BY COALESCE(bu.last_login, bu.created_at, '') DESC, bu.id DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [limit, offset]),
            )
            users = [dict(row) for row in cursor.fetchall()]
            return jsonify({"items": users, "limit": limit, "offset": offset, "total": total})
        finally:
            conn.close()

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
                        "status": "active",
                        "created_at": None,
                        "last_login": None,
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
                    LOWER(COALESCE(NULLIF(u.status, ''), 'active')) AS status,
                    u.created_at,
                    u.last_login,
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
                SELECT id, username, nickname, phone, user_number, is_admin, status, created_at, last_login
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
            where.append("user_id = ?")
            params.append(user_id)
        if start_date:
            where.append("date >= ?")
            params.append(start_date)
        if end_date:
            where.append("date <= ?")
            params.append(end_date)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT id, date, user_id, total_asset, total_invest, total_cash,
                       total_other, total_liability, total_pnl, day_pnl, updated_at
                FROM daily_snapshots
                {where_sql}
                ORDER BY date DESC, user_id ASC
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

        payload = {
            "status": "ok" if (db_ok and upstream_ok) else "degraded",
            "server_time_utc": datetime.now(timezone.utc).isoformat(),
            "db": {"ok": db_ok, "error": db_error},
            "upstream": upstream,
            "runtime": get_price_runtime_metrics(),
            "sources": get_price_source_health(),
            "version_info": system_manager.get_version_info(),
        }
        return jsonify(payload)

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
            while len(generated) < missing * 2:
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
        payload = db.list_invite_codes(status=status, batch_id=batch_id, limit=limit, offset=offset)
        return jsonify(payload)

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
        writer.writerow(["code", "batch_id", "status", "created_by", "created_at", "used_by_user_id", "used_at", "note"])
        for item in payload.get("items", []):
            writer.writerow([
                item.get("code", ""),
                item.get("batch_id", ""),
                item.get("status", ""),
                item.get("created_by", ""),
                item.get("created_at", ""),
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
        limit = max(1, min(request.args.get("limit", 100, type=int), 500))
        offset = max(0, request.args.get("offset", 0, type=int))

        where = []
        params: List[Any] = []
        if action:
            where.append("action = ?")
            params.append(action)
        if admin_user_id:
            where.append("admin_user_id = ?")
            params.append(admin_user_id)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT id, admin_user_id, action, target_type, target_id,
                       method, path, status_code, result, error, created_at
                FROM admin_audit_logs
                {where_sql}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [limit, offset]),
            )
            items = [dict(row) for row in cursor.fetchall()]
            return jsonify({"items": items, "limit": limit, "offset": offset})
        finally:
            conn.close()

    return bp

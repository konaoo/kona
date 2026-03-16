"""
管理后台：用户写链路路由。
"""

from __future__ import annotations

from typing import Any, List

from flask import g, jsonify

from core.auth import admin_required
from core.admin.user_admin import reset_user_password, revoke_user_sessions


def register_admin_user_write_routes(bp, db, admin_write_audit) -> None:
    import admin_routes as admin_routes_module

    @bp.route("/users/status", methods=["POST"])
    @admin_write_audit(action="admin.users.status", target_type="user")
    @admin_required
    def admin_users_status():
        data = admin_routes_module._json_body()
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
                WHERE id = ? AND {admin_routes_module._real_user_where()}
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
        data = admin_routes_module._json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        updates = []
        params: List[Any] = []

        if "is_admin" in data:
            try:
                is_admin_value = 1 if admin_routes_module._coerce_bool(data.get("is_admin")) else 0
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
                f"UPDATE users SET {', '.join(updates)} WHERE id = ? AND {admin_routes_module._real_user_where()}",
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
                WHERE id = ? AND {admin_routes_module._real_user_where()}
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
        data = admin_routes_module._json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if user_id == g.user_id:
            return jsonify({"error": "Cannot disable current admin user"}), 400
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"UPDATE users SET status = 'disabled' WHERE id = ? AND {admin_routes_module._real_user_where()}",
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
        data = admin_routes_module._json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"UPDATE users SET status = 'active' WHERE id = ? AND {admin_routes_module._real_user_where()}",
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
        data = admin_routes_module._json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if user_id == "__local__":
            return jsonify({"error": "Local anonymous user is read-only"}), 400
        force_change = True
        if "force_change" in data:
            try:
                force_change = admin_routes_module._coerce_bool(data.get("force_change"))
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
        data = admin_routes_module._json_body()
        user_id = str(data.get("user_id", "")).strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        if user_id == "__local__":
            return jsonify({"error": "Local anonymous user is read-only"}), 400
        payload, code = revoke_user_sessions(db=db, user_id=user_id)
        return jsonify(payload), code

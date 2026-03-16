"""
管理后台：用户读链路路由。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
import time

from flask import jsonify, request

from core.auth import admin_required


def register_admin_user_read_routes(bp, db) -> None:
    import admin_routes as admin_routes_module

    @bp.route("/users", methods=["GET"])
    @admin_required
    def admin_users():
        q = request.args.get("q", "").strip()
        status = request.args.get("status", "all").strip().lower()
        sort_by = request.args.get("sort_by", "last_active_at").strip().lower()
        sort_dir = request.args.get("sort_dir", "desc").strip().lower()
        include_local_raw = request.args.get("include_local", "1")
        try:
            include_local = admin_routes_module._coerce_bool(include_local_raw)
        except ValueError:
            return jsonify({"error": "Invalid include_local"}), 400
        sort_expr_map = {
            "last_active_at": "COALESCE(bu.last_active_at, bu.last_login, bu.created_at, '')",
            "total_asset_cny": "COALESCE(bu.total_asset_cny, 0.0)",
            "total_invest_cny": "COALESCE(bu.total_invest_cny, 0.0)",
            "created_at": "COALESCE(bu.created_at, '')",
        }
        if sort_by not in sort_expr_map:
            return jsonify({"error": "Invalid sort_by"}), 400
        if sort_dir not in {"asc", "desc"}:
            return jsonify({"error": "Invalid sort_dir"}), 400
        order_by_sql = f"{sort_expr_map[sort_by]} {sort_dir.upper()}, bu.id DESC"
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
        elif status == "all":
            where.append("COALESCE(bu.total_asset_cny, 0.0) > 0")

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
                        '' AS last_active_ip,
                        '' AS last_active_region,
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
                        COALESCE(u.last_active_ip, '') AS last_active_ip,
                        COALESCE(u.last_active_region, '') AS last_active_region,
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
                    WHERE {admin_routes_module._real_user_where("u")}
                    {local_union_sql}
                )
        """
        try:
            force = admin_routes_module._admin_parse_force_arg()
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
                        bu.last_active_ip,
                        bu.last_active_region,
                        bu.active_sessions,
                        bu.total_asset_cny,
                        bu.total_invest_cny,
                        bu.can_manage,
                        COUNT(1) OVER() AS __total_count
                    FROM base_users bu
                    {where_sql}
                    ORDER BY {order_by_sql}
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
                    item["last_login_region"] = admin_routes_module._admin_region_display(item.get("last_login_region"))
                    item["last_active_region"] = admin_routes_module._admin_region_display(
                        item.get("last_active_region") or item.get("last_login_region")
                    )
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

        payload, cache_state, params_hash, elapsed_ms = admin_routes_module._admin_cached_payload(
            route_name="admin_users",
            params={
                "q": q,
                "status": status,
                "include_local": int(include_local),
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "limit": limit,
                "offset": offset,
                "force": request.args.get("force", ""),
            },
            force=force,
            loader=_load_users_payload,
        )
        admin_routes_module._admin_log_read("admin_users", cache_state, elapsed_ms, params_hash)
        return jsonify(payload)

    @bp.route("/users/metrics", methods=["GET"])
    @admin_required
    def admin_users_metrics():
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            metrics = admin_routes_module._get_user_ops_metrics(cursor)
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
                if admin_routes_module._has_local_anonymous_user(cursor):
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
                        "last_active_ip": "",
                        "last_active_region": "",
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
                    COALESCE(u.last_active_ip, '') AS last_active_ip,
                    COALESCE(u.last_active_region, '') AS last_active_region,
                    (
                        SELECT COUNT(1)
                        FROM auth_refresh_tokens rt
                        WHERE rt.user_id = u.id
                          AND rt.revoked_at IS NULL
                          AND DATETIME(rt.expires_at) > DATETIME('now')
                    ) AS active_sessions,
                    1 AS can_manage
                FROM users u
                WHERE u.id = ? AND {admin_routes_module._real_user_where("u")}
                LIMIT 1
                """,
                (uid,),
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "User not found"}), 404
            item = dict(row)
            item["last_login_region"] = admin_routes_module._admin_region_display(item.get("last_login_region"))
            item["last_active_region"] = admin_routes_module._admin_region_display(
                item.get("last_active_region") or item.get("last_login_region")
            )
            return jsonify(item)
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
        try:
            force = admin_routes_module._admin_parse_force_arg()
        except ValueError:
            return jsonify({"error": "Invalid force"}), 400

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT 1
                FROM users u
                WHERE u.id = ? AND {admin_routes_module._real_user_where("u")}
                LIMIT 1
                """,
                (uid,),
            )
            if not cursor.fetchone():
                return jsonify({"error": "User not found"}), 404
        finally:
            conn.close()

        if not force and admin_routes_module.ADMIN_PORTFOLIO_CACHE_TTL_SECONDS > 0:
            now_ts = time.time()
            with admin_routes_module._ADMIN_PORTFOLIO_CACHE_LOCK:
                cached = admin_routes_module._ADMIN_PORTFOLIO_CACHE.get(uid)
                if cached and cached[0] > now_ts:
                    return jsonify(dict(cached[1]))
                if cached:
                    admin_routes_module._ADMIN_PORTFOLIO_CACHE.pop(uid, None)

        payload = admin_routes_module._build_admin_portfolio_payload(db, uid)
        expires_at_ts = time.time() + admin_routes_module.ADMIN_PORTFOLIO_CACHE_TTL_SECONDS
        with admin_routes_module._ADMIN_PORTFOLIO_CACHE_LOCK:
            admin_routes_module._ADMIN_PORTFOLIO_CACHE[uid] = (expires_at_ts, dict(payload))
        return jsonify(payload)

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
            active_sessions = admin_routes_module._get_active_session_count(cursor, user_id)
            return jsonify({"user_id": user_id, "active_sessions": active_sessions})
        finally:
            conn.close()

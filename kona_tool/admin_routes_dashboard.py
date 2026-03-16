"""
管理后台：概览 / 词典 / 待办 路由。
"""

from __future__ import annotations

from typing import Any, Dict, List

from flask import jsonify, request

from core.auth import admin_required


def register_admin_dashboard_routes(bp, db) -> None:
    import admin_routes as admin_routes_module

    @bp.route("/overview", methods=["GET"])
    @admin_required
    def admin_overview():
        try:
            force = admin_routes_module._admin_parse_force_arg()
        except ValueError:
            return jsonify({"error": "Invalid force"}), 400

        def _load_overview_payload() -> Dict[str, Any]:
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                user_ops = admin_routes_module._get_user_ops_metrics(cursor)
                retention_rows = admin_routes_module._get_user_retention_rows(cursor, days=60)
                new_user_bars = admin_routes_module._build_mini_bars(retention_rows, "new_users")
                active_user_bars = admin_routes_module._build_mini_bars(retention_rows, "active_users")
                new_user_trend_text = admin_routes_module._build_trend_text(
                    retention_rows,
                    "new_users",
                    unit="人",
                    empty_text="近7天新增走势",
                    single_text="仅有今日数据",
                )
                active_user_trend_text = admin_routes_module._build_trend_text(
                    retention_rows,
                    "active_users",
                    unit="人",
                    empty_text="近7天活跃走势",
                    single_text="仅有今日数据",
                )
                new_users_avatar_count = int(user_ops["new_today"] or 0) // 10

                cursor.execute("SELECT COUNT(*) AS c FROM daily_snapshots")
                snapshot_total = int(cursor.fetchone()["c"])
                cursor.execute("SELECT MAX(date) AS latest_date FROM daily_snapshots")
                latest_row = cursor.fetchone()
                latest_snapshot_date = latest_row["latest_date"] if latest_row else None

                recent_audits = admin_routes_module._recent_admin_audits(cursor, limit=20)

                return {
                    "dashboard": {
                        "new_users_today": user_ops["new_today"],
                        "active_users_today": user_ops["dau"],
                        "total_users": user_ops["user_total"],
                        "new_users_avatar_count": new_users_avatar_count,
                        "new_user_trend_text": new_user_trend_text,
                        "active_user_trend_text": active_user_trend_text,
                        "new_user_bars": new_user_bars,
                        "active_user_bars": active_user_bars,
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

        payload, cache_state, params_hash, elapsed_ms = admin_routes_module._admin_cached_payload(
            route_name="admin_overview",
            params={"force": request.args.get("force", "")},
            force=force,
            loader=_load_overview_payload,
        )
        admin_routes_module._admin_log_read("admin_overview", cache_state, elapsed_ms, params_hash)
        return jsonify(payload)

    @bp.route("/meta/dictionaries", methods=["GET"])
    @admin_required
    def admin_meta_dictionaries():
        policy_labels = {
            key: value["name"] for key, value in admin_routes_module.POLICY_LABELS.items()
        }
        policy_impacts = {
            key: value["impact"] for key, value in admin_routes_module.POLICY_LABELS.items()
        }
        config_labels = {
            key: rule.get("display_name", key)
            for key, rule in admin_routes_module.CONFIG_WHITELIST.items()
        }
        return jsonify(
            {
                "status_labels": admin_routes_module.STATUS_LABELS,
                "action_labels": admin_routes_module.ACTION_LABELS,
                "policy_labels": policy_labels,
                "policy_impacts": policy_impacts,
                "policy_type_labels": admin_routes_module.POLICY_TYPE_LABELS,
                "register_method_labels": admin_routes_module.REGISTER_METHOD_LABELS,
                "error_labels": admin_routes_module.ERROR_LABELS,
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
                  AND {admin_routes_module._real_user_where('u')}
                """
            )
            disabled_users = int((cursor.fetchone() or {"c": 0})["c"] or 0)
        finally:
            conn.close()

        policies = db.list_admin_api_policies(scope_type="all")
        disabled_policies = [p for p in policies if not bool(p.get("enabled"))]
        upstream = admin_routes_module.system_manager.check_api_status()
        degraded_upstream = [
            key for key, item in (upstream or {}).items() if not bool((item or {}).get("ok"))
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
            names = [admin_routes_module.POLICY_LABELS.get(p["scope_key"], {}).get("name", p["scope_key"]) for p in disabled_policies]
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
            names = [admin_routes_module.POLICY_LABELS.get(f"upstream.{k}", {}).get("name", k) for k in degraded_upstream]
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
                    "suggestion": "请检查后台日志并及时处理失败原因。",
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

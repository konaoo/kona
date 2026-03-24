"""
管理后台：接口健康、策略、巡检与价格告警路由。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
import time

from flask import current_app, g, jsonify, request

from core.admin import cache as admin_cache
from core.admin import common as admin_common
from core.admin import constants as admin_constants
from core.admin import monitoring as admin_monitoring
from core.admin.policies import batch_update_policies, list_policies, update_policy
from core.auth import admin_required
from core.policy_runtime import invalidate_policy_cache
from core.system import system_manager


def register_admin_api_routes(bp, db, admin_write_audit) -> None:
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
        except Exception as exc:
            db_ok = False
            db_error = str(exc)
        finally:
            conn.close()

        upstream = system_manager.check_api_status()
        upstream_ok = all(item.get("ok") for item in upstream.values()) if upstream else True
        policies = db.list_admin_api_policies(scope_type="all")
        for policy in policies:
            policy["enabled"] = bool(policy.get("enabled"))
            scope_key = str(policy.get("scope_key", ""))
            policy["display_name"] = admin_constants.POLICY_LABELS.get(scope_key, {}).get("name", scope_key)
            policy["impact"] = admin_constants.POLICY_LABELS.get(scope_key, {}).get("impact", "")
            policy["scope_type_label"] = admin_constants.POLICY_TYPE_LABELS.get(
                str(policy.get("scope_type", "")),
                str(policy.get("scope_type", "")),
            )

        payload = {
            "status": "ok" if (db_ok and upstream_ok) else "degraded",
            "server_time_utc": datetime.now(timezone.utc).isoformat(),
            "db": {"ok": db_ok, "error": db_error},
            "upstream": upstream,
            "policies": policies,
            "runtime": admin_monitoring.get_price_runtime_metrics(),
            "sources": admin_monitoring.get_price_source_health(),
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
            item["display_name"] = admin_constants.POLICY_LABELS.get(scope_key, {}).get("name", scope_key)
            item["impact"] = admin_constants.POLICY_LABELS.get(scope_key, {}).get("impact", "")
            item["scope_type_label"] = admin_constants.POLICY_TYPE_LABELS.get(
                str(item.get("scope_type", "")),
                str(item.get("scope_type", "")),
            )
        return jsonify(payload)

    @bp.route("/apis/policies/update", methods=["POST"])
    @admin_write_audit(action="admin.apis.policies.update", target_type="policy")
    @admin_required
    def admin_apis_policies_update():
        data = admin_common.json_body()
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
        data = admin_common.json_body()
        items = data.get("items")
        payload, code = batch_update_policies(
            db=db,
            items=items if isinstance(items, list) else [],
            updated_by=getattr(g, "user_id", "") or "",
        )
        if code == 200:
            invalidate_policy_cache()
        return jsonify(payload), code

    @bp.route("/apis/provider_test", methods=["POST"])
    @admin_required
    def admin_apis_provider_test():
        data = admin_common.json_body()
        provider_key = str(data.get("provider_key", "")).strip().lower()
        if provider_key not in admin_constants.API_TEST_PROVIDER_LABELS:
            return jsonify({"error": "Invalid provider_key"}), 400

        if provider_key == "forex_rate":
            payload = admin_monitoring.run_forex_provider_test()
            return jsonify(payload)

        payload = admin_monitoring.run_market_provider_test(provider_key)
        return jsonify(payload)

    @bp.route("/apis/provider_tests/latest", methods=["GET"])
    @admin_required
    def admin_apis_provider_tests_latest():
        payload = admin_monitoring.get_latest_provider_test_report()
        if payload:
            return jsonify(payload)
        return jsonify(
            {
                "tested_at_utc": "",
                "summary": {"status": "idle", "label": "未测试", "alert_keys": []},
                "providers": {},
            }
        )

    @bp.route("/apis/provider_tests/run", methods=["POST"])
    @admin_required
    def admin_apis_provider_tests_run():
        payload = admin_monitoring.run_provider_test_report_job()
        return jsonify(payload)

    @bp.route("/apis/price_alerts", methods=["GET"])
    @admin_required
    def admin_apis_price_alerts():
        force = admin_cache.admin_parse_force_arg()
        started = time.perf_counter()
        params = dict(request.args or {})
        _, params_hash = admin_cache.admin_cache_key(admin_constants.PRICE_ALERT_ROUTE_NAME, params)

        if not force:
            latest_report = admin_monitoring.get_latest_price_alert_report()
            if latest_report:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                payload = {
                    "tested_at_utc": latest_report.get("tested_at_utc") or "",
                    "total_assets": int(latest_report.get("total_assets") or 0),
                    "alert_count": int(latest_report.get("alert_count") or 0),
                    "summary": dict(latest_report.get("summary") or {}),
                    "items": list(latest_report.get("items") or []),
                    "report_date": latest_report.get("report_date") or "",
                    "history": admin_monitoring.list_price_alert_report_history(),
                    "cache": {
                        "state": "snapshot",
                        "elapsed_ms": elapsed_ms,
                    },
                }
                admin_cache.log_admin_read(
                    admin_constants.PRICE_ALERT_ROUTE_NAME,
                    "SNAPSHOT",
                    elapsed_ms,
                    params_hash,
                )
                return jsonify(payload)

        payload, cache_state, params_hash, elapsed_ms = admin_cache.cached_payload(
            admin_constants.PRICE_ALERT_ROUTE_NAME,
            params,
            force,
            admin_monitoring.load_price_alerts_payload,
        )
        if cache_state in {"MISS", "BYPASS"}:
            admin_monitoring.save_price_alert_report_snapshot(payload)
        payload["history"] = admin_monitoring.list_price_alert_report_history()
        admin_cache.log_admin_read(
            admin_constants.PRICE_ALERT_ROUTE_NAME,
            cache_state,
            elapsed_ms,
            params_hash,
        )
        payload["cache"] = {
            "state": cache_state.lower(),
            "elapsed_ms": elapsed_ms,
        }
        return jsonify(payload)

    @bp.route("/apis/price_probe", methods=["POST"])
    @admin_required
    def admin_apis_price_probe():
        data = admin_common.json_body()
        code = str(data.get("code", "")).strip()
        if not code:
            return jsonify({"error": "Missing code"}), 400
        try:
            payload = admin_monitoring.build_price_probe_payload(code)
            return jsonify(payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @bp.route("/apis/smoke_test", methods=["POST"])
    @admin_write_audit(action="admin.apis.smoke_test", target_type="system")
    @admin_required
    def admin_apis_smoke_test():
        results: List[Dict[str, Any]] = []

        def run_case(name: str, fn) -> None:
            try:
                detail = fn()
                results.append({"name": name, "ok": True, "detail": detail})
            except Exception as exc:
                results.append({"name": name, "ok": False, "error": str(exc)})

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
            return {
                "runtime": admin_monitoring.get_price_runtime_metrics(),
                "sources": admin_monitoring.get_price_source_health(),
            }

        run_case("health", _health_case)
        run_case("db", _db_case)
        run_case("upstream", _upstream_case)
        run_case("runtime", _runtime_case)

        all_ok = all(item.get("ok") for item in results)
        return jsonify({"status": "ok" if all_ok else "degraded", "items": results})

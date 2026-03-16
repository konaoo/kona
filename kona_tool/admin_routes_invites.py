"""
管理后台：邀请码路由。
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, List

from flask import g, jsonify, make_response, request

from core.auth import admin_required


def register_admin_invite_routes(bp, db, admin_write_audit) -> None:
    import admin_routes as admin_routes_module

    @bp.route("/invites/generate", methods=["POST"])
    @admin_write_audit(action="admin.invites.generate", target_type="invite")
    @admin_required
    def admin_invites_generate():
        data = admin_routes_module._json_body()
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
                code = admin_routes_module._make_invite_code(10)
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

        return jsonify(
            {
                "status": "ok",
                "batch_id": batch_id,
                "requested": target,
                "inserted": inserted_total,
                "codes": generated_all[:inserted_total],
            }
        )

    @bp.route("/invites", methods=["GET"])
    @admin_required
    def admin_invites_list():
        status = request.args.get("status", "all").strip().lower()
        batch_id = request.args.get("batch_id", "").strip()
        limit = max(1, min(request.args.get("limit", 200, type=int), 2000))
        offset = max(0, request.args.get("offset", 0, type=int))
        random_order = request.args.get("random", "0") == "1"

        try:
            force = admin_routes_module._admin_parse_force_arg()
        except ValueError:
            return jsonify({"error": "Invalid force"}), 400

        payload, cache_state, params_hash, elapsed_ms = admin_routes_module._admin_cached_payload(
            route_name="admin_invites",
            params={
                "status": status,
                "batch_id": batch_id,
                "limit": limit,
                "offset": offset,
                "random": "1" if random_order else "0",
                "force": request.args.get("force", ""),
            },
            force=force or random_order,
            loader=lambda: db.list_invite_codes(
                status=status,
                batch_id=batch_id,
                limit=limit,
                offset=offset,
                ordered_random=random_order,
            ),
        )
        admin_routes_module._admin_log_read("admin_invites", cache_state, elapsed_ms, params_hash)
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
        data = admin_routes_module._json_body()
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
            writer.writerow(
                [
                    item.get("code", ""),
                    item.get("batch_id", ""),
                    admin_routes_module.STATUS_LABELS.get(
                        str(item.get("status", "")).lower(),
                        item.get("status", ""),
                    ),
                    item.get("created_by", ""),
                    item.get("created_at", ""),
                    item.get("used_by_username", ""),
                    item.get("used_by_user_number", ""),
                    item.get("used_by_user_id", ""),
                    item.get("used_at", ""),
                    item.get("note", ""),
                ]
            )
        csv_content = output.getvalue()
        resp = make_response(csv_content)
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        filename = batch_id or "all"
        resp.headers["Content-Disposition"] = f"attachment; filename=invites-{filename}.csv"
        return resp

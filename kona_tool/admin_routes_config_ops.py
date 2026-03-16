"""
管理后台：配置与运营配置路由。
"""

from __future__ import annotations

from typing import Any, List, Tuple

import config
from flask import g, jsonify

from core.admin import common as admin_common
from core.admin import constants as admin_constants
from core.admin import runtime_config as admin_runtime_config
from core.auth import admin_required


def register_admin_config_ops_routes(bp, db, admin_write_audit) -> None:
    @bp.route("/config", methods=["GET"])
    @admin_required
    def admin_config():
        return jsonify({"items": admin_runtime_config.get_whitelist_configs()})

    @bp.route("/config/update", methods=["POST"])
    @admin_write_audit(action="admin.config.update", target_type="config")
    @admin_required
    def admin_config_update():
        data = admin_common.json_body()
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

        try:
            updated_items = admin_runtime_config.update_runtime_configs(updates)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"status": "ok", "updated": updated_items})

    @bp.route("/config/reset", methods=["POST"])
    @admin_write_audit(action="admin.config.reset", target_type="config")
    @admin_required
    def admin_config_reset():
        data = admin_common.json_body()
        key = str(data.get("key", "")).strip()
        try:
            updated_items = admin_runtime_config.reset_runtime_configs(key)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"status": "ok", "updated": updated_items})

    @bp.route("/ops/invite_acquire", methods=["GET"])
    @admin_required
    def admin_ops_invite_acquire():
        return jsonify(admin_runtime_config.load_invite_acquire_ops_config(db))

    @bp.route("/ops/invite_acquire/update", methods=["POST"])
    @admin_write_audit(action="admin.ops.invite_acquire.update", target_type="ops_config")
    @admin_required
    def admin_ops_invite_acquire_update():
        data = admin_common.json_body()
        try:
            text = admin_runtime_config.normalize_invite_acquire_text(data.get("text"))
            image_url = admin_runtime_config.normalize_invite_acquire_image_url(data.get("image_url"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        updater = str(getattr(g, "user_id", "") or "")
        db.set_runtime_config(admin_constants.OPS_INVITE_ACQUIRE_TEXT_KEY, text, updated_by=updater)
        db.set_runtime_config(admin_constants.OPS_INVITE_ACQUIRE_IMAGE_URL_KEY, image_url, updated_by=updater)
        return jsonify({"status": "ok", "text": text, "image_url": image_url})

    @bp.route("/ops/user_group", methods=["GET"])
    @admin_required
    def admin_ops_user_group():
        return jsonify(admin_runtime_config.load_user_group_ops_config(db))

    @bp.route("/ops/user_group/update", methods=["POST"])
    @admin_write_audit(action="admin.ops.user_group.update", target_type="ops_config")
    @admin_required
    def admin_ops_user_group_update():
        data = admin_common.json_body()
        try:
            text = admin_runtime_config.normalize_invite_acquire_text(data.get("text"))
            image_url = admin_runtime_config.normalize_invite_acquire_image_url(data.get("image_url"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        updater = str(getattr(g, "user_id", "") or "")
        db.set_runtime_config(admin_constants.OPS_USER_GROUP_TEXT_KEY, text, updated_by=updater)
        db.set_runtime_config(admin_constants.OPS_USER_GROUP_IMAGE_URL_KEY, image_url, updated_by=updater)
        return jsonify({"status": "ok", "text": text, "image_url": image_url})

    @bp.route("/ops/ios_qr", methods=["GET"])
    @admin_required
    def admin_ops_ios_qr():
        return jsonify(admin_runtime_config.load_ios_qr_ops_config(db))

    @bp.route("/ops/ios_qr/update", methods=["POST"])
    @admin_write_audit(action="admin.ops.ios_qr.update", target_type="ops_config")
    @admin_required
    def admin_ops_ios_qr_update():
        data = admin_common.json_body()
        try:
            text = admin_runtime_config.normalize_ios_qr_text(data.get("text"))
            image_url = admin_runtime_config.normalize_ios_qr_image_url(data.get("image_url"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        updater = str(getattr(g, "user_id", "") or "")
        db.set_runtime_config(admin_constants.OPS_IOS_QR_TEXT_KEY, text, updated_by=updater)
        db.set_runtime_config(admin_constants.OPS_IOS_QR_IMAGE_URL_KEY, image_url, updated_by=updater)
        return jsonify({"status": "ok", "text": text, "image_url": image_url})

    @bp.route("/ops/app_update", methods=["GET"])
    @admin_required
    def admin_ops_app_update():
        return jsonify(admin_runtime_config.load_app_update_ops_config(db))

    @bp.route("/ops/app_update/update", methods=["POST"])
    @admin_write_audit(action="admin.ops.app_update.update", target_type="ops_config")
    @admin_required
    def admin_ops_app_update_update():
        data = admin_common.json_body()
        try:
            text = admin_runtime_config.normalize_app_update_text(data.get("text"))
            download_url = admin_runtime_config.normalize_app_update_download_url(data.get("download_url"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        updater = str(getattr(g, "user_id", "") or "")
        db.set_runtime_config(admin_constants.OPS_APP_UPDATE_TEXT_KEY, text, updated_by=updater)
        db.set_runtime_config(
            admin_constants.OPS_APP_UPDATE_DOWNLOAD_URL_KEY,
            download_url,
            updated_by=updater,
        )
        return jsonify({"status": "ok", "text": text, "download_url": download_url})

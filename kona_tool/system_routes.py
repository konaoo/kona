"""
公开配置 / 系统信息 / 下载相关路由
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import config
from flask import Blueprint, jsonify, request, send_file


_RUNTIME_CFG_INVITE_ACQUIRE_TEXT_KEY = "ops.invite_acquire.text"
_RUNTIME_CFG_INVITE_ACQUIRE_IMAGE_URL_KEY = "ops.invite_acquire.image_url"
_RUNTIME_CFG_USER_GROUP_TEXT_KEY = "ops.user_group.text"
_RUNTIME_CFG_USER_GROUP_IMAGE_URL_KEY = "ops.user_group.image_url"
_RUNTIME_CFG_IOS_QR_TEXT_KEY = "ops.ios_qr.text"
_RUNTIME_CFG_IOS_QR_IMAGE_URL_KEY = "ops.ios_qr.image_url"
_RUNTIME_CFG_APP_UPDATE_TEXT_KEY = "ops.app_update.text"
_RUNTIME_CFG_APP_UPDATE_DOWNLOAD_URL_KEY = "ops.app_update.download_url"


def _read_runtime_config_or_default(db, key: str, default_value: str) -> str:
    """读取运行时配置，缺失时回退默认值。"""
    try:
        value = db.get_runtime_config(key)
    except Exception:
        return str(default_value or "")
    if value is None:
        return str(default_value or "")
    return str(value)


def create_system_blueprint(db, system_manager):
    bp = Blueprint("system_routes", __name__)

    @bp.route("/api/app/version", methods=["GET"])
    def api_app_version():
        """获取最新版客户端应用配置"""
        release_notes = _read_runtime_config_or_default(
            db,
            _RUNTIME_CFG_APP_UPDATE_TEXT_KEY,
            config.CLIENT_APP_RELEASE_NOTES,
        ).strip() or config.CLIENT_APP_RELEASE_NOTES
        download_url = _read_runtime_config_or_default(
            db,
            _RUNTIME_CFG_APP_UPDATE_DOWNLOAD_URL_KEY,
            config.CLIENT_APP_DOWNLOAD_URL,
        ).strip() or config.CLIENT_APP_DOWNLOAD_URL
        return jsonify(
            {
                "version": config.CLIENT_APP_VERSION,
                "buildNumber": config.CLIENT_APP_BUILD_NUMBER,
                "releaseNotes": release_notes,
                "downloadUrl": download_url,
                "forceUpdate": config.CLIENT_APP_FORCE_UPDATE,
            }
        )

    @bp.route("/api/settings/info")
    def get_system_info():
        """获取系统版本信息"""
        info = system_manager.get_version_info()
        return jsonify(info)

    @bp.route("/api/web/config")
    def get_web_config():
        """公开 Web 门户配置（无需鉴权）。"""
        apk_download_url = config.WEB_APK_DOWNLOAD_URL or config.CLIENT_APP_DOWNLOAD_URL
        invite_acquire_text = _read_runtime_config_or_default(
            db,
            _RUNTIME_CFG_INVITE_ACQUIRE_TEXT_KEY,
            config.INVITE_ACQUIRE_TEXT,
        ).strip() or config.INVITE_ACQUIRE_TEXT
        invite_acquire_image_url = _read_runtime_config_or_default(
            db,
            _RUNTIME_CFG_INVITE_ACQUIRE_IMAGE_URL_KEY,
            config.INVITE_ACQUIRE_IMAGE_URL,
        ).strip()
        user_group_text = _read_runtime_config_or_default(
            db,
            _RUNTIME_CFG_USER_GROUP_TEXT_KEY,
            config.USER_GROUP_TEXT,
        ).strip() or config.USER_GROUP_TEXT
        user_group_image_url = _read_runtime_config_or_default(
            db,
            _RUNTIME_CFG_USER_GROUP_IMAGE_URL_KEY,
            config.USER_GROUP_IMAGE_URL,
        ).strip()
        ios_qr_text = _read_runtime_config_or_default(
            db,
            _RUNTIME_CFG_IOS_QR_TEXT_KEY,
            config.IOS_QR_TEXT,
        ).strip() or config.IOS_QR_TEXT
        ios_qr_image_url = _read_runtime_config_or_default(
            db,
            _RUNTIME_CFG_IOS_QR_IMAGE_URL_KEY,
            config.IOS_QR_IMAGE_URL,
        ).strip()

        if not apk_download_url and config.WEB_APK_LOCAL_PATH.exists():
            apk_download_url = "/download/apk"

        return jsonify(
            {
                "portal_title": config.WEB_PORTAL_TITLE,
                "apk_download_url": apk_download_url,
                "app_version": config.APP_VERSION,
                "invite_acquire_text": invite_acquire_text,
                "invite_acquire_image_url": invite_acquire_image_url,
                "user_group_text": user_group_text,
                "user_group_image_url": user_group_image_url,
                "ios_qr_text": ios_qr_text,
                "ios_qr_image_url": ios_qr_image_url,
            }
        )

    @bp.route("/download/apk")
    def download_apk():
        """下载 Android APK 安装包。"""
        apk_path = config.WEB_APK_LOCAL_PATH
        if not apk_path.exists() or not apk_path.is_file():
            return jsonify({"error": "APK not found"}), 404
        return send_file(
            apk_path,
            as_attachment=True,
            download_name=apk_path.name,
            mimetype="application/vnd.android.package-archive",
        )

    @bp.route("/api/settings/check_api")
    def check_api_status():
        """检测 API 状态"""
        status = system_manager.check_api_status()
        return jsonify(status)

    @bp.route("/api/settings/backup")
    def backup_database():
        """下载数据库备份"""
        if config.DATABASE_PATH.exists():
            return send_file(
                config.DATABASE_PATH,
                as_attachment=True,
                download_name=f"portfolio_backup_{int(time.time())}.db",
                mimetype="application/x-sqlite3",
            )
        return jsonify({"error": "Database not found"}), 404

    @bp.route("/api/settings/restore", methods=["POST"])
    def restore_database():
        """恢复数据库"""
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        temp_path = config.BASE_DIR / "temp_restore.db"
        try:
            file.save(temp_path)
            success = system_manager.restore_database(str(temp_path))

            if success:
                return jsonify({"status": "ok", "message": "Restore successful"})
            return jsonify({"error": "Restore failed or invalid file"}), 500
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500
        finally:
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    return bp

"""
认证 API 路由
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

import config
from flask import Blueprint, g, jsonify, request

from core.auth import (
    generate_refresh_token,
    generate_token,
    get_user_profile,
    hash_password,
    hash_refresh_token,
    is_valid_username,
    login_required,
    normalize_username,
    validate_password,
    verify_password,
)


def _refresh_token_expiry_days() -> int:
    return int(getattr(config, "AUTH_REFRESH_TOKEN_DAYS", 365))


def _is_refresh_token_valid(token_row: dict) -> bool:
    if not token_row:
        return False
    if token_row.get("revoked_at"):
        return False
    expires_at = token_row.get("expires_at")
    if not expires_at:
        return False
    try:
        expire_dt = datetime.fromisoformat(str(expires_at))
    except Exception:
        return False
    if expire_dt.tzinfo is not None:
        expire_dt = expire_dt.astimezone(timezone.utc).replace(tzinfo=None)
    return expire_dt > datetime.utcnow()


def _issue_auth_tokens(db, user_id: str, username: str, device_id: str = "") -> dict:
    access_token = generate_token(user_id, username)
    refresh_token = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=_refresh_token_expiry_days())
    db.create_refresh_token(
        user_id=user_id,
        token_hash=refresh_hash,
        expires_at=expires_at,
        device_id=device_id,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_expires_at": expires_at.isoformat(),
    }


def _request_payload_diagnostics() -> str:
    """记录请求体诊断信息，排查空 body 或错误 content-type。"""
    content_type = (request.headers.get("Content-Type") or "").strip() or "-"
    header_content_length = (request.headers.get("Content-Length") or "").strip() or "-"
    request_id = (
        request.headers.get("X-Request-Id")
        or request.headers.get("X-Request-ID")
        or ""
    ).strip()[:64] or "-"
    try:
        body_len = len(request.get_data(cache=True) or b"")
    except Exception:
        body_len = -1
    content_length = request.content_length if request.content_length is not None else "-"
    return (
        f"content_type={content_type} "
        f"content_length={content_length} "
        f"header_content_length={header_content_length} "
        f"body_len={body_len} "
        f"request_id={request_id}"
    )


def _username_limit_key(client_ip_getter: Callable[[], str]) -> str:
    data = request.get_json(silent=True) or {}
    username = normalize_username(str(data.get("username", "")))
    return f"username:{username}" if username else f"ip:{client_ip_getter()}"


def create_auth_blueprint(
    db,
    limiter,
    *,
    client_ip_getter: Callable[[], str],
    resolve_ip_region: Callable[[str], str],
    auth_audit: Callable[..., None],
):
    bp = Blueprint("auth_routes", __name__, url_prefix="/api/auth")

    @bp.route("/login", methods=["POST"])
    @limiter.limit("20 per 10 minute")
    @limiter.limit("8 per 10 minute", key_func=lambda: _username_limit_key(client_ip_getter))
    def auth_login():
        data = request.get_json(silent=True)
        if not data:
            auth_audit(
                event="auth_login",
                outcome="failed",
                reason=f"missing_payload {_request_payload_diagnostics()}",
                level="warning",
            )
            return jsonify({"error": "请求参数缺失"}), 400

        username = normalize_username(data.get("username", ""))
        password = str(data.get("password", ""))
        device_id = str(data.get("device_id", "")).strip()[:128]
        if not username or not password:
            auth_audit(
                event="auth_login",
                outcome="failed",
                username=username,
                reason="missing_credentials",
                level="warning",
            )
            return jsonify({"error": "请输入账号和密码"}), 400

        user = db.get_user_by_username(username)
        if not user:
            auth_audit(
                event="auth_login",
                outcome="failed",
                username=username,
                reason="user_not_found",
                level="warning",
            )
            return jsonify({"error": "账号或密码错误"}), 401
        if str(user.get("status") or "active").lower() != "active":
            auth_audit(
                event="auth_login",
                outcome="failed",
                username=username,
                reason="user_disabled",
                level="warning",
            )
            return jsonify({"error": "账号已停用，请联系管理员"}), 403
        if user.get("legacy_needs_password_setup") or not user.get("password_hash"):
            auth_audit(
                event="auth_login",
                outcome="failed",
                username=username,
                reason="password_not_setup",
                level="warning",
            )
            return jsonify({"error": "当前账号还未完成密码初始化"}), 403
        if not verify_password(password, str(user.get("password_hash") or "")):
            auth_audit(
                event="auth_login",
                outcome="failed",
                username=username,
                reason="bad_password",
                level="warning",
            )
            return jsonify({"error": "账号或密码错误"}), 401

        client_ip = client_ip_getter()
        db.update_last_login(
            user["id"],
            login_ip=client_ip,
            login_region=resolve_ip_region(client_ip),
        )
        tokens = _issue_auth_tokens(db, user["id"], username, device_id=device_id)
        profile = get_user_profile(db, user["id"]) or {}
        auth_audit(event="auth_login", outcome="success", username=username, reason=f"user_id={user['id']}")
        return jsonify(
            {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "refresh_expires_at": tokens["refresh_expires_at"],
                "user": profile,
            }
        )

    @bp.route("/register", methods=["POST"])
    @limiter.limit("10 per 10 minute")
    @limiter.limit("5 per 10 minute", key_func=lambda: _username_limit_key(client_ip_getter))
    def auth_register():
        data = request.get_json(silent=True) or {}
        username = normalize_username(data.get("username", ""))
        password = str(data.get("password", ""))
        invite_code = str(data.get("invite_code", "")).strip().upper()
        device_id = str(data.get("device_id", "")).strip()[:128]

        if not is_valid_username(username):
            auth_audit(
                event="auth_register",
                outcome="failed",
                username=username,
                reason="invalid_username",
                level="warning",
            )
            return jsonify({"error": "用户名格式不正确"}), 400
        ok, msg = validate_password(password)
        if not ok:
            auth_audit(
                event="auth_register",
                outcome="failed",
                username=username,
                reason="weak_password",
                level="warning",
            )
            return jsonify({"error": msg}), 400
        if not invite_code:
            auth_audit(
                event="auth_register",
                outcome="failed",
                username=username,
                reason="missing_invite",
                level="warning",
            )
            return jsonify({"error": "请填写邀请码"}), 400
        if db.get_user_by_username(username):
            auth_audit(
                event="auth_register",
                outcome="failed",
                username=username,
                reason="username_exists",
                level="warning",
            )
            return jsonify({"error": "用户名已存在"}), 409
        invite = db.get_invite_code(invite_code)
        if not invite or invite.get("status") != "active" or invite.get("used_by_user_id"):
            auth_audit(
                event="auth_register",
                outcome="failed",
                username=username,
                reason="invalid_invite",
                level="warning",
            )
            return jsonify({"error": "邀请码无效或已被使用"}), 400

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(1) AS c FROM users WHERE COALESCE(password_hash, '') != ''")
            pwd_user_count = int(cursor.fetchone()["c"] or 0)
        finally:
            conn.close()
        is_first_password_user = pwd_user_count == 0

        user_id = secrets.token_hex(16)
        password_h = hash_password(password)
        try:
            created = db.create_user(
                username=username,
                password_hash=password_h,
                register_method="password_invite",
                is_admin=is_first_password_user,
                user_id=user_id,
            )
        except Exception:
            auth_audit(
                event="auth_register",
                outcome="failed",
                username=username,
                reason="create_user_failed",
                level="warning",
            )
            return jsonify({"error": "注册失败，请稍后重试"}), 500

        consumed, reason = db.consume_invite_code(invite_code, created["id"])
        if not consumed:
            db.delete_user(created["id"])
            auth_audit(
                event="auth_register",
                outcome="failed",
                username=username,
                reason="consume_invite_failed",
                level="warning",
            )
            return jsonify({"error": reason or "邀请码无效或已被使用"}), 400

        client_ip = client_ip_getter()
        db.update_last_login(
            created["id"],
            login_ip=client_ip,
            login_region=resolve_ip_region(client_ip),
        )
        tokens = _issue_auth_tokens(db, created["id"], username, device_id=device_id)
        profile = get_user_profile(db, created["id"]) or {}
        auth_audit(event="auth_register", outcome="success", username=username, reason=f"user_id={created['id']}")
        return jsonify(
            {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "refresh_expires_at": tokens["refresh_expires_at"],
                "user": profile,
            }
        )

    @bp.route("/invite/validate", methods=["POST"])
    @limiter.limit("30 per 10 minute")
    def auth_validate_invite():
        data = request.get_json(silent=True) or {}
        invite_code = str(data.get("invite_code", "")).strip().upper()
        if not re.match(r"^[A-Z0-9]{8,16}$", invite_code):
            return jsonify({"valid": False, "error": "邀请码格式不正确"}), 400
        invite = db.get_invite_code(invite_code)
        if not invite or invite.get("status") != "active" or invite.get("used_by_user_id"):
            return jsonify({"valid": False, "error": "邀请码无效或已被使用"}), 404
        return jsonify({"valid": True, "code": invite_code, "batch_id": invite.get("batch_id")})

    @bp.route("/me", methods=["GET"])
    @login_required
    def auth_me():
        profile = get_user_profile(db, g.user_id)
        if profile:
            return jsonify(profile)
        return jsonify({"user_id": g.user_id, "username": g.username})

    @bp.route("/profile", methods=["POST"])
    @login_required
    @limiter.limit("30 per 10 minute")
    def update_profile():
        data = request.json or {}
        nickname = data.get("nickname")
        avatar = data.get("avatar")

        if nickname is None and avatar is None:
            auth_audit(
                event="auth_profile_update",
                outcome="failed",
                username=g.username,
                reason="no_fields",
                level="warning",
            )
            return jsonify({"error": "没有可更新的资料"}), 400

        if isinstance(nickname, str):
            nickname = nickname.strip()

        if isinstance(avatar, str) and len(avatar) > 1_500_000:
            auth_audit(
                event="auth_profile_update",
                outcome="failed",
                username=g.username,
                reason="avatar_too_large",
                level="warning",
            )
            return jsonify({"error": "头像文件过大"}), 400

        ok = db.update_user_profile(g.user_id, nickname=nickname, avatar=avatar)
        if not ok:
            auth_audit(
                event="auth_profile_update",
                outcome="failed",
                username=g.username,
                reason="db_update_failed",
                level="warning",
            )
            return jsonify({"error": "资料更新失败"}), 500
        auth_audit(event="auth_profile_update", outcome="success", username=g.username, reason=f"user_id={g.user_id}")

        profile = get_user_profile(db, g.user_id) or {}
        return jsonify(profile)

    @bp.route("/bootstrap_credentials", methods=["POST"])
    @login_required
    @limiter.limit("8 per 10 minute")
    def auth_bootstrap_credentials():
        data = request.get_json(silent=True) or {}
        username = normalize_username(data.get("username", ""))
        new_password = str(data.get("password", ""))
        if not is_valid_username(username):
            auth_audit(
                event="auth_bootstrap",
                outcome="failed",
                username=username,
                reason="invalid_username",
                level="warning",
            )
            return jsonify({"error": "用户名格式不正确"}), 400
        ok, msg = validate_password(new_password)
        if not ok:
            auth_audit(
                event="auth_bootstrap",
                outcome="failed",
                username=username,
                reason="weak_password",
                level="warning",
            )
            return jsonify({"error": msg}), 400
        success, reason = db.bootstrap_credentials(g.user_id, username, hash_password(new_password))
        if not success:
            auth_audit(
                event="auth_bootstrap",
                outcome="failed",
                username=username,
                reason=reason or "bootstrap_failed",
                level="warning",
            )
            return jsonify({"error": reason or "初始化失败"}), 400
        db.revoke_all_refresh_tokens(g.user_id)
        client_ip = client_ip_getter()
        db.update_last_login(
            g.user_id,
            login_ip=client_ip,
            login_region=resolve_ip_region(client_ip),
        )
        tokens = _issue_auth_tokens(db, g.user_id, username)
        profile = get_user_profile(db, g.user_id) or {}
        auth_audit(event="auth_bootstrap", outcome="success", username=username, reason=f"user_id={g.user_id}")
        return jsonify(
            {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "refresh_expires_at": tokens["refresh_expires_at"],
                "user": profile,
            }
        )

    @bp.route("/password/change", methods=["POST"])
    @login_required
    @limiter.limit("10 per 10 minute")
    def auth_change_password():
        data = request.get_json(silent=True) or {}
        old_password = str(data.get("old_password", ""))
        new_password = str(data.get("new_password", ""))
        if not old_password or not new_password:
            return jsonify({"error": "请输入旧密码和新密码"}), 400
        ok, msg = validate_password(new_password)
        if not ok:
            return jsonify({"error": msg}), 400
        user = db.get_user_by_id(g.user_id)
        if not user:
            return jsonify({"error": "用户不存在"}), 404
        if not verify_password(old_password, str(user.get("password_hash") or "")):
            auth_audit(
                event="auth_password_change",
                outcome="failed",
                username=user.get("username") or g.username,
                reason="bad_old_password",
                level="warning",
            )
            return jsonify({"error": "旧密码不正确"}), 400
        if not db.set_user_password(g.user_id, hash_password(new_password)):
            return jsonify({"error": "密码更新失败"}), 500
        revoked = db.revoke_all_refresh_tokens(g.user_id)
        auth_audit(
            event="auth_password_change",
            outcome="success",
            username=user.get("username") or g.username,
            reason=f"revoked={revoked}",
        )
        return jsonify({"status": "ok", "revoked_refresh_tokens": revoked})

    @bp.route("/refresh", methods=["POST"])
    @limiter.limit("20 per 10 minute")
    def auth_refresh():
        data = request.get_json(silent=True) or {}
        refresh_token = str(data.get("refresh_token", "")).strip()
        device_id = str(data.get("device_id", "")).strip()[:128]
        if not refresh_token:
            return jsonify({"error": "缺少刷新令牌"}), 400
        token_hash = hash_refresh_token(refresh_token)
        token_row = db.get_refresh_token(token_hash)
        if not _is_refresh_token_valid(token_row):
            auth_audit(event="auth_refresh", outcome="failed", reason="invalid_refresh_token", level="warning")
            return jsonify({"error": "登录状态已过期，请重新登录"}), 401
        user = db.get_user_by_id(token_row.get("user_id"))
        if not user or str(user.get("status") or "active").lower() != "active":
            auth_audit(
                event="auth_refresh",
                outcome="failed",
                reason="user_disabled_or_missing",
                level="warning",
            )
            return jsonify({"error": "账号不可用，请重新登录"}), 403
        db.revoke_refresh_token(token_hash)
        db.touch_refresh_token(token_hash)
        tokens = _issue_auth_tokens(
            db,
            user["id"],
            user["username"],
            device_id=device_id or (token_row.get("device_id") or ""),
        )
        db.update_last_login(user["id"])
        auth_audit(event="auth_refresh", outcome="success", username=user["username"], reason=f"user_id={user['id']}")
        return jsonify(
            {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "refresh_expires_at": tokens["refresh_expires_at"],
                "user": get_user_profile(db, user["id"]) or {},
            }
        )

    @bp.route("/logout", methods=["POST"])
    @login_required
    def auth_logout():
        data = request.get_json(silent=True) or {}
        refresh_token = str(data.get("refresh_token", "")).strip()
        revoked = 0
        if refresh_token:
            if db.revoke_refresh_token(hash_refresh_token(refresh_token)):
                revoked = 1
        else:
            revoked = db.revoke_all_refresh_tokens(g.user_id)
        auth_audit(event="auth_logout", outcome="success", username=g.username, reason=f"revoked={revoked}")
        return jsonify({"status": "ok", "revoked_refresh_tokens": revoked})

    @bp.route("/send_code", methods=["POST"])
    def auth_send_code():
        """Deprecated: email verification login has been removed."""
        return jsonify({"error": "Deprecated endpoint", "code": "AUTH_EMAIL_OTP_REMOVED"}), 410

    return bp

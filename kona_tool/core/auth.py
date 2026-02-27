"""
Authentication and authorization helpers.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple

import jwt
from flask import g, jsonify, request

import config

logger = logging.getLogger(__name__)

JWT_SECRET = getattr(config, "JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(getattr(config, "JWT_EXPIRY_HOURS", 2))

_USERNAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{3,23}$")
_RESERVED_USERNAMES = {
    "admin",
    "administrator",
    "root",
    "system",
    "support",
    "service",
    "security",
    "owner",
}
_WEAK_PASSWORDS = {
    "12345678",
    "123456789",
    "password",
    "password123",
    "qwerty123",
    "11111111",
    "abc12345",
    "admin123",
    "00000000",
}

_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_LEN = 64
_PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/api/auth/password/change",
    "/api/auth/logout",
    "/api/auth/me",
}


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def is_valid_username(username: str) -> bool:
    u = normalize_username(username)
    return bool(_USERNAME_PATTERN.match(u)) and u not in _RESERVED_USERNAMES


def validate_password(password: str) -> Tuple[bool, str]:
    if not isinstance(password, str):
        return False, "Invalid password"
    if len(password) < 8 or len(password) > 64:
        return False, "Password length must be 8-64"
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must include letters"
    if not re.search(r"\d", password):
        return False, "Password must include numbers"
    if password.lower() in _WEAK_PASSWORDS:
        return False, "Password is too weak"
    return True, ""


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_LEN,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt_b64}${digest_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        parts = str(password_hash or "").split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            return False
        _, n, r, p, salt_b64, digest_b64 = parts
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
        return hmac.compare_digest(expected, actual)
    except Exception:
        return False


def generate_token(user_id: str, username: str) -> str:
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "username": normalize_username(username),
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": now,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Tuple[bool, Optional[dict]]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return True, payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return False, None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token: %s", e)
        return False, None


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _extract_bearer_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return ""
    return parts[1]


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({"error": "Missing Authorization header"}), 401
        valid, payload = verify_token(token)
        if not valid or not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        user_id = payload.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid token payload"}), 401
        from core.db import db as global_db

        user = global_db.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        if str(user.get("status") or "active").lower() != "active":
            return jsonify({"error": "User is disabled"}), 403

        must_change = bool(user.get("must_change_password"))
        if must_change and request.path not in _PASSWORD_CHANGE_ALLOWED_PATHS:
            return (
                jsonify(
                    {
                        "error": "Password change required",
                        "code": "PASSWORD_CHANGE_REQUIRED",
                    }
                ),
                403,
            )

        g.user_id = user.get("id")
        g.username = user.get("username") or payload.get("username")
        g.must_change_password = must_change
        return f(*args, **kwargs)

    return decorated


def optional_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        g.user_id = None
        g.username = None
        token = _extract_bearer_token()
        if token:
            valid, payload = verify_token(token)
            if not valid or not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            user_id = payload.get("user_id")
            if not user_id:
                return jsonify({"error": "Invalid token payload"}), 401
            from core.db import db as global_db

            user = global_db.get_user_by_id(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 401
            if str(user.get("status") or "active").lower() != "active":
                return jsonify({"error": "User is disabled"}), 403
            g.user_id = user.get("id")
            g.username = user.get("username")
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        remote_addr = (request.remote_addr or "").strip()
        has_proxy_headers = bool(
            request.headers.get("X-Forwarded-For")
            or request.headers.get("X-Real-IP")
        )
        is_loopback = remote_addr in {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
        if (
            getattr(config, "ALLOW_LOCAL_ADMIN_BYPASS", False)
            and is_loopback
            and not has_proxy_headers
        ):
            g.user_id = "admin_local_bypass"
            g.username = "admin_local"
            g.is_admin = True
            g.user_status = "active"
            return f(*args, **kwargs)

        token = _extract_bearer_token()
        if not token:
            return jsonify({"error": "Missing Authorization header"}), 401

        valid, payload = verify_token(token)
        if not valid or not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.user_id = payload.get("user_id")
        g.username = payload.get("username")

        from core.db import db as global_db

        auth_info = global_db.get_user_auth_info(g.user_id)
        if not auth_info:
            return jsonify({"error": "User not found"}), 403

        status = str(auth_info.get("status") or "active").lower()
        if status != "active":
            return jsonify({"error": "User is disabled"}), 403

        if not auth_info.get("is_admin"):
            return jsonify({"error": "Admin privileges required"}), 403

        g.is_admin = True
        g.user_status = status
        return f(*args, **kwargs)

    return decorated


def get_user_profile(db, user_id: str) -> Optional[dict]:
    profile = db.get_user_profile(user_id)
    if profile:
        profile["is_admin"] = bool(profile.get("is_admin"))
        profile["must_change_password"] = bool(profile.get("must_change_password"))
    return profile

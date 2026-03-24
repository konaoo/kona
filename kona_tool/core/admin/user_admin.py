"""Admin user management service."""

from __future__ import annotations

import secrets
from typing import Any, Dict, Optional, Tuple

from core.auth import hash_password, validate_password


def _generate_temp_password(length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    # Ensure both letter and number exist.
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(ch.isalpha() for ch in pwd) and any(ch.isdigit() for ch in pwd):
            return pwd


def reset_user_password(
    db,
    user_id: str,
    admin_user_id: str,
    temp_password: Optional[str] = None,
    force_change: bool = True,
) -> Tuple[Dict[str, Any], int]:
    uid = str(user_id or "").strip()
    if not uid:
        return {"error": "Missing user_id"}, 400

    user = db.get_user_by_id(uid)
    if not user:
        return {"error": "User not found"}, 404

    generated = False
    password = str(temp_password or "").strip()
    if not password:
        password = _generate_temp_password()
        generated = True

    ok, msg = validate_password(password)
    if not ok:
        return {"error": msg or "Invalid password"}, 400

    success = db.admin_reset_user_password(
        uid,
        hash_password(password),
        admin_user_id=admin_user_id,
        force_change=force_change,
    )
    if not success:
        return {"error": "Failed to reset password"}, 500

    revoked = db.revoke_all_refresh_tokens(uid)
    payload: Dict[str, Any] = {
        "status": "ok",
        "user_id": uid,
        "must_change_password": bool(force_change),
        "revoked_refresh_tokens": int(revoked),
    }
    if generated:
        payload["temp_password"] = password
    return payload, 200


def revoke_user_sessions(db, user_id: str) -> Tuple[Dict[str, Any], int]:
    uid = str(user_id or "").strip()
    if not uid:
        return {"error": "Missing user_id"}, 400
    if not db.get_user_by_id(uid):
        return {"error": "User not found"}, 404
    revoked = db.revoke_all_refresh_tokens(uid)
    return {
        "status": "ok",
        "user_id": uid,
        "revoked_refresh_tokens": int(revoked),
    }, 200

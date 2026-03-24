"""
管理后台通用 helper。
"""

from __future__ import annotations

import importlib.util
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from flask import request

from core.ip_region import normalize_region_text
from core.utils import safe_float


def make_invite_code(length: int = 10) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def load_script_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return True
        if raw in {"0", "false", "no", "off"}:
            return False
    raise ValueError("Invalid boolean value")


def json_body() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def admin_region_display(value: Any) -> str:
    normalized = normalize_region_text(value)
    return normalized or "未知"


def iso_utc(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat()


def to_cny(amount: Any, curr: Any, rates: Dict[str, Any]) -> float:
    value = safe_float(amount)
    if value == 0:
        return 0.0
    code = str(curr or "CNY").strip().upper() or "CNY"
    if code == "CNY":
        return float(value)
    rate = safe_float((rates or {}).get(code, 0))
    if rate <= 0:
        return 0.0
    return float(value * rate)


def real_user_where(alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return (
        "NOT ("
        f"COALESCE({prefix}is_admin, 0) = 1 "
        f"AND LOWER(COALESCE({prefix}username, '')) LIKE 'admin_local%'"
        ")"
    )


def has_local_anonymous_user(cursor) -> bool:
    cursor.execute(
        """
        SELECT EXISTS(
            SELECT 1 FROM portfolio WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM cash_assets WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM other_assets WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM liabilities WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM transactions WHERE user_id IS NULL OR TRIM(user_id) = ''
            UNION ALL SELECT 1 FROM daily_snapshots WHERE user_id IS NULL OR TRIM(user_id) = ''
        ) AS has_local_user
        """
    )
    row = cursor.fetchone()
    return bool((row["has_local_user"] if row else 0) or 0)


def stable_params_hash(route_name: str, params: Dict[str, Any]) -> tuple[str, str]:
    normalized = {
        str(key): str(value)
        for key, value in params.items()
        if str(key).strip().lower() != "force"
    }
    payload = json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    import hashlib

    digest = hashlib.sha1(f"{route_name}|{payload}".encode("utf-8")).hexdigest()
    return f"{route_name}:{digest}", digest

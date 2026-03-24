"""Admin API policy service."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

ALLOWED_POLICY_SCOPES = {
    "upstream.price",
    "upstream.rate",
    "upstream.news",
    "api.auth",
    "api.portfolio",
    "api.news",
}

_LIMIT_RANGE = (1, 6000)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False
    raise ValueError("Invalid boolean value")


def _validate_scope_key(scope_key: str) -> str:
    key = str(scope_key or "").strip()
    if key not in ALLOWED_POLICY_SCOPES:
        raise ValueError("Unsupported scope_key")
    return key


def _normalize_limit(limit_per_min: Any) -> int:
    value = int(limit_per_min)
    if value < _LIMIT_RANGE[0] or value > _LIMIT_RANGE[1]:
        raise ValueError(f"limit_per_min must be {_LIMIT_RANGE[0]}-{_LIMIT_RANGE[1]}")
    return value


def list_policies(db, scope_type: str = "all") -> Dict[str, Any]:
    items = db.list_admin_api_policies(scope_type=scope_type)
    for item in items:
        item["enabled"] = bool(item.get("enabled"))
    return {"items": items}


def update_policy(
    db,
    scope_key: str,
    payload: Dict[str, Any],
    updated_by: str,
) -> Tuple[Dict[str, Any], int]:
    try:
        key = _validate_scope_key(scope_key)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    enabled = None
    if "enabled" in payload:
        try:
            enabled = _to_bool(payload.get("enabled"))
        except ValueError as exc:
            return {"error": str(exc)}, 400

    limit_per_min = None
    if "limit_per_min" in payload:
        raw_limit = payload.get("limit_per_min")
        if raw_limit in (None, "", 0, "0"):
            limit_per_min = None
        else:
            try:
                limit_per_min = _normalize_limit(raw_limit)
            except (TypeError, ValueError) as exc:
                return {"error": str(exc)}, 400

    note = None
    if "note" in payload:
        note = str(payload.get("note") or "").strip()[:500]

    if enabled is None and limit_per_min is None and note is None:
        return {"error": "No updatable fields"}, 400

    policy = db.update_admin_api_policy(
        key,
        enabled=enabled,
        limit_per_min=limit_per_min,
        note=note,
        updated_by=updated_by,
    )
    if not policy:
        return {"error": "Policy not found"}, 404
    policy["enabled"] = bool(policy.get("enabled"))
    return {"status": "ok", "policy": policy}, 200


def batch_update_policies(
    db,
    items: List[Dict[str, Any]],
    updated_by: str,
) -> Tuple[Dict[str, Any], int]:
    if not isinstance(items, list) or not items:
        return {"error": "Missing items"}, 400

    updated = []
    for item in items:
        if not isinstance(item, dict):
            return {"error": "Invalid items payload"}, 400
        scope_key = item.get("scope_key")
        if not scope_key:
            return {"error": "Missing scope_key"}, 400
        resp, code = update_policy(db, str(scope_key), item, updated_by)
        if code != 200:
            return resp, code
        updated.append(resp["policy"])

    return {"status": "ok", "updated_count": len(updated), "items": updated}, 200

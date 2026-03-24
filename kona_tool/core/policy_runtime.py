"""Runtime helpers for API/upstream policy checks."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

_CACHE_TTL_SECONDS = 3.0
_cache_lock = threading.Lock()
_policy_cache: Dict[str, Dict[str, Any]] = {}
_policy_cache_ts: Dict[str, float] = {}


def _load_policy(scope_key: str) -> Optional[Dict[str, Any]]:
    from core.db import db as global_db

    return global_db.get_admin_api_policy(scope_key)


def get_policy(scope_key: str) -> Optional[Dict[str, Any]]:
    key = str(scope_key or "").strip()
    if not key:
        return None
    now = time.time()
    with _cache_lock:
        ts = _policy_cache_ts.get(key, 0.0)
        if now - ts < _CACHE_TTL_SECONDS and key in _policy_cache:
            return _policy_cache[key]

    policy = _load_policy(key)
    if policy is None:
        return None
    with _cache_lock:
        _policy_cache[key] = policy
        _policy_cache_ts[key] = now
    return policy


def invalidate_policy_cache(scope_key: str = "") -> None:
    key = str(scope_key or "").strip()
    with _cache_lock:
        if key:
            _policy_cache.pop(key, None)
            _policy_cache_ts.pop(key, None)
            return
        _policy_cache.clear()
        _policy_cache_ts.clear()


def is_policy_enabled(scope_key: str, default: bool = True) -> bool:
    policy = get_policy(scope_key)
    if not policy:
        return bool(default)
    return bool(policy.get("enabled"))


def get_policy_limit_per_min(scope_key: str) -> Optional[int]:
    policy = get_policy(scope_key)
    if not policy:
        return None
    raw = policy.get("limit_per_min")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None

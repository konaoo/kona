"""
管理后台读缓存。
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, Tuple

from flask import current_app, request

import config
from core.admin.common import coerce_bool, stable_params_hash
from core.admin.constants import ADMIN_PORTFOLIO_CACHE_TTL_SECONDS


_ADMIN_READ_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_ADMIN_READ_CACHE_LOCK = threading.Lock()
_ADMIN_PORTFOLIO_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_ADMIN_PORTFOLIO_CACHE_LOCK = threading.Lock()
_ADMIN_LOGGER = logging.getLogger(__name__)


def admin_cache_ttl_seconds() -> int:
    try:
        ttl = int(getattr(config, "ADMIN_READ_CACHE_TTL_SECONDS", 120))
    except Exception:
        ttl = 120
    return max(0, min(ttl, 3600))


def admin_parse_force_arg() -> bool:
    raw = str(request.args.get("force", "") or "").strip()
    if not raw:
        return False
    return coerce_bool(raw)


def admin_cache_key(route_name: str, params: Dict[str, Any]) -> Tuple[str, str]:
    return stable_params_hash(route_name, params)


def clear_admin_caches() -> None:
    with _ADMIN_READ_CACHE_LOCK:
        _ADMIN_READ_CACHE.clear()
    with _ADMIN_PORTFOLIO_CACHE_LOCK:
        _ADMIN_PORTFOLIO_CACHE.clear()


def cached_payload(
    route_name: str,
    params: Dict[str, Any],
    force: bool,
    loader: Callable[[], Dict[str, Any]],
) -> Tuple[Dict[str, Any], str, str, int]:
    ttl = admin_cache_ttl_seconds()
    cache_key, params_hash = admin_cache_key(route_name, params)
    started = time.perf_counter()
    if not force and ttl > 0:
        now_ts = time.time()
        with _ADMIN_READ_CACHE_LOCK:
            hit = _ADMIN_READ_CACHE.get(cache_key)
            if hit and hit[0] > now_ts:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                return dict(hit[1]), "HIT", params_hash, elapsed_ms
            if hit:
                _ADMIN_READ_CACHE.pop(cache_key, None)

    payload = loader()
    if ttl > 0:
        expires_at = time.time() + ttl
        with _ADMIN_READ_CACHE_LOCK:
            _ADMIN_READ_CACHE[cache_key] = (expires_at, dict(payload))
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    cache_state = "BYPASS" if force or ttl <= 0 else "MISS"
    return payload, cache_state, params_hash, elapsed_ms


def log_admin_read(route_name: str, cache_state: str, elapsed_ms: int, params_hash: str) -> None:
    try:
        current_app.logger.info(
            "admin_read route=%s cache=%s elapsed_ms=%s params_hash=%s",
            route_name,
            cache_state,
            elapsed_ms,
            params_hash,
        )
    except Exception:
        _ADMIN_LOGGER.debug("admin_read log skipped", exc_info=True)


def get_cached_portfolio(user_id: str) -> Dict[str, Any] | None:
    if ADMIN_PORTFOLIO_CACHE_TTL_SECONDS <= 0:
        return None
    now_ts = time.time()
    with _ADMIN_PORTFOLIO_CACHE_LOCK:
        cached = _ADMIN_PORTFOLIO_CACHE.get(user_id)
        if cached and cached[0] > now_ts:
            return dict(cached[1])
        if cached:
            _ADMIN_PORTFOLIO_CACHE.pop(user_id, None)
    return None


def set_cached_portfolio(user_id: str, payload: Dict[str, Any]) -> None:
    expires_at_ts = time.time() + ADMIN_PORTFOLIO_CACHE_TTL_SECONDS
    with _ADMIN_PORTFOLIO_CACHE_LOCK:
        _ADMIN_PORTFOLIO_CACHE[user_id] = (expires_at_ts, dict(payload))

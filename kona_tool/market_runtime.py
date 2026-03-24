"""市场状态运行时。

负责承接：
- 市场状态缓存
- 市场状态强制刷新
"""

from __future__ import annotations

from datetime import datetime, timezone
import threading
import time
from typing import Any, Callable, Dict


class MarketRuntime:
    """封装市场状态缓存运行时。"""

    def __init__(
        self,
        *,
        market_scope: list[str],
        market_statuses_getter: Callable[[list[str]], dict] | Callable[..., dict],
        all_markets_closed_getter: Callable[[list[str]], bool] | Callable[..., bool],
        time_getter: Callable[[], float] | None = None,
        cache_ttl_seconds: float = 5.0,
    ) -> None:
        self.market_scope = list(market_scope)
        self.market_statuses_getter = market_statuses_getter
        self.all_markets_closed_getter = all_markets_closed_getter
        self.time_getter = time_getter or time.time
        self.cache_ttl_seconds = cache_ttl_seconds

        self._market_status_lock = threading.Lock()
        self._market_status_cache: Dict[str, Any] = {}

    def get_market_status_cached(
        self,
        now_utc: datetime | None = None,
        *,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        now = now_utc or datetime.now(timezone.utc)
        now_ts = self.time_getter()
        if not force_refresh:
            with self._market_status_lock:
                cached_at = float(self._market_status_cache.get("cached_at", 0.0) or 0.0)
                if self._market_status_cache and (now_ts - cached_at) < self.cache_ttl_seconds:
                    return dict(self._market_status_cache.get("payload", {}))

        markets = self.market_statuses_getter(self.market_scope, now=now)
        payload = {
            "server_time_utc": now.isoformat(),
            "markets": markets,
            "all_closed": self.all_markets_closed_getter(self.market_scope, now=now),
        }
        with self._market_status_lock:
            self._market_status_cache["cached_at"] = now_ts
            self._market_status_cache["payload"] = payload
        return dict(payload)


def create_market_runtime(**kwargs) -> MarketRuntime:
    return MarketRuntime(**kwargs)

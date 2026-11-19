"""
数据源健康监控与熔断
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any

import config


_OVERSEAS_SOURCES = {
    "morningstar_fund_history", "fidelity_fund_history", "ft_fund", "ft_metadata",
    "marketscreener_fund", "marketscreener_fund_api", "yahoo_us_history", "stooq_us_history",
}


class SourceHealth:
    def __init__(self, fail_threshold: int = 3, cooldown_seconds: int = 30):
        self._fail_threshold = max(1, fail_threshold)
        self._cooldown_seconds = max(1, cooldown_seconds)
        self._lock = threading.Lock()
        self._stats: Dict[str, Dict[str, Any]] = {}

    def _ensure(self, source: str) -> Dict[str, Any]:
        if source not in self._stats:
            self._stats[source] = {
                "ok": 0,
                "fail": 0,
                "timeout": 0,
                "consecutive_fail": 0,
                "latency_avg_ms": 0.0,
                "last_error": "",
                "last_ok_at": "",
                "last_fail_at": "",
                "circuit_open_until": 0.0,
                "circuit_trips": 0,
                "probe_until": 0.0,
                "skipped": 0,
                "last_status_code": None,
            }
        return self._stats[source]

    def _policy(self, source: str) -> tuple[int, int]:
        """
        支持对慢源使用更快熔断策略，避免反复超时拖慢请求。
        """
        slow_sources = {"nasdaq_quote", "ft_fund"}
        if source in slow_sources:
            return (
                max(1, int(getattr(config, "SLOW_SOURCE_FAIL_THRESHOLD", self._fail_threshold))),
                max(1, int(getattr(config, "SLOW_SOURCE_COOLDOWN_SECONDS", self._cooldown_seconds))),
            )
        return self._fail_threshold, self._cooldown_seconds

    def can_attempt(self, source: str) -> bool:
        with self._lock:
            info = self._ensure(source)
            now = time.time()
            if now < max(info["circuit_open_until"], info["probe_until"]):
                info["skipped"] += 1
                return False
            if source in _OVERSEAS_SOURCES and info["circuit_trips"]:
                # 冷却结束只放行一个探测；租约防止异常中断后永久锁住。
                info["probe_until"] = now + max(30.0, float(config.API_TIMEOUT) * 2)
            return True

    def record(
        self,
        source: str,
        success: bool,
        duration_ms: float = 0.0,
        timeout: bool = False,
        error: str = "",
        status_code: int | None = None,
        retry_after_seconds: float = 0.0,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        fail_threshold, cooldown_seconds = self._policy(source)
        with self._lock:
            info = self._ensure(source)
            info["probe_until"] = 0.0
            info["last_status_code"] = status_code
            if success:
                info["ok"] += 1
                info["consecutive_fail"] = 0
                info["last_ok_at"] = now
                info["last_error"] = ""
                old = float(info.get("latency_avg_ms", 0.0))
                info["latency_avg_ms"] = duration_ms if old <= 0 else (old * 0.8 + duration_ms * 0.2)
                info["circuit_open_until"] = 0.0
                info["circuit_trips"] = 0
                return

            info["fail"] += 1
            info["consecutive_fail"] += 1
            info["last_fail_at"] = now
            info["last_error"] = error[:160]
            if timeout:
                info["timeout"] += 1
            blocked = status_code in (403, 429)
            if info["consecutive_fail"] >= fail_threshold or (source in _OVERSEAS_SOURCES and blocked):
                if source in _OVERSEAS_SOURCES:
                    info["circuit_trips"] += 1
                    base = max(cooldown_seconds, config.OVERSEAS_SOURCE_COOLDOWN_SECONDS)
                    cooldown_seconds = min(
                        config.OVERSEAS_SOURCE_MAX_COOLDOWN_SECONDS,
                        max(base * (2 ** min(info["circuit_trips"] - 1, 6)),
                            config.OVERSEAS_SOURCE_BLOCKED_COOLDOWN_SECONDS if blocked else 0,
                            retry_after_seconds),
                    )
                info["circuit_open_until"] = time.time() + cooldown_seconds

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            out: Dict[str, Dict[str, Any]] = {}
            for source, info in self._stats.items():
                out[source] = dict(info)
                out[source]["circuit_open"] = time.time() < float(info.get("circuit_open_until", 0.0))
            return out

    def reset(self) -> None:
        with self._lock:
            self._stats.clear()


source_health = SourceHealth(
    fail_threshold=config.SOURCE_FAIL_THRESHOLD,
    cooldown_seconds=config.SOURCE_COOLDOWN_SECONDS,
)

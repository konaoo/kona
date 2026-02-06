"""
数据源健康监控与熔断
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any

import config


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
            }
        return self._stats[source]

    def can_attempt(self, source: str) -> bool:
        with self._lock:
            info = self._ensure(source)
            return time.time() >= float(info.get("circuit_open_until", 0.0))

    def record(
        self,
        source: str,
        success: bool,
        duration_ms: float = 0.0,
        timeout: bool = False,
        error: str = "",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            info = self._ensure(source)
            if success:
                info["ok"] += 1
                info["consecutive_fail"] = 0
                info["last_ok_at"] = now
                info["last_error"] = ""
                old = float(info.get("latency_avg_ms", 0.0))
                info["latency_avg_ms"] = duration_ms if old <= 0 else (old * 0.8 + duration_ms * 0.2)
                info["circuit_open_until"] = 0.0
                return

            info["fail"] += 1
            info["consecutive_fail"] += 1
            info["last_fail_at"] = now
            info["last_error"] = error[:160]
            if timeout:
                info["timeout"] += 1
            if info["consecutive_fail"] >= self._fail_threshold:
                info["circuit_open_until"] = time.time() + self._cooldown_seconds

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


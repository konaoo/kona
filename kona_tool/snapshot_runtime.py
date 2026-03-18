"""快照运行时服务。

负责承接：
- 单用户快照保存
- 异步快照节流与防并发
- 后台定时任务单次执行与循环调度
"""

from __future__ import annotations

from datetime import datetime
import threading
import time
from typing import Any, Callable


class SnapshotRuntime:
    """封装快照保存和后台调度的运行时逻辑。"""

    def __init__(
        self,
        *,
        db: Any,
        logger: Any,
        calculate_portfolio_stats: Callable[[str | None], dict],
        app_testing_getter: Callable[[], bool],
        background_snapshot_runner: Callable[[], Any],
        provider_test_runner: Callable[[], Any] | None = None,
        time_getter: Callable[[], float] | None = None,
        sleep_func: Callable[[float], None] | None = None,
        thread_factory: Callable[..., Any] | None = None,
        min_interval_seconds: float = 3.0,
    ) -> None:
        self.db = db
        self.logger = logger
        self.calculate_portfolio_stats = calculate_portfolio_stats
        self.app_testing_getter = app_testing_getter
        self.background_snapshot_runner = background_snapshot_runner
        self.provider_test_runner = provider_test_runner
        self.time_getter = time_getter or time.time
        self.sleep_func = sleep_func or time.sleep
        self.thread_factory = thread_factory or threading.Thread
        self.min_interval_seconds = min_interval_seconds

        self._snapshot_lock = threading.Lock()
        self._snapshot_inflight: set[str] = set()
        self._snapshot_last_run_ts: dict[str, float] = {}

    def save_snapshot_for_user(self, user_id: str | None = None) -> None:
        """保存用户当日快照。"""
        try:
            stats = self.calculate_portfolio_stats(user_id)
            snapshot_date = str(stats.get("snapshot_date") or datetime.now().strftime("%Y-%m-%d"))
            saved = self.db.save_daily_snapshot(stats, user_id, snapshot_date=snapshot_date)
            if saved:
                snapshot_date = str(stats.get("snapshot_date") or datetime.now().strftime("%Y-%m-%d"))
                breakdown_ok = self.db.save_daily_snapshot_market_breakdown(
                    date_str=snapshot_date,
                    day_pnl_by_market=stats.get("day_pnl_by_market") or {},
                    total_day_pnl=float(stats.get("day_pnl", 0.0) or 0.0),
                    user_id=user_id,
                    source="exact",
                    confidence=1.0,
                )
                if not breakdown_ok:
                    self.logger.warning(
                        "Snapshot market breakdown save failed: user_id=%s date=%s",
                        user_id,
                        snapshot_date,
                    )
        except Exception as exc:
            self.logger.warning("Snapshot save failed: %s", exc)

    def save_snapshot_for_user_async(self, user_id: str | None = None) -> None:
        """异步保存用户快照，避免阻塞资产接口响应。"""
        if self.app_testing_getter():
            self.save_snapshot_for_user(user_id)
            return

        uid = user_id or ""
        now_ts = self.time_getter()
        with self._snapshot_lock:
            last_run = self._snapshot_last_run_ts.get(uid, 0.0)
            if uid in self._snapshot_inflight:
                self.logger.info("[snapshot_skip_inflight] user_id=%s", uid)
                return
            if now_ts - last_run < self.min_interval_seconds:
                self.logger.info("[snapshot_skip_throttle] user_id=%s interval=%.2fs", uid, now_ts - last_run)
                return
            self._snapshot_inflight.add(uid)

        def _worker():
            try:
                self.save_snapshot_for_user(user_id if uid else None)
            finally:
                with self._snapshot_lock:
                    self._snapshot_inflight.discard(uid)
                    self._snapshot_last_run_ts[uid] = self.time_getter()

        worker = self.thread_factory(target=_worker, daemon=True)
        worker.start()

    def run_background_scheduler_once(
        self,
        *,
        enable_background_snapshot: bool,
        enable_background_provider_test: bool,
    ) -> None:
        if enable_background_snapshot:
            try:
                self.background_snapshot_runner()
            except Exception as exc:
                self.logger.error("Snapshot scheduler error: %s", exc)

        if enable_background_provider_test and self.provider_test_runner is not None:
            try:
                self.provider_test_runner()
            except Exception as exc:
                self.logger.error("Provider test scheduler error: %s", exc)

    def background_scheduler(
        self,
        *,
        enable_background_snapshot_getter: Callable[[], bool],
        enable_background_provider_test_getter: Callable[[], bool],
        interval_seconds: float = 3600.0,
    ) -> None:
        """后台任务调度循环。"""
        self.logger.info("Scheduler started")
        while True:
            self.run_background_scheduler_once(
                enable_background_snapshot=enable_background_snapshot_getter(),
                enable_background_provider_test=enable_background_provider_test_getter(),
            )
            self.sleep_func(interval_seconds)


def create_snapshot_runtime(**kwargs) -> SnapshotRuntime:
    return SnapshotRuntime(**kwargs)

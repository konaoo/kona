import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from snapshot_runtime import create_snapshot_runtime  # noqa: E402


class _FakeDb:
    def __init__(self):
        self.saved_stats = []
        self.saved_breakdowns = []

    def save_daily_snapshot(self, stats, user_id):
        self.saved_stats.append({"stats": stats, "user_id": user_id})
        return True

    def save_daily_snapshot_market_breakdown(self, **kwargs):
        self.saved_breakdowns.append(kwargs)
        return True


class _FakeLogger:
    def __init__(self):
        self.info_messages = []
        self.warning_messages = []
        self.error_messages = []

    def info(self, message, *args):
        self.info_messages.append(message % args if args else message)

    def warning(self, message, *args):
        self.warning_messages.append(message % args if args else message)

    def error(self, message, *args):
        self.error_messages.append(message % args if args else message)


class _ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self.target = target
        self.daemon = daemon

    def start(self):
        if self.target is not None:
            self.target()


class SnapshotRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.db = _FakeDb()
        self.logger = _FakeLogger()
        self.now = 1_700_000_000.0
        self.snapshot_calls = []
        self.provider_calls = []
        self.runtime = create_snapshot_runtime(
            db=self.db,
            logger=self.logger,
            calculate_portfolio_stats=self._calculate_stats,
            app_testing_getter=lambda: False,
            background_snapshot_runner=lambda: self.snapshot_calls.append("snapshot"),
            provider_test_runner=lambda: self.provider_calls.append("provider"),
            time_getter=lambda: self.now,
            thread_factory=_ImmediateThread,
            min_interval_seconds=3.0,
        )

    def _calculate_stats(self, user_id):
        return {
            "snapshot_date": "2026-03-14",
            "day_pnl": 12.34,
            "day_pnl_by_market": {"a": 12.34},
            "user_id": user_id,
        }

    def test_save_snapshot_for_user_writes_snapshot_and_breakdown(self):
        self.runtime.save_snapshot_for_user("u_1")

        self.assertEqual(len(self.db.saved_stats), 1)
        self.assertEqual(self.db.saved_stats[0]["user_id"], "u_1")
        self.assertEqual(len(self.db.saved_breakdowns), 1)
        self.assertEqual(self.db.saved_breakdowns[0]["date_str"], "2026-03-14")
        self.assertEqual(self.db.saved_breakdowns[0]["user_id"], "u_1")

    def test_async_snapshot_uses_sync_path_in_testing_mode(self):
        testing_runtime = create_snapshot_runtime(
            db=self.db,
            logger=self.logger,
            calculate_portfolio_stats=self._calculate_stats,
            app_testing_getter=lambda: True,
            background_snapshot_runner=lambda: None,
            provider_test_runner=None,
            time_getter=lambda: self.now,
            thread_factory=_ImmediateThread,
        )

        testing_runtime.save_snapshot_for_user_async("u_test")

        self.assertEqual(len(self.db.saved_stats), 1)
        self.assertEqual(self.db.saved_stats[0]["user_id"], "u_test")

    def test_async_snapshot_throttles_same_user(self):
        self.runtime.save_snapshot_for_user_async("u_2")
        self.runtime.save_snapshot_for_user_async("u_2")

        self.assertEqual(len(self.db.saved_stats), 1)
        self.assertTrue(any("snapshot_skip_throttle" in message for message in self.logger.info_messages))

    def test_background_scheduler_once_runs_enabled_jobs(self):
        self.runtime.run_background_scheduler_once(
            enable_background_snapshot=True,
            enable_background_provider_test=True,
        )

        self.assertEqual(self.snapshot_calls, ["snapshot"])
        self.assertEqual(self.provider_calls, ["provider"])


if __name__ == "__main__":
    unittest.main()

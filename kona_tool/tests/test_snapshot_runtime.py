import sys
from pathlib import Path
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from snapshot_runtime import create_snapshot_runtime  # noqa: E402
from core.snapshot import _persist_ledger_snapshot_stats, persist_snapshot_stats  # noqa: E402


class _FakeDb:
    def __init__(self):
        self.saved_stats = []
        self.saved_ledger_stats = []
        self.saved_breakdowns = []
        self.saved_ledger_breakdowns = []
        self.saved_asset_breakdowns = []
        self.partial_breakdowns = []
        self.synced_dates = []
        self.synced_ledger_dates = []
        self.snapshot_dates = {"2026-03-13"}

    def save_daily_snapshot(self, stats, user_id, snapshot_date=None):
        self.saved_stats.append({"stats": stats, "user_id": user_id, "snapshot_date": snapshot_date})
        if snapshot_date:
            self.snapshot_dates.add(snapshot_date)
        return True

    def save_daily_snapshot_market_breakdown(self, **kwargs):
        self.saved_breakdowns.append(kwargs)
        return True

    def save_ledger_daily_snapshot(self, **kwargs):
        self.saved_ledger_stats.append(kwargs)
        if kwargs.get("date_str"):
            self.snapshot_dates.add(kwargs["date_str"])
        return True

    def save_daily_snapshot_asset_breakdowns(self, **kwargs):
        self.saved_asset_breakdowns.append(kwargs)
        return True

    def save_ledger_daily_snapshot_market_breakdown(self, **kwargs):
        self.saved_ledger_breakdowns.append(kwargs)
        return True

    def save_daily_snapshot_market_breakdown_partial(self, **kwargs):
        self.partial_breakdowns.append(kwargs)
        return True

    def sync_daily_snapshot_day_pnl_from_breakdown(self, date_str, user_id=None):
        self.synced_dates.append({"date_str": date_str, "user_id": user_id})
        return True

    def sync_ledger_daily_snapshot_day_pnl(self, date_str, user_id=None):
        self.synced_ledger_dates.append({"date_str": date_str, "user_id": user_id})
        return True

    def sync_ledger_daily_snapshot_day_pnl_from_breakdown(self, *, date_str, user_id=None, ledger_id=None):
        self.synced_ledger_dates.append(
            {"date_str": date_str, "user_id": user_id, "ledger_id": ledger_id}
        )
        return True

    def has_daily_snapshot(self, date_str, user_id=None):
        return date_str in self.snapshot_dates

    def get_daily_snapshot_market_breakdown_map(self, date_str, user_id=None, ledger_id=None):
        return {market: 0.0 for market in ("a", "hk", "us", "fund", "unallocated")}

    def get_daily_snapshot_asset_breakdown_rows(self, *, date_str, user_id=None, ledger_id=None):
        return []


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
            "snapshot_day_pnl": 0.0,
            "snapshot_day_pnl_by_market": {"a": 0.0, "hk": 0.0, "us": 0.0, "fund": 0.0, "unallocated": 0.0},
            "day_pnl_breakdowns_by_date": {
                "2026-03-13": {"us": -20.0, "fund": -10.0},
                "2026-03-14": {"a": 0.0, "hk": 0.0, "us": 0.0, "fund": 0.0},
            },
            "user_id": user_id,
        }

    def test_save_snapshot_for_user_writes_snapshot_and_breakdown(self):
        self.runtime.save_snapshot_for_user("u_1")

        self.assertEqual(len(self.db.saved_stats), 1)
        self.assertEqual(self.db.saved_stats[0]["user_id"], "u_1")
        self.assertEqual(len(self.db.saved_breakdowns), 2)
        self.assertEqual(self.db.saved_breakdowns[0]["date_str"], "2026-03-14")
        self.assertEqual(self.db.saved_breakdowns[0]["user_id"], "u_1")
        self.assertEqual(self.db.saved_breakdowns[1]["date_str"], "2026-03-13")
        self.assertEqual(self.db.saved_breakdowns[1]["day_pnl_by_market"], {"a": 0.0, "hk": 0.0, "us": -20.0, "fund": -10.0})
        self.assertEqual(len(self.db.partial_breakdowns), 0)
        self.assertEqual(len(self.db.synced_dates), 1)
        self.assertEqual(self.db.synced_dates[0]["date_str"], "2026-03-13")

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

    def test_persist_snapshot_stats_moves_preopen_a_share_pnl_back_to_previous_day(self):
        stats = {
            "snapshot_date": "2026-03-24",
            "snapshot_day_pnl": 100.0,
            "snapshot_day_pnl_by_market": {"a": 100.0, "hk": 0.0, "us": 0.0, "fund": 0.0, "unallocated": 0.0},
            "day_pnl_breakdowns_by_date": {
                "2026-03-24": {"a": 100.0, "hk": 0.0, "us": 0.0, "fund": 0.0, "unallocated": 0.0},
            },
            "now_utc": datetime(2026, 3, 24, 0, 30, tzinfo=timezone.utc),
        }
        statuses = {
            "a": {"open": False, "trading_day": True, "reason": "off_hours"},
            "hk": {"open": False, "trading_day": True, "reason": "off_hours"},
            "us": {"open": False, "trading_day": True, "reason": "off_hours"},
            "fund": {"open": False, "trading_day": True, "reason": "off_hours"},
        }
        self.db.snapshot_dates.add("2026-03-23")

        with patch("core.snapshot.get_market_statuses", return_value=statuses):
            with patch("core.snapshot.get_previous_trading_day") as mocked_prev:
                mocked_prev.side_effect = lambda market, target_date: datetime(2026, 3, 23).date()
                ok = persist_snapshot_stats(self.db, self.logger, stats, user_id="u_preopen")

        self.assertTrue(ok)
        self.assertEqual(len(self.db.saved_stats), 1)
        self.assertAlmostEqual(float(self.db.saved_stats[0]["stats"]["day_pnl"]), 0.0, places=2)
        self.assertEqual(len(self.db.saved_breakdowns), 2)
        self.assertAlmostEqual(float(self.db.saved_breakdowns[0]["day_pnl_by_market"]["a"]), 0.0, places=2)
        self.assertEqual(self.db.saved_breakdowns[1]["date_str"], "2026-03-23")
        self.assertEqual(self.db.saved_breakdowns[1]["day_pnl_by_market"], {"a": 100.0, "hk": 0.0, "us": 0.0, "fund": 0.0})
        self.assertEqual(len(self.db.partial_breakdowns), 0)
        self.assertEqual(len(self.db.synced_dates), 1)
        self.assertEqual(self.db.synced_dates[0]["date_str"], "2026-03-23")

    def test_persist_snapshot_stats_replaces_asset_breakdowns_when_late_settlement_backfills_prior_date(self):
        stats = {
            "snapshot_date": "2026-03-27",
            "snapshot_day_pnl": 0.0,
            "snapshot_day_pnl_by_market": {
                "a": 0.0,
                "hk": 0.0,
                "us": 0.0,
                "fund": 0.0,
                "unallocated": 0.0,
            },
            "day_pnl_breakdowns_by_date": {
                "2026-03-26": {"a": 0.0, "hk": 0.0, "us": -100.0, "fund": -200.0},
                "2026-03-27": {"a": 0.0, "hk": 0.0, "us": 0.0, "fund": 0.0},
            },
            "asset_day_breakdowns_by_date": {
                "2026-03-26": [
                    {"code": "gb_qqq", "name": "QQQ", "market": "us", "curr": "USD", "day_pnl": -100.0, "day_base": 1000.0},
                    {"code": "f_110018", "name": "增强回报", "market": "fund", "curr": "CNY", "day_pnl": -200.0, "day_base": 2000.0},
                ],
                "2026-03-27": [],
            },
            "now_utc": datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
        }
        self.db.snapshot_dates.add("2026-03-26")

        with patch("core.snapshot.get_market_statuses", return_value={}):
            ok = persist_snapshot_stats(self.db, self.logger, stats, user_id="u_late")

        self.assertTrue(ok)
        self.assertEqual(len(self.db.saved_breakdowns), 2)
        self.assertEqual(self.db.saved_breakdowns[1]["date_str"], "2026-03-26")
        self.assertEqual(
            self.db.saved_breakdowns[1]["day_pnl_by_market"],
            {"a": 0.0, "hk": 0.0, "us": -100.0, "fund": -200.0},
        )
        self.assertEqual(len(self.db.partial_breakdowns), 0)
        self.assertEqual(len(self.db.saved_asset_breakdowns), 2)
        prior_day_calls = [
            item for item in self.db.saved_asset_breakdowns if item["date_str"] == "2026-03-26"
        ]
        self.assertEqual(len(prior_day_calls), 1)
        self.assertTrue(all(item.get("replace_existing") is True for item in prior_day_calls))
        self.assertEqual({item["market"] for item in prior_day_calls[0]["items"]}, {"us", "fund"})
        self.assertTrue(all(item["snapshot_date"] == "2026-03-27" for item in prior_day_calls))

    def test_persist_ledger_snapshot_stats_backfills_prior_date_with_full_day_breakdown(self):
        stats = {
            "snapshot_date": "2026-03-27",
            "total_cost": 1000.0,
            "total_pnl": 50.0,
            "total_invest": 1050.0,
            "holdings_count": 1,
            "day_pnl_breakdowns_by_date": {
                "2026-03-26": {"a": 120.0, "hk": 0.0, "us": 0.0, "fund": -30.0},
                "2026-03-27": {"a": 0.0, "hk": 0.0, "us": 0.0, "fund": 0.0},
            },
            "asset_day_breakdowns_by_date": {
                "2026-03-26": [
                    {"code": "sz_000001", "name": "平安银行", "market": "a", "curr": "CNY", "day_pnl": 120.0, "day_base": 1000.0},
                    {"code": "f_110018", "name": "增强回报", "market": "fund", "curr": "CNY", "day_pnl": -30.0, "day_base": 300.0},
                ],
                "2026-03-27": [],
            },
            "now_utc": datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
        }

        with patch("core.snapshot.get_market_statuses", return_value={}):
            with patch("core.snapshot._has_ledger_daily_snapshot", return_value=True):
                ok, handled_dates = _persist_ledger_snapshot_stats(
                    self.db,
                    self.logger,
                    stats,
                    user_id="u_late",
                    ledger_id=62,
                )

        self.assertTrue(ok)
        self.assertEqual(handled_dates, {"2026-03-26", "2026-03-27"})
        self.assertEqual(len(self.db.saved_ledger_stats), 1)
        self.assertEqual(len(self.db.saved_ledger_breakdowns), 2)
        self.assertEqual(self.db.saved_ledger_breakdowns[1]["date_str"], "2026-03-26")
        self.assertEqual(
            self.db.saved_ledger_breakdowns[1]["day_pnl_by_market"],
            {"a": 120.0, "hk": 0.0, "us": 0.0, "fund": -30.0},
        )
        prior_day_asset_calls = [
            item for item in self.db.saved_asset_breakdowns
            if item["date_str"] == "2026-03-26" and item.get("ledger_id") == 62
        ]
        self.assertEqual(len(prior_day_asset_calls), 1)
        self.assertTrue(prior_day_asset_calls[0].get("replace_existing"))
        self.assertEqual(len(self.db.partial_breakdowns), 0)
        self.assertEqual(
            self.db.synced_ledger_dates,
            [{"date_str": "2026-03-26", "user_id": "u_late", "ledger_id": 62}],
        )


if __name__ == "__main__":
    unittest.main()

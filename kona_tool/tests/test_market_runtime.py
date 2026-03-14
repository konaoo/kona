import sys
from datetime import datetime, timezone
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from market_runtime import create_market_runtime  # noqa: E402


class MarketRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.now_ts = 1_700_000_000.0
        self.market_calls = []
        self.closed_calls = []
        self.runtime = create_market_runtime(
            market_scope=["a", "hk", "us", "fund"],
            market_statuses_getter=self._get_markets,
            all_markets_closed_getter=self._all_closed,
            time_getter=lambda: self.now_ts,
            cache_ttl_seconds=5.0,
        )

    def _get_markets(self, scope, now=None):
        self.market_calls.append({"scope": list(scope), "now": now})
        return {"a": {"open": False, "reason": "holiday"}}

    def _all_closed(self, scope, now=None):
        self.closed_calls.append({"scope": list(scope), "now": now})
        return True

    def test_market_status_result_is_cached_within_ttl(self):
        now_utc = datetime(2026, 3, 14, tzinfo=timezone.utc)
        first = self.runtime.get_market_status_cached(now_utc=now_utc)
        second = self.runtime.get_market_status_cached(now_utc=now_utc)

        self.assertEqual(first["all_closed"], True)
        self.assertEqual(second["markets"]["a"]["reason"], "holiday")
        self.assertEqual(len(self.market_calls), 1)
        self.assertEqual(len(self.closed_calls), 1)

    def test_market_status_force_refresh_bypasses_cache(self):
        now_utc = datetime(2026, 3, 14, tzinfo=timezone.utc)
        self.runtime.get_market_status_cached(now_utc=now_utc)
        self.runtime.get_market_status_cached(now_utc=now_utc, force_refresh=True)

        self.assertEqual(len(self.market_calls), 2)
        self.assertEqual(len(self.closed_calls), 2)


if __name__ == "__main__":
    unittest.main()

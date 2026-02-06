import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import core.price as price
from core.source_health import source_health


class TestPriceResilience(unittest.TestCase):
    def setUp(self):
        price.price_cache.clear()
        source_health.reset()

    def test_fallback_to_stale_price_when_fetch_fails(self):
        code = "sh600000"
        stale = (11.0, 10.0, 1.0, 10.0)
        price.price_cache.set(code, stale)

        # Force cache entry stale but still inside stale-ttl window.
        data, ts = price.price_cache.cache[code]
        price.price_cache.cache[code] = (data, ts - (price.price_cache.ttl + 1))

        with patch("core.price.get_stock_price", return_value=(0.0, 0.0, 0.0, 0.0)):
            got = price.get_price(code)

        self.assertEqual(got, stale)
        metrics = price.get_price_runtime_metrics()
        self.assertGreaterEqual(metrics.get("stale_hits", 0), 1)

    def test_source_health_snapshot_has_expected_fields(self):
        source_health.record("test_source", success=False, timeout=True, error="timeout")
        source_health.record("test_source", success=True, duration_ms=12.5)
        snap = source_health.snapshot()
        self.assertIn("test_source", snap)
        self.assertIn("ok", snap["test_source"])
        self.assertIn("fail", snap["test_source"])
        self.assertIn("timeout", snap["test_source"])
        self.assertIn("latency_avg_ms", snap["test_source"])


if __name__ == "__main__":
    unittest.main()


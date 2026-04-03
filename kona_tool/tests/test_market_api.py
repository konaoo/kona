import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class MarketApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def test_market_status_endpoint(self):
        mocked_markets = {
            "a": {"open": False, "reason": "holiday_or_weekend"},
            "hk": {"open": False, "reason": "holiday_or_weekend"},
            "us": {"open": False, "reason": "off_hours"},
            "fund": {"open": False, "reason": "holiday_or_weekend"},
        }
        with patch.object(
            app_module.market_runtime,
            "get_market_status_cached",
            return_value={
                "server_time_utc": "2026-03-14T00:00:00+00:00",
                "all_closed": True,
                "markets": mocked_markets,
            },
        ):
            resp = self.client.get('/api/market/status')
            self.assertEqual(resp.status_code, 200)
            body = resp.get_json() or {}
            self.assertIn("server_time_utc", body)
            self.assertEqual(body.get("all_closed"), True)
            markets = body.get("markets") or {}
            self.assertEqual((markets.get("a") or {}).get("open"), False)
            self.assertEqual((markets.get("a") or {}).get("reason"), "holiday_or_weekend")
            self.assertEqual((markets.get("us") or {}).get("reason"), "off_hours")
            self.assertGreater(int(resp.headers.get('X-Trace-Stage-Count', '0')), 0)

    def test_market_indices_endpoint(self):
        with patch.object(
            app_module,
            "batch_get_prices",
            return_value={
                # 价格接口已标准化为 5 元组：(price, yclose, amt, pct, nav_date)
                's_sh000001': (3200.0, 3190.0, 10.0, 0.31, None),
                's_sz399001': (10100.0, 10000.0, 100.0, 1.0, None),
                's_sz399006': (2000.0, 1980.0, 20.0, 1.01, None),
                'gb_ixic': (17000.0, 16900.0, 100.0, 0.59, None),
            },
        ), patch.object(
            app_module,
            "get_hstech_price",
            return_value=(3500.0, 3480.0, 20.0, 0.57, None),
        ), patch.object(
            app_module,
            "get_forex_rates",
            return_value={"USD": 7.2},
        ):
            resp = self.client.get('/api/market/indices')
            self.assertEqual(resp.status_code, 200)
            items = resp.get_json() or []
            self.assertEqual(len(items), 6)
            self.assertEqual(items[0].get('name'), '上证指数')
            self.assertEqual(items[3].get('name'), '恒生科技')
            self.assertEqual(items[-1].get('name'), 'USD/CNY')
            self.assertEqual(items[-1].get('value'), 7.2)
            self.assertGreater(int(resp.headers.get('X-Trace-Stage-Count', '0')), 0)


if __name__ == '__main__':
    unittest.main()

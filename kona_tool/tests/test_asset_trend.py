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

from core.trend import _resolve_tencent_symbol, _fetch_stock_history_points


class _JsonResp:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


class AssetTrendTests(unittest.TestCase):
    def test_resolve_tencent_symbol_supports_hk_suffix_code(self):
        market, symbol = _resolve_tencent_symbol("00175.HK", "hk")
        self.assertEqual(market, "hk")
        self.assertEqual(symbol, "hk00175")

    def test_fallbacks_to_tencent_when_eastmoney_history_is_empty(self):
        eastmoney_empty = _JsonResp({"data": {"klines": []}})
        tencent_payload = _JsonResp(
            {
                "data": {
                    "hk00175": {
                        "qfqday": [
                            ["2026-03-04", "15.660", "15.430", "15.800", "15.300", "1"],
                            ["2026-03-05", "15.500", "15.150", "15.570", "14.910", "1"],
                            ["2026-03-06", "15.330", "16.360", "16.560", "15.250", "1"],
                        ]
                    }
                }
            }
        )

        with patch("core.trend.monitored_http_get", side_effect=[eastmoney_empty, tencent_payload]):
            points = _fetch_stock_history_points("00175.HK", 3, "hk")

        self.assertEqual(
            points,
            [
                {"date": "2026-03-04", "value": 15.43},
                {"date": "2026-03-05", "value": 15.15},
                {"date": "2026-03-06", "value": 16.36},
            ],
        )


if __name__ == "__main__":
    unittest.main()

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

from core.trend import (
    _resolve_tencent_symbol,
    _fetch_stock_history_points,
    _fetch_yahoo_us_history_points,
)


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

    def test_resolve_tencent_symbol_supports_exchange_fund_with_plain_digits(self):
        market, symbol = _resolve_tencent_symbol("159655", "fund")
        self.assertEqual(market, "a")
        self.assertEqual(symbol, "sz159655")

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

    def test_us_trend_falls_back_to_tencent_when_eastmoney_points_too_sparse(self):
        eastmoney_sparse = _JsonResp(
            {
                "data": {
                    "klines": [
                        "2011-06-02,0,27.21,0,0,0,0,0",
                        "2026-03-06,0,91.98,0,0,0,0,0",
                    ]
                }
            }
        )
        tencent_payload = _JsonResp(
            {
                "data": {
                    "usSE": {
                        "qfqday": [
                            ["2026-03-04", "88.00", "88.26", "89.10", "87.80", "1"],
                            ["2026-03-05", "91.00", "95.52", "96.10", "90.80", "1"],
                            ["2026-03-06", "93.00", "91.98", "93.50", "91.20", "1"],
                        ]
                    }
                }
            }
        )

        with patch("core.trend._fetch_yahoo_us_history_points", return_value=[]), patch(
            "core.trend.monitored_http_get",
            side_effect=[eastmoney_sparse, tencent_payload],
        ):
            points = _fetch_stock_history_points("gb_se", 20, "us")

        self.assertEqual(
            points,
            [
                {"date": "2026-03-04", "value": 88.26},
                {"date": "2026-03-05", "value": 95.52},
                {"date": "2026-03-06", "value": 91.98},
            ],
        )

    def test_plain_exchange_fund_digits_with_fund_hint_can_fetch_trend_points(self):
        eastmoney_empty = _JsonResp({"data": {"klines": []}})
        tencent_payload = _JsonResp(
            {
                "data": {
                    "sz159655": {
                        "qfqday": [
                            ["2026-03-05", "1.700", "1.756", "1.780", "1.680", "1"],
                            ["2026-03-06", "1.760", "1.767", "1.780", "1.750", "1"],
                            ["2026-03-09", "1.730", "1.722", "1.731", "1.710", "1"],
                        ]
                    }
                }
            }
        )

        with patch("core.trend.monitored_http_get", side_effect=[eastmoney_empty, tencent_payload]):
            points = _fetch_stock_history_points("159655", 3, "fund")

        self.assertEqual(
            points,
            [
                {"date": "2026-03-05", "value": 1.756},
                {"date": "2026-03-06", "value": 1.767},
                {"date": "2026-03-09", "value": 1.722},
            ],
        )

    def test_fetch_yahoo_us_history_points_supports_boxx(self):
        yahoo_payload = _JsonResp(
            {
                "chart": {
                    "result": [
                        {
                            "timestamp": [1772634600, 1772721000, 1772807400],
                            "indicators": {
                                "quote": [
                                    {
                                        "close": [115.85, 115.86, 115.89],
                                    }
                                ]
                            },
                        }
                    ]
                }
            }
        )

        with patch("core.trend.monitored_http_get", return_value=yahoo_payload):
            points = _fetch_yahoo_us_history_points("gb_boxx", 20)

        self.assertEqual(
            points,
            [
                {"date": "2026-03-04", "value": 115.85},
                {"date": "2026-03-05", "value": 115.86},
                {"date": "2026-03-06", "value": 115.89},
            ],
        )


if __name__ == "__main__":
    unittest.main()

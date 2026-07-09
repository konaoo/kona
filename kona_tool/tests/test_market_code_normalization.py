import os
import sys
from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

from core.parser import parse_code
from core.asset_type import infer_asset_type, infer_category_type
from core.market_calendar import market_from_asset
from core.price import get_price, price_cache
from core.stock import get_sina_stock_price, _is_hk_quote_stale


class _MockResp:
    def __init__(self, text: str = "", status_code: int = 200, json_data=None):
        self.text = text
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data or {}


class TestMarketCodeNormalization(unittest.TestCase):
    def test_parse_code_numeric_5_defaults_to_hk(self):
        parsed = parse_code("00700", "")
        self.assertEqual(parsed["code"], "00700.HK")
        self.assertEqual(parsed["curr"], "HKD")

    def test_parse_code_hk_suffix_pads_to_5_digits(self):
        parsed = parse_code("0700.HK", "")
        self.assertEqual(parsed["code"], "00700.HK")
        self.assertEqual(parsed["curr"], "HKD")

    def test_parse_code_sh_b_share_uses_usd(self):
        parsed = parse_code("900901", "")
        self.assertEqual(parsed["code"], "sh900901")
        self.assertEqual(parsed["curr"], "USD")

    def test_parse_code_sz_b_share_uses_hkd(self):
        parsed = parse_code("200002", "")
        self.assertEqual(parsed["code"], "sz200002")
        self.assertEqual(parsed["curr"], "HKD")

    def test_parse_code_sh_b_share_forces_currency(self):
        parsed = parse_code("sh900901", "CNY")
        self.assertEqual(parsed["code"], "sh900901")
        self.assertEqual(parsed["curr"], "USD")

    def test_parse_code_sz_b_share_forces_currency(self):
        parsed = parse_code("sz200002", "CNY")
        self.assertEqual(parsed["code"], "sz200002")
        self.assertEqual(parsed["curr"], "HKD")

    def test_parse_code_16_prefix_keeps_fund_path(self):
        parsed = parse_code("161907", "")
        self.assertEqual(parsed["code"], "f_161907")
        self.assertEqual(parsed["curr"], "CNY")

    def test_parse_code_us_symbol_with_dot_uses_gb_and_usd(self):
        parsed = parse_code("BRK.B", "")
        self.assertEqual(parsed["code"], "gb_brk.b")
        self.assertEqual(parsed["curr"], "USD")

    def test_parse_code_us_symbol_with_dash_uses_gb_and_usd(self):
        parsed = parse_code("BRK-B", "")
        self.assertEqual(parsed["code"], "gb_brk-b")
        self.assertEqual(parsed["curr"], "USD")

    def test_infer_asset_type_numeric_5_is_hk(self):
        self.assertEqual(infer_asset_type("00700", "腾讯控股"), "hk")

    def test_get_sina_stock_price_numeric_5_uses_hk_route(self):
        def _fake_http_get(source, url, **kwargs):
            if source == "eastmoney_cn_hk_stock":
                self.assertIn("secid=116.00700", url)
                return _MockResp(json_data={"data": {"f43": 533.0, "f60": 532.0}})
            raise AssertionError(f"unexpected source={source}, url={url}")

        with patch("core.stock.monitored_http_get", side_effect=_fake_http_get):
            price, yclose, amt, chg, nav_date = get_sina_stock_price("00700")

        self.assertEqual(price, 533.0)
        self.assertEqual(yclose, 532.0)
        self.assertAlmostEqual(amt, 1.0)
        self.assertAlmostEqual(chg, (1.0 / 532.0) * 100)

    def test_get_sina_stock_price_hk_falls_back_to_sina_when_tencent_fails(self):
        def _fake_http_get(source, url, **kwargs):
            if source == "eastmoney_cn_hk_stock":
                raise RuntimeError("eastmoney timeout")
            if source == "tencent_stock":
                raise RuntimeError("tencent timeout")
            if source == "sina_stock":
                return _MockResp(
                    'var hq_str_hk00700="TENCENT,腾讯控股,530.000,532.000,535.000,527.500,533.000,1.000,0.188";'
                )
            raise AssertionError(f"unexpected source={source}, url={url}")

        with patch("core.stock.monitored_http_get", side_effect=_fake_http_get):
            price, yclose, amt, chg, nav_date = get_sina_stock_price("00700.HK")

        self.assertEqual(price, 533.0)
        self.assertEqual(yclose, 532.0)
        self.assertAlmostEqual(amt, 1.0)
        self.assertAlmostEqual(chg, (1.0 / 532.0) * 100)

    def test_get_sina_stock_price_hk_suffix_4_digit_uses_hk_5_digit_route(self):
        def _fake_http_get(source, url, **kwargs):
            if source == "eastmoney_cn_hk_stock":
                self.assertIn("secid=116.00700", url)
                return _MockResp(json_data={"data": {"f43": 533.0, "f60": 532.0}})
            raise AssertionError(f"unexpected source={source}, url={url}")

        with patch("core.stock.monitored_http_get", side_effect=_fake_http_get):
            price, yclose, amt, chg, nav_date = get_sina_stock_price("0700.HK")

        self.assertEqual(price, 533.0)
        self.assertEqual(yclose, 532.0)
        self.assertAlmostEqual(amt, 1.0)
        self.assertAlmostEqual(chg, (1.0 / 532.0) * 100)

    def test_hk_quote_stale_only_during_regular_session(self):
        self.assertTrue(
            _is_hk_quote_stale(
                "2026/07/09 09:52:05",
                now=datetime(2026, 7, 9, 10, 6, 25),
            )
        )
        self.assertFalse(
            _is_hk_quote_stale(
                "2026/07/09 10:04:30",
                now=datetime(2026, 7, 9, 10, 6, 25),
            )
        )
        self.assertFalse(
            _is_hk_quote_stale(
                "2026/07/09 09:52:05",
                now=datetime(2026, 7, 9, 12, 30, 0),
            )
        )

    def test_price_cache_unifies_hk_aliases(self):
        price_cache.clear()
        try:
            with patch("core.price.get_stock_price", return_value=(533.0, 532.0, 1.0, 0.188, None)) as first_fetch:
                first = get_price("hk00700")
            self.assertEqual(first[0], 533.0)
            first_fetch.assert_called_once()

            with patch("core.price.get_stock_price", return_value=(400.0, 399.0, 1.0, 0.25, None)) as second_fetch:
                second = get_price("0700.HK")
            self.assertEqual(second[0], 533.0)
            second_fetch.assert_not_called()
        finally:
            price_cache.clear()

    def test_infer_asset_type_us_etf_remains_us(self):
        self.assertEqual(infer_asset_type("gb_qqq", "Invesco QQQ ETF"), "us")

    def test_infer_asset_type_a_share_etf_remains_a(self):
        self.assertEqual(infer_asset_type("sh510300", "沪深300ETF"), "a")

    def test_infer_category_type_exchange_etf_counts_as_fund(self):
        self.assertEqual(infer_category_type("sz159201", "华夏国证自由现金流ETF", "a"), "fund")

    def test_infer_asset_type_otc_fund_prefix_remains_fund(self):
        self.assertEqual(infer_asset_type("f_161907", "万家中证红利ETF联接A"), "fund")

    def test_market_from_asset_exchange_etf_with_f_prefix_uses_a_market(self):
        self.assertEqual(
            market_from_asset({"code": "f_511360", "asset_type": "fund"}),
            "a",
        )

    def test_infer_asset_type_invalid_f_prefix_letters_treated_as_us(self):
        self.assertEqual(infer_asset_type("f_NUGT", "Direxion NUGT ETF"), "us")

    def test_infer_asset_type_us_symbol_with_dash_remains_us(self):
        self.assertEqual(infer_asset_type("BRK-B", "伯克希尔B"), "us")


if __name__ == "__main__":
    unittest.main()

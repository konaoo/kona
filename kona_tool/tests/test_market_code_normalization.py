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

from core.parser import parse_code
from core.asset_type import infer_asset_type
from core.stock import get_sina_stock_price


class _MockResp:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code


class TestMarketCodeNormalization(unittest.TestCase):
    def test_parse_code_numeric_5_defaults_to_hk(self):
        parsed = parse_code("00700", "")
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

    def test_infer_asset_type_numeric_5_is_hk(self):
        self.assertEqual(infer_asset_type("00700", "腾讯控股"), "hk")

    def test_get_sina_stock_price_numeric_5_uses_hk_route(self):
        def _fake_http_get(source, url, **kwargs):
            if source == "tencent_stock":
                self.assertIn("hk00700", url)
                return _MockResp('v_hk00700="x~x~x~533.000~532.000~";')
            raise AssertionError(f"unexpected source={source}, url={url}")

        with patch("core.stock.monitored_http_get", side_effect=_fake_http_get):
            price, yclose, amt, chg = get_sina_stock_price("00700")

        self.assertEqual(price, 533.0)
        self.assertEqual(yclose, 532.0)
        self.assertAlmostEqual(amt, 1.0)
        self.assertAlmostEqual(chg, (1.0 / 532.0) * 100)

    def test_get_sina_stock_price_hk_falls_back_to_sina_when_tencent_fails(self):
        def _fake_http_get(source, url, **kwargs):
            if source == "tencent_stock":
                raise RuntimeError("tencent timeout")
            if source == "sina_stock":
                return _MockResp(
                    'var hq_str_hk00700="TENCENT,腾讯控股,530.000,532.000,535.000,527.500,533.000,1.000,0.188";'
                )
            raise AssertionError(f"unexpected source={source}, url={url}")

        with patch("core.stock.monitored_http_get", side_effect=_fake_http_get):
            price, yclose, amt, chg = get_sina_stock_price("00700.HK")

        self.assertEqual(price, 533.0)
        self.assertEqual(yclose, 532.0)
        self.assertAlmostEqual(amt, 1.0)
        self.assertAlmostEqual(chg, (1.0 / 532.0) * 100)

    def test_infer_asset_type_us_etf_remains_us(self):
        self.assertEqual(infer_asset_type("gb_qqq", "Invesco QQQ ETF"), "us")

    def test_infer_asset_type_a_share_etf_remains_a(self):
        self.assertEqual(infer_asset_type("sh510300", "沪深300ETF"), "a")

    def test_infer_asset_type_otc_fund_prefix_remains_fund(self):
        self.assertEqual(infer_asset_type("f_161907", "万家中证红利ETF联接A"), "fund")

    def test_infer_asset_type_invalid_f_prefix_letters_treated_as_us(self):
        self.assertEqual(infer_asset_type("f_NUGT", "Direxion NUGT ETF"), "us")


if __name__ == "__main__":
    unittest.main()

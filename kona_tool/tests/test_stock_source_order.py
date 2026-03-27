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

from core.stock import get_boursorama_fund_price, get_sina_stock_price, get_stock_price, get_us_stock_price


class _Resp:
    def __init__(self, text: str = "", status_code: int = 200, json_data=None, url: str = ""):
        self.text = text
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.url = url

    def json(self):
        return self._json_data


class TestStockSourceOrder(unittest.TestCase):
    def test_a_share_prefers_tencent_before_sina(self):
        calls = []

        def fake_get(source, *args, **kwargs):
            calls.append(source)
            if source == "tencent_stock":
                return _Resp(text='v_sh600000="1~浦发银行~600000~9.66~9.60~0~0~0";', status_code=200)
            raise AssertionError("Sina should not be called when Tencent already returns valid quote")

        with patch("core.stock.monitored_http_get", side_effect=fake_get):
            curr, yclose, *_ = get_sina_stock_price("sh600000")

        self.assertAlmostEqual(curr, 9.66, places=2)
        self.assertAlmostEqual(yclose, 9.60, places=2)
        self.assertEqual(calls, ["tencent_stock"])

    def test_a_share_fallbacks_to_sina_when_tencent_invalid(self):
        calls = []

        def fake_get(source, *args, **kwargs):
            calls.append(source)
            if source == "tencent_stock":
                return _Resp(text='v_sh600000="";', status_code=200)
            if source == "sina_stock":
                return _Resp(text='var hq_str_sh600000="浦发银行,9.560,9.600,9.590";', status_code=200)
            return _Resp(status_code=500)

        with patch("core.stock.monitored_http_get", side_effect=fake_get):
            curr, yclose, *_ = get_sina_stock_price("sh600000")

        self.assertAlmostEqual(curr, 9.59, places=2)
        self.assertAlmostEqual(yclose, 9.60, places=2)
        self.assertEqual(calls, ["tencent_stock", "sina_stock"])

    def test_a_share_fallbacks_to_eastmoney_when_tencent_and_sina_invalid(self):
        calls = []

        def fake_get(source, *args, **kwargs):
            calls.append(source)
            if source == "tencent_stock":
                return _Resp(text='v_sh600000="";', status_code=200)
            if source == "sina_stock":
                return _Resp(text='var hq_str_sh600000="";', status_code=200)
            if source == "eastmoney_cn_hk_stock":
                return _Resp(status_code=200, json_data={"data": {"f43": 9.61, "f60": 9.60}})
            return _Resp(status_code=500)

        with patch("core.stock.monitored_http_get", side_effect=fake_get):
            curr, yclose, *_ = get_sina_stock_price("sh600000")

        self.assertAlmostEqual(curr, 9.61, places=2)
        self.assertAlmostEqual(yclose, 9.60, places=2)
        self.assertEqual(calls, ["tencent_stock", "sina_stock", "eastmoney_cn_hk_stock"])

    def test_hk_fallbacks_to_eastmoney_before_sina(self):
        calls = []

        def fake_get(source, *args, **kwargs):
            calls.append(source)
            if source == "tencent_stock":
                return _Resp(text='v_hk01810="";', status_code=200)
            if source == "eastmoney_cn_hk_stock":
                return _Resp(status_code=200, json_data={"data": {"f43": 32.74, "f60": 32.00}})
            raise AssertionError("Sina should not be called when Eastmoney already returns valid quote")

        with patch("core.stock.monitored_http_get", side_effect=fake_get):
            curr, yclose, *_ = get_sina_stock_price("HK1810")

        self.assertAlmostEqual(curr, 32.74, places=2)
        self.assertAlmostEqual(yclose, 32.00, places=2)
        self.assertEqual(calls, ["tencent_stock", "eastmoney_cn_hk_stock"])

    def test_us_stock_fallbacks_to_eastmoney_when_sina_fails(self):
        calls = []

        def fake_get(source, *args, **kwargs):
            calls.append(source)
            if source == "sina_us_stock":
                return _Resp(text="Forbidden", status_code=403)
            if source == "eastmoney_us_stock":
                return _Resp(status_code=200, json_data={"data": {"f43": 262.52, "f60": 263.75}})
            raise AssertionError("Nasdaq should not be reached when Eastmoney already returns valid quote")

        with patch("core.stock.monitored_http_get", side_effect=fake_get):
            curr, yclose, *_ = get_us_stock_price("gb_aapl")

        self.assertAlmostEqual(curr, 262.52, places=2)
        self.assertAlmostEqual(yclose, 263.75, places=2)
        self.assertEqual(calls, ["sina_us_stock", "eastmoney_us_stock"])

    def test_us_stock_fallbacks_to_nasdaq_when_sina_and_eastmoney_fail(self):
        calls = []

        def fake_get(source, *args, **kwargs):
            calls.append(source)
            if source == "sina_us_stock":
                return _Resp(text="Forbidden", status_code=403)
            if source == "eastmoney_us_stock":
                return _Resp(status_code=200, json_data={"data": None})
            return _Resp(status_code=500)

        with patch("core.stock.monitored_http_get", side_effect=fake_get), patch(
            "core.stock._get_nasdaq_quote",
            side_effect=lambda symbol, assetclass: (262.0, 263.0, -1.0, -0.38, None) if assetclass == "stocks" else None,
        ) as nasdaq_mock:
            curr, yclose, *_ = get_us_stock_price("gb_aapl")

        self.assertAlmostEqual(curr, 262.0, places=2)
        self.assertAlmostEqual(yclose, 263.0, places=2)
        self.assertIn("sina_us_stock", calls)
        # eastmoney 会按 105/106 两个 secid 依次尝试
        self.assertGreaterEqual(calls.count("eastmoney_us_stock"), 1)
        self.assertGreaterEqual(nasdaq_mock.call_count, 1)

    def test_us_stock_special_symbol_fallbacks_to_relaxed_nasdaq(self):
        calls = []

        def fake_get(source, *args, **kwargs):
            calls.append(source)
            if source == "sina_us_stock":
                return _Resp(text='var hq_str_gb_brk.b="";', status_code=200)
            if source == "eastmoney_us_stock":
                return _Resp(status_code=200, json_data={"data": None})
            raise AssertionError(f"unexpected source={source}")

        with patch("core.stock.monitored_http_get", side_effect=fake_get), patch(
            "core.stock._get_nasdaq_quote",
            return_value=None,
        ) as nasdaq_mock, patch(
            "core.stock._get_nasdaq_quote_relaxed",
            side_effect=lambda symbol, assetclass: (493.57, 494.14, -0.57, -0.12, None)
            if symbol == "BRK.B" and assetclass == "stocks"
            else None,
        ) as relaxed_mock:
            curr, yclose, *_ = get_us_stock_price("gb_brk.b")

        self.assertAlmostEqual(curr, 493.57, places=2)
        self.assertAlmostEqual(yclose, 494.14, places=2)
        self.assertEqual(calls, [])
        self.assertEqual(nasdaq_mock.call_count, 0)
        self.assertGreaterEqual(relaxed_mock.call_count, 1)

    def test_boursorama_fund_parser_reads_price_and_variation(self):
        html = """
        <html><body>
          <span class="c-instrument c-instrument--last" data-ist-last>9,38</span>
          <span class="c-instrument c-instrument--variation" data-ist-variation>+0,29%</span>
        </body></html>
        """
        with patch(
            "core.stock.monitored_http_get",
            return_value=_Resp(
                text=html,
                status_code=200,
                url="https://www.boursorama.com/bourse/opcvm/cours/0P00014FO3/",
            ),
        ):
            curr, yclose, amt, chg, nav_date = get_boursorama_fund_price("LU1116320737")

        self.assertAlmostEqual(curr, 9.38, places=2)
        self.assertAlmostEqual(chg, 0.29, places=2)
        self.assertAlmostEqual(yclose, curr / 1.0029, places=4)
        self.assertAlmostEqual(amt, curr - yclose, places=4)

    def test_ft_fund_prefers_blackrock_before_boursorama_and_ft(self):
        with patch(
            "core.stock.get_blackrock_fund_price",
            return_value=(9.41, 9.38, 0.03, 0.32, None),
        ) as blackrock_mock, patch(
            "core.stock.get_marketscreener_fund_price",
            return_value=(0.0, 0.0, 0.0, 0.0),
        ) as marketscreener_mock, patch(
            "core.stock.get_boursorama_fund_price",
            return_value=(9.38, 9.3529, 0.0271, 0.29, None),
        ) as boursorama_mock, patch(
            "core.stock.get_ft_fund_price",
            return_value=(0.0, 0.0, 0.0, 0.0, None),
        ) as ft_mock:
            curr, yclose, *_ = get_stock_price("ft_LU1116320737")

        self.assertAlmostEqual(curr, 9.41, places=2)
        self.assertAlmostEqual(yclose, 9.38, places=2)
        blackrock_mock.assert_called_once_with("LU1116320737")
        marketscreener_mock.assert_not_called()
        boursorama_mock.assert_not_called()
        ft_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()

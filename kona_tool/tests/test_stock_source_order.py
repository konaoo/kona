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

from core.stock import get_sina_stock_price, get_us_stock_price


class _Resp:
    def __init__(self, text: str = "", status_code: int = 200, json_data=None):
        self.text = text
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}

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
            side_effect=lambda symbol, assetclass: (262.0, 263.0, -1.0, -0.38) if assetclass == "stocks" else None,
        ) as nasdaq_mock:
            curr, yclose, *_ = get_us_stock_price("gb_aapl")

        self.assertAlmostEqual(curr, 262.0, places=2)
        self.assertAlmostEqual(yclose, 263.0, places=2)
        self.assertIn("sina_us_stock", calls)
        # eastmoney 会按 105/106 两个 secid 依次尝试
        self.assertGreaterEqual(calls.count("eastmoney_us_stock"), 1)
        self.assertGreaterEqual(nasdaq_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()

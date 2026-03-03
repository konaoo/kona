import os
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import config  # noqa: E402
from core import price as price_module  # noqa: E402


class SearchTimeoutTests(unittest.TestCase):
    def test_search_returns_partial_results_within_deadline(self):
        original_aggregate = getattr(config, "SEARCH_AGGREGATE_TIMEOUT_SECONDS", 1.8)
        original_source = getattr(config, "SEARCH_SOURCE_TIMEOUT_SECONDS", 1.2)
        config.SEARCH_AGGREGATE_TIMEOUT_SECONDS = 0.5
        config.SEARCH_SOURCE_TIMEOUT_SECONDS = 0.5
        try:
            def fake_search_sina(query, type_code):
                if type_code == "11":
                    return [
                        {
                            "code": "sh600000",
                            "name": "浦发银行",
                            "type_name": "A股",
                            "currency": "CNY",
                        }
                    ]
                time.sleep(1.0)
                return [
                    {
                        "code": "gb_tsla",
                        "name": "Tesla",
                        "type_name": "美股",
                        "currency": "USD",
                    }
                ]

            def fake_search_fund(query):
                time.sleep(1.0)
                return [
                    {
                        "code": "f_000001",
                        "name": "测试基金",
                        "type_name": "基金",
                        "currency": "CNY",
                    }
                ]

            with mock.patch.object(price_module, "_search_sina", side_effect=fake_search_sina), mock.patch.object(
                price_module, "_search_fund", side_effect=fake_search_fund
            ):
                started = time.monotonic()
                results = price_module.search_stocks("test")
                elapsed = time.monotonic() - started

            self.assertLess(elapsed, 0.9)
            self.assertTrue(any(item.get("code") == "sh600000" for item in results))
            self.assertFalse(any(item.get("code") == "gb_tsla" for item in results))
            target = next((item for item in results if item.get("code") == "sh600000"), None)
            self.assertIsNotNone(target)
            self.assertEqual(target.get("asset_type"), "a")
        finally:
            config.SEARCH_AGGREGATE_TIMEOUT_SECONDS = original_aggregate
            config.SEARCH_SOURCE_TIMEOUT_SECONDS = original_source

    def test_search_source_timeout_uses_search_specific_config(self):
        original_source = getattr(config, "SEARCH_SOURCE_TIMEOUT_SECONDS", 1.2)
        config.SEARCH_SOURCE_TIMEOUT_SECONDS = 0.73
        try:
            captured = []

            class _Resp:
                status_code = 200
                text = 'var suggestdata="";'

                def json(self):
                    return {"Datas": []}

            def fake_get(source, url, params=None, headers=None, timeout=3):
                captured.append(timeout)
                return _Resp()

            with mock.patch.object(price_module, "monitored_http_get", side_effect=fake_get):
                price_module._search_sina("tsla", "41")
                price_module._search_fund("tsla")

            self.assertEqual(captured, [0.73, 0.73])
        finally:
            config.SEARCH_SOURCE_TIMEOUT_SECONDS = original_source

    def test_search_filters_letter_prefixed_fund_codes(self):
        def fake_search_sina(query, type_code):
            if type_code == "41":
                return [
                    {
                        "code": "gb_nugt",
                        "name": "3X多金矿",
                        "type_name": "美股",
                        "currency": "USD",
                    }
                ]
            return []

        def fake_search_fund(query):
            return [
                {
                    "code": "f_NUGT",
                    "name": "二倍做多金矿指数ETF-Direxion",
                    "type_name": "基金",
                    "currency": "CNY",
                },
                {
                    "code": "f_110017",
                    "name": "易方达增强回报债券A",
                    "type_name": "基金",
                    "currency": "CNY",
                },
            ]

        with mock.patch.object(price_module, "_search_sina", side_effect=fake_search_sina), mock.patch.object(
            price_module, "_search_fund", side_effect=fake_search_fund
        ):
            results = price_module.search_stocks("nugt")

        codes = [item.get("code") for item in results]
        self.assertIn("gb_nugt", codes)
        self.assertIn("f_110017", codes)
        self.assertNotIn("f_NUGT", codes)

    def test_search_uses_longer_alias_name_for_us_symbol(self):
        def fake_search_sina(query, type_code):
            if type_code == "41":
                return [
                    {
                        "code": "gb_nugt",
                        "name": "3X多金矿",
                        "type_name": "美股",
                        "currency": "USD",
                    }
                ]
            return []

        def fake_search_fund(query):
            return [
                {
                    "code": "f_NUGT",
                    "name": "二倍做多金矿指数ETF-Direxion",
                    "type_name": "基金",
                    "currency": "CNY",
                }
            ]

        with mock.patch.object(price_module, "_search_sina", side_effect=fake_search_sina), mock.patch.object(
            price_module, "_search_fund", side_effect=fake_search_fund
        ):
            results = price_module.search_stocks("nugt")

        target = next((item for item in results if item.get("code") == "gb_nugt"), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get("name"), "二倍做多金矿指数ETF-Direxion")

    def test_search_fund_maps_exchange_qdii_to_sz_or_sh_code(self):
        class _Resp:
            status_code = 200

            @staticmethod
            def json():
                return {
                    "Datas": [
                        {
                            "CODE": "159687",
                            "NAME": "南方东英富时亚太低碳精选ETF(QDII)",
                        }
                    ]
                }

        with mock.patch.object(price_module, "monitored_http_get", return_value=_Resp()), mock.patch.object(
            price_module,
            "get_stock_price",
            side_effect=lambda code: (1.7, 1.6, 0.1, 6.2) if code == "sz159687" else (0.0, 0.0, 0.0, 0.0),
        ):
            results = price_module._search_fund("159687")

        self.assertTrue(results)
        self.assertEqual(results[0].get("code"), "sz159687")


if __name__ == "__main__":
    unittest.main()

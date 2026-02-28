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


if __name__ == "__main__":
    unittest.main()

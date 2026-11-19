"""价格巡检发现的历史误标：兼容取价并封住新增入口。"""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import fund, price
from core.asset_type import infer_asset_type, infer_category_type
from core.parser import parse_code
from core.market_calendar import market_from_asset
from core.trend import get_asset_trend
from portfolio_runtime import create_portfolio_runtime


# 2026-11-19 线上只读巡检的 23 种代码，不保存用户信息。
EXCHANGE_FUNDS = (
    "159201", "159687", "159892", "159928", "159980", "501018",
    "510300", "510900", "513050", "513060", "513120", "513130",
    "513300", "513310", "513400", "513750", "513880", "515180",
    "515450", "516020", "518680", "520870", "563020",
)
STOCKS = ("600329", "601818")
EMPTY = (0.0, 0.0, 0.0, 0.0, None)
QUOTE = (2.0, 1.9, 0.1, 5.26, None)


class PriceIdentityRegressionTests(unittest.TestCase):
    def setUp(self):
        price.price_cache.clear()
        self.addCleanup(price.price_cache.clear)

    def test_legacy_alias_quote_and_new_identity_use_exchange_without_probe(self):
        for suffix in (*EXCHANGE_FUNDS, *STOCKS):
            with self.subTest(suffix=suffix):
                legacy = f"f_{suffix}"
                expected = f"{'sz' if suffix.startswith('15') else 'sh'}{suffix}"
                self.assertEqual(parse_code(legacy, "USD"), {"code": expected, "curr": "CNY"})
                self.assertEqual(infer_asset_type(legacy), "a")
                self.assertEqual(
                    infer_category_type(legacy, "测试ETF" if suffix in EXCHANGE_FUNDS else "测试股票"),
                    "fund" if suffix in EXCHANGE_FUNDS else "a",
                )

                runtime = create_portfolio_runtime(
                    parse_code=parse_code, infer_asset_type=infer_asset_type,
                    batch_get_prices_getter=Mock(side_effect=AssertionError("明确号段不依赖行情探测")),
                )
                identity = runtime.normalize_portfolio_identity(legacy, "USD", "测试资产")
                self.assertEqual(identity["code"], expected)
                self.assertEqual(identity["asset_type"], "a")
                self.assertEqual(identity["curr"], "CNY")

                price.price_cache.clear()
                try:
                    with patch("core.price.get_stock_price", return_value=QUOTE) as stock, patch(
                        "core.price.get_fund_price", side_effect=AssertionError("不应走场外净值")
                    ):
                        result = price.batch_get_prices([legacy], use_cache=False)
                    self.assertEqual(result[legacy], QUOTE)  # 返回键保留历史身份，交易记录不改名。
                    stock.assert_called_once_with(expected)
                finally:
                    price.price_cache.clear()

    def test_otc_and_feeder_funds_are_not_changed(self):
        for suffix in ("000001", "000216", "110017", "968163"):
            with self.subTest(suffix=suffix):
                legacy = f"f_{suffix}"
                self.assertEqual(parse_code(legacy)["code"], legacy)
                self.assertEqual(infer_asset_type(legacy, "黄金ETF联接A"), "fund")
                with patch("core.price.get_stock_price") as stock, patch(
                    "core.price.get_fund_price", return_value=QUOTE
                ):
                    self.assertEqual(price.get_price(legacy, use_cache=False), QUOTE)
                stock.assert_not_called()
                price.price_cache.clear()

    def test_sz16_ambiguous_fund_keeps_probe_and_missing_quote_keeps_identity(self):
        runtime = create_portfolio_runtime(
            parse_code=parse_code, infer_asset_type=infer_asset_type,
            batch_get_prices_getter=Mock(return_value={"sz161907": EMPTY}),
        )
        self.assertEqual(runtime.normalize_portfolio_identity("f_161907", "CNY", "基金")["code"], "f_161907")
        runtime.batch_get_prices_getter.assert_called_once_with(["sz161907"])

    def test_exchange_quote_failure_does_not_fall_back_to_otc_nav(self):
        with patch("core.price.get_stock_price", return_value=EMPTY), patch(
            "core.price.get_fund_price"
        ) as otc:
            self.assertEqual(price.get_price("f_510300", use_cache=False), EMPTY)
        otc.assert_not_called()

    def test_fund_search_normalizes_even_when_quote_source_is_down(self):
        response = Mock(status_code=200)
        response.json.return_value = {"Datas": [{"CODE": "510300", "NAME": "沪深300ETF"}]}
        with patch("core.price.monitored_http_get", return_value=response), patch(
            "core.price.get_stock_price", side_effect=AssertionError("搜索不应依赖取价成功")
        ):
            self.assertEqual(price._search_fund("510300")[0]["code"], "sh510300")

    def test_tencent_failure_contract_always_has_five_values(self):
        for response in (
            Mock(status_code=503, text=""),
            Mock(status_code=200, text=""),
            Mock(status_code=200, text='v_jj000001="short~payload";'),
            Mock(status_code=200, text='v_jj000001="0~基金~0~0~~0~0~0~2026-11-19~";'),
        ):
            with self.subTest(status_code=response.status_code, text=response.text):
                with patch("core.fund.monitored_http_get", return_value=response):
                    self.assertEqual(fund.get_fund_tencent_jj("000001"), EMPTY)

    def test_actual_fund_source_failure_chain_returns_five_values(self):
        # 不替换子源返回值，真实走过天天失败、腾讯失败和全部失败分支。
        for suffix in (*STOCKS, "110017", "968163"):
            with self.subTest(suffix=suffix):
                response = Mock(status_code=503, text="")
                with patch("core.fund.monitored_http_get", return_value=response):
                    self.assertEqual(fund.get_fund_price(f"f_{suffix}"), EMPTY)

    def test_empty_fund_code_and_http_exception_return_five_values(self):
        self.assertEqual(fund.get_fund_price(""), EMPTY)
        with patch("core.fund.monitored_http_get", side_effect=RuntimeError("行情超时")):
            self.assertEqual(fund.get_fund_tiantian_price("f_110017"), EMPTY)
            self.assertEqual(fund.get_fund_tencent_jj("110017"), EMPTY)

    def test_legacy_stock_market_and_history_ignore_stale_fund_type(self):
        for suffix in STOCKS:
            with self.subTest(suffix=suffix):
                code = f"f_{suffix}"
                self.assertEqual(market_from_asset({"code": code, "asset_type": "fund"}), "a")
                self.assertEqual(infer_category_type(code, "测试股票", "fund"), "a")
                self.assertFalse(price.is_nav_fund_code(code))
                history = [{"date": "2026-11-18", "value": 2.0}]
                with patch("core.trend._fetch_stock_history_points", return_value=history) as stock, patch(
                    "core.trend._fetch_fund_history_points"
                ) as otc:
                    result = get_asset_trend(code, market_hint="fund")
                self.assertEqual(result["code"], code)
                self.assertEqual(result["resolved_code"], f"sh{suffix}")
                self.assertEqual(result["kind"], "stock")
                self.assertEqual(result["points"], history)
                stock.assert_called_once_with(f"sh{suffix}", 20, "fund")
                otc.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""价格巡检发现的历史误标：兼容取价并封住新增入口。"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

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


@pytest.mark.parametrize("suffix", (*EXCHANGE_FUNDS, *STOCKS))
def test_legacy_alias_quote_and_new_identity_use_exchange_without_probe(suffix):
    legacy = f"f_{suffix}"
    expected = f"{'sz' if suffix.startswith('15') else 'sh'}{suffix}"
    assert parse_code(legacy, "USD") == {"code": expected, "curr": "CNY"}
    assert infer_asset_type(legacy) == "a"
    assert infer_category_type(legacy, "测试ETF" if suffix in EXCHANGE_FUNDS else "测试股票") == (
        "fund" if suffix in EXCHANGE_FUNDS else "a"
    )

    runtime = create_portfolio_runtime(
        parse_code=parse_code, infer_asset_type=infer_asset_type,
        batch_get_prices_getter=Mock(side_effect=AssertionError("明确号段不依赖行情探测")),
    )
    identity = runtime.normalize_portfolio_identity(legacy, "USD", "测试资产")
    assert identity["code"] == expected
    assert identity["asset_type"] == "a"
    assert identity["curr"] == "CNY"

    price.price_cache.clear()
    try:
        with patch("core.price.get_stock_price", return_value=QUOTE) as stock, patch(
            "core.price.get_fund_price", side_effect=AssertionError("不应走场外净值")
        ):
            result = price.batch_get_prices([legacy], use_cache=False)
        assert result[legacy] == QUOTE  # 返回键保留历史身份，交易记录不改名。
        stock.assert_called_once_with(expected)
    finally:
        price.price_cache.clear()


@pytest.mark.parametrize("suffix", ("000001", "000216", "110017", "968163"))
def test_otc_and_feeder_funds_are_not_changed(suffix):
    legacy = f"f_{suffix}"
    assert parse_code(legacy)["code"] == legacy
    assert infer_asset_type(legacy, "黄金ETF联接A") == "fund"
    with patch("core.price.get_stock_price") as stock, patch(
        "core.price.get_fund_price", return_value=QUOTE
    ):
        assert price.get_price(legacy, use_cache=False) == QUOTE
    stock.assert_not_called()
    price.price_cache.clear()


def test_sz16_ambiguous_fund_keeps_probe_and_missing_quote_keeps_identity():
    runtime = create_portfolio_runtime(
        parse_code=parse_code, infer_asset_type=infer_asset_type,
        batch_get_prices_getter=Mock(return_value={"sz161907": EMPTY}),
    )
    assert runtime.normalize_portfolio_identity("f_161907", "CNY", "基金")["code"] == "f_161907"
    runtime.batch_get_prices_getter.assert_called_once_with(["sz161907"])


def test_exchange_quote_failure_does_not_fall_back_to_otc_nav():
    price.price_cache.clear()
    with patch("core.price.get_stock_price", return_value=EMPTY), patch(
        "core.price.get_fund_price"
    ) as otc:
        assert price.get_price("f_510300", use_cache=False) == EMPTY
    otc.assert_not_called()


def test_fund_search_normalizes_even_when_quote_source_is_down():
    response = Mock(status_code=200)
    response.json.return_value = {"Datas": [{"CODE": "510300", "NAME": "沪深300ETF"}]}
    with patch("core.price.monitored_http_get", return_value=response), patch(
        "core.price.get_stock_price", side_effect=AssertionError("搜索不应依赖取价成功")
    ):
        assert price._search_fund("510300")[0]["code"] == "sh510300"


@pytest.mark.parametrize("response", (
    Mock(status_code=503, text=""),
    Mock(status_code=200, text=""),
    Mock(status_code=200, text='v_jj000001="short~payload";'),
    Mock(status_code=200, text='v_jj000001="0~基金~0~0~~0~0~0~2026-11-19~";'),
))
def test_tencent_failure_contract_always_has_five_values(response):
    with patch("core.fund.monitored_http_get", return_value=response):
        assert fund.get_fund_tencent_jj("000001") == EMPTY


@pytest.mark.parametrize("suffix", (*STOCKS, "110017", "968163"))
def test_actual_fund_source_failure_chain_returns_five_values(suffix):
    # 不替换子源返回值，真实走过天天失败、腾讯失败和全部失败分支。
    response = Mock(status_code=503, text="")
    with patch("core.fund.monitored_http_get", return_value=response):
        assert fund.get_fund_price(f"f_{suffix}") == EMPTY


def test_empty_fund_code_and_http_exception_return_five_values():
    assert fund.get_fund_price("") == EMPTY
    with patch("core.fund.monitored_http_get", side_effect=RuntimeError("行情超时")):
        assert fund.get_fund_tiantian_price("f_110017") == EMPTY
        assert fund.get_fund_tencent_jj("110017") == EMPTY


@pytest.mark.parametrize("suffix", STOCKS)
def test_legacy_stock_market_and_history_ignore_stale_fund_type(suffix):
    code = f"f_{suffix}"
    assert market_from_asset({"code": code, "asset_type": "fund"}) == "a"
    assert infer_category_type(code, "测试股票", "fund") == "a"
    assert not price.is_nav_fund_code(code)
    history = [{"date": "2026-11-18", "value": 2.0}]
    with patch("core.trend._fetch_stock_history_points", return_value=history) as stock, patch(
        "core.trend._fetch_fund_history_points"
    ) as otc:
        result = get_asset_trend(code, market_hint="fund")
    assert result["code"] == code
    assert result["resolved_code"] == f"sh{suffix}"
    assert result["kind"] == "stock"
    assert result["points"] == history
    stock.assert_called_once_with(f"sh{suffix}", 20, "fund")
    otc.assert_not_called()

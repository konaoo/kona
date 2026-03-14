"""
市场状态 / 首页指数处理函数
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict


def create_market_payload_handlers(
    *,
    market_status_getter: Callable[..., Dict[str, Any]],
    prices_batch_getter: Callable[[list[str]], Dict[str, tuple[Any, Any, Any, Any]]],
    rates_getter: Callable[[], Dict[str, Any]],
    hstech_price_getter: Callable[[], tuple[Any, Any, Any, Any]],
):
    def build_market_status_payload() -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc)
        return market_status_getter(now_utc=now_utc)

    def build_market_indices_payload() -> list[Dict[str, Any]]:
        index_codes = [
            's_sh000001',
            's_sz399001',
            's_sz399006',
            'gb_ixic',
        ]

        prices = prices_batch_getter(index_codes)
        hstech = hstech_price_getter()
        rates = rates_getter()
        usd_cny = rates.get('USD', 0.0)

        def format_item(name, data):
            curr, _yclose, amt, pct = data
            return {
                "name": name,
                "value": curr,
                "change": amt,
                "change_pct": pct,
            }

        return [
            format_item("上证指数", prices.get('s_sh000001', (0, 0, 0, 0))),
            format_item("深成指数", prices.get('s_sz399001', (0, 0, 0, 0))),
            format_item("创业板指", prices.get('s_sz399006', (0, 0, 0, 0))),
            format_item("恒生科技", hstech),
            format_item("纳斯达克", prices.get('gb_ixic', (0, 0, 0, 0))),
            {
                "name": "USD/CNY",
                "value": usd_cny,
                "change": 0.0,
                "change_pct": 0.0,
            },
        ]

    return {
        "status": build_market_status_payload,
        "indices": build_market_indices_payload,
    }

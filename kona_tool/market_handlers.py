"""
市场状态 / 首页指数处理函数
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict

from core.request_trace import trace_request_stage

def create_market_payload_handlers(
    *,
    market_status_getter: Callable[..., Dict[str, Any]],
    # 价格抓取链路已标准化为 5 元组：(price, yclose, amt, pct, nav_date)
    # 但这里允许兼容旧的 4 元组返回，避免历史代码/测试 mock 断裂。
    prices_batch_getter: Callable[[list[str]], Dict[str, tuple[Any, ...]]],
    rates_getter: Callable[[], Dict[str, Any]],
    hstech_price_getter: Callable[[], tuple[Any, ...]],
):
    def build_market_status_payload() -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc)
        with trace_request_stage("market.status"):
            return market_status_getter(now_utc=now_utc)

    def build_market_indices_payload() -> list[Dict[str, Any]]:
        index_codes = [
            's_sh000001',
            's_sz399001',
            's_sz399006',
            'gb_ixic',
        ]

        with trace_request_stage("market.indices.prices", code_count=len(index_codes)):
            prices = prices_batch_getter(index_codes)
        with trace_request_stage("market.indices.hstech"):
            hstech = hstech_price_getter()
        with trace_request_stage("market.indices.rates"):
            rates = rates_getter()
        usd_cny = rates.get('USD', 0.0)

        def _unpack_price_tuple(data: Any) -> tuple[float, float, float, float]:
            """
            兼容 (price, yclose, amt, pct) 和 (price, yclose, amt, pct, nav_date) 两种格式。
            """
            if not isinstance(data, tuple) or len(data) < 4:
                return (0.0, 0.0, 0.0, 0.0)
            # 只取前 4 个，忽略 nav_date 等尾部字段
            price, yclose, amt, pct = data[0], data[1], data[2], data[3]
            try:
                return (float(price or 0.0), float(yclose or 0.0), float(amt or 0.0), float(pct or 0.0))
            except Exception:
                return (0.0, 0.0, 0.0, 0.0)

        def format_item(name, data):
            curr, _yclose, amt, pct = _unpack_price_tuple(data)
            return {
                "name": name,
                "value": curr,
                "change": amt,
                "change_pct": pct,
            }

        with trace_request_stage("market.indices.assemble"):
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

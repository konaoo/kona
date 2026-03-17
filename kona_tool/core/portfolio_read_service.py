"""投资读侧服务。

把实时持仓读模型从 app_factory / handler 里抽出来。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Tuple

from .portfolio_metrics import build_portfolio_items_with_metrics
from .request_trace import trace_request_stage


class PortfolioReadService:
    def __init__(
        self,
        *,
        db: Any,
        batch_get_prices_getter: Callable[[List[str]], Dict[str, Tuple[float, float, float, float]]],
        rates_getter: Callable[[], Dict[str, float]],
        convert_amount: Callable[[float, str, str, Dict[str, float]], float],
        market_status_getter: Callable[..., Dict[str, Any]],
    ) -> None:
        self.db = db
        self.batch_get_prices_getter = batch_get_prices_getter
        self.rates_getter = rates_getter
        self.convert_amount = convert_amount
        self.market_status_getter = market_status_getter

    def _enrich_items_with_metrics(
        self,
        items: List[Dict[str, Any]],
        *,
        now_utc: datetime | None = None,
    ) -> List[Dict[str, Any]]:
        if not items:
            return []

        codes = [item.get("code") for item in items if item.get("code")]
        with trace_request_stage("portfolio.quotes", code_count=len(codes)):
            quotes = self.batch_get_prices_getter(codes) if codes else {}
        with trace_request_stage("portfolio.rates"):
            rates = self.rates_getter() or {}
        resolved_now = now_utc or datetime.now(timezone.utc)
        with trace_request_stage("portfolio.market"):
            market_payload = self.market_status_getter(
                now_utc=resolved_now,
                force_refresh=False,
            )
        market_statuses = market_payload.get("markets", {}) if isinstance(market_payload, dict) else {}
        with trace_request_stage("portfolio.assemble", item_count=len(items)):
            return build_portfolio_items_with_metrics(
                items,
                quotes,
                rates,
                market_statuses,
                self.convert_amount,
            )

    def build_metrics_payload(
        self,
        *,
        user_id: str | None,
        now_utc: datetime | None = None,
    ) -> List[Dict[str, Any]]:
        with trace_request_stage("portfolio.db", query="get_portfolio", item_scope="all"):
            items = self.db.get_portfolio(user_id=user_id)
        return self._enrich_items_with_metrics(items, now_utc=now_utc)

    def build_portfolio_payload(
        self,
        *,
        asset_type: str,
        user_id: str | None,
        with_metrics: bool,
    ) -> List[Dict[str, Any]]:
        with trace_request_stage("portfolio.db", query="get_portfolio", item_scope=asset_type):
            items = self.db.get_portfolio(asset_type, user_id)
        if not with_metrics:
            return items
        return self._enrich_items_with_metrics(items)

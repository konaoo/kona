"""投资读侧服务。

把实时持仓读模型从 app_factory / handler 里抽出来。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Tuple

from .portfolio_metrics import build_portfolio_items_with_metrics
from .price import is_exchange_fund_code
from .request_trace import trace_request_stage


class PortfolioReadService:
    def __init__(
        self,
        *,
        db: Any,
        batch_get_prices_getter: Callable[[List[str]], Dict[str, Tuple[float, float, float, float, Optional[str]]]],
        rates_getter: Callable[[], Dict[str, float]],
        convert_amount: Callable[[float, str, str, Dict[str, float]], float],
        fund_latest_nav_date_getter: Callable[[str], str | None],
        market_status_getter: Callable[..., Dict[str, Any]],
    ) -> None:
        self.db = db
        self.batch_get_prices_getter = batch_get_prices_getter
        self.rates_getter = rates_getter
        self.convert_amount = convert_amount
        self.fund_latest_nav_date_getter = fund_latest_nav_date_getter
        self.market_status_getter = market_status_getter

    def _enrich_items_with_metrics(
        self,
        items: List[Dict[str, Any]],
        *,
        user_id: str | None = None,
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
        from zoneinfo import ZoneInfo as _ZoneInfo
        date_str = resolved_now.astimezone(_ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
        with trace_request_stage("portfolio.today_buys"):
            today_buys = self.db.get_today_buy_transactions(date_str, user_id)
        nav_date_codes = [
            code
            for code in dict.fromkeys(codes)
            if code.lower().startswith(("f_", "ft_")) and not is_exchange_fund_code(code)
        ]
        if nav_date_codes:
            with trace_request_stage("portfolio.nav_dates", code_count=len(nav_date_codes)):
                latest_nav_dates = {
                    code: self.fund_latest_nav_date_getter(code)
                    for code in nav_date_codes
                }
        else:
            latest_nav_dates = {}
        with trace_request_stage("portfolio.assemble", item_count=len(items)):
            return build_portfolio_items_with_metrics(
                items,
                quotes,
                rates,
                market_statuses,
                self.convert_amount,
                today_buys,
                latest_nav_dates,
            )

    def build_metrics_payload(
        self,
        *,
        user_id: str | None,
        now_utc: datetime | None = None,
        ledger_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        with trace_request_stage("portfolio.db", query="get_portfolio", item_scope="all"):
            items = self.db.get_portfolio(user_id=user_id, ledger_id=ledger_id)
        return self._enrich_items_with_metrics(items, user_id=user_id, now_utc=now_utc)

    def build_portfolio_payload(
        self,
        *,
        asset_type: str,
        user_id: str | None,
        with_metrics: bool,
        ledger_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        with trace_request_stage("portfolio.db", query="get_portfolio", item_scope=asset_type):
            items = self.db.get_portfolio(asset_type, user_id, ledger_id=ledger_id)
        if not with_metrics:
            return items
        return self._enrich_items_with_metrics(items, user_id=user_id)

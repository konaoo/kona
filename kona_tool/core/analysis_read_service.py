"""分析页读侧服务。"""

import logging
from typing import Any, Callable, Dict

from .request_trace import trace_request_stage

logger = logging.getLogger(__name__)


class _StatsGetterRealtimeTodayAdapter:
    def __init__(self, stats_getter: Callable[..., Dict[str, Any]]) -> None:
        self.stats_getter = stats_getter

    def build_payload(self, *, user_id: str | None, ledger_id: int | None = None) -> Dict[str, Any]:
        stats = self.stats_getter(user_id)
        day_pnl = float(stats.get("day_pnl") or 0.0)
        day_pnl_base = float(stats.get("day_pnl_base") or stats.get("total_invest") or 0.0)
        return {
            "effective_date": stats.get("day_pnl_effective_date"),
            "source": "realtime",
            "scope": {
                "ledger_id": ledger_id,
                "mode": "ledger" if ledger_id is not None else "global",
            },
            "totals": {
                "day_pnl": round(day_pnl, 2),
                "day_pnl_base": round(day_pnl_base, 2),
                "day_pnl_rate": round(day_pnl / day_pnl_base * 100, 2) if day_pnl_base > 0 else 0.0,
            },
        }


class AnalysisReadService:
    def __init__(
        self,
        *,
        db: Any,
        price_batch_getter: Callable[[list[str]], Dict[str, Any]],
        realtime_today_service: Any | None = None,
        stats_getter: Callable[[str | None], Dict[str, Any]] | None = None,
        rates_getter: Callable[[], Dict[str, float]] | None = None,
        convert_amount: Callable[[float, str, str, Dict[str, float]], float] | None = None,
        all_markets_closed_getter: Callable[[], bool] | None = None,
    ) -> None:
        self.db = db
        self.price_batch_getter = price_batch_getter
        self.realtime_today_service = realtime_today_service or (
            _StatsGetterRealtimeTodayAdapter(stats_getter) if stats_getter is not None else None
        )
        self.rates_getter = rates_getter
        self.convert_amount = convert_amount
        self.all_markets_closed_getter = all_markets_closed_getter

    def _get_day_overview(self, user_id: str | None, ledger_id: int | None = None) -> Dict[str, Any]:
        if self.realtime_today_service is None:
            return self.db.get_pnl_overview("day", user_id, ledger_id=ledger_id)
        realtime_today = self.realtime_today_service.build_payload(
            user_id=user_id,
            ledger_id=ledger_id,
        )
        totals = realtime_today.get("totals") or {}
        return {
            "pnl": round(float(totals.get("day_pnl") or 0.0), 2),
            "pnl_rate": round(float(totals.get("day_pnl_rate") or 0.0), 2),
            "base_value": round(float(totals.get("day_pnl_base") or 0.0), 2),
            "effective_date": realtime_today.get("effective_date"),
            "source": "realtime",
        }

    def build_overview_payload(self, *, period: str, user_id: str | None, ledger_id: int | None = None):
        if period == "all":
            with trace_request_stage("analysis.overview.day"):
                day = self._get_day_overview(user_id, ledger_id=ledger_id)
            with trace_request_stage("analysis.overview.month"):
                month = self.db.get_pnl_overview("month", user_id, ledger_id=ledger_id)
            with trace_request_stage("analysis.overview.year"):
                year = self.db.get_pnl_overview("year", user_id, ledger_id=ledger_id)
            with trace_request_stage("analysis.overview.all"):
                total = self.db.get_pnl_overview("all", user_id, ledger_id=ledger_id)
            return {
                "day": day,
                "month": month,
                "year": year,
                "all": total,
            }

        with trace_request_stage("analysis.overview.single", period=period):
            if period == "day":
                return {"day": self._get_day_overview(user_id, ledger_id=ledger_id)}
            return {period: self.db.get_pnl_overview(period, user_id, ledger_id=ledger_id)}

    def build_calendar_payload(
        self,
        *,
        time_type: str,
        user_id: str | None,
        year: int | None,
        month: int | None,
        ledger_id: int | None = None,
    ):
        with trace_request_stage("analysis.calendar.db", time_type=time_type):
            return self.db.get_calendar_data(time_type, user_id, year=year, month=month, ledger_id=ledger_id)

    def build_market_breakdown_payload(
        self,
        *,
        user_id: str | None,
        year: int | None,
        month: int | None,
        ledger_id: int | None = None,
    ):
        with trace_request_stage("analysis.market_breakdown.db", time_type="day"):
            result = self.db.get_market_breakdown_calendar_data(
                time_type="day",
                user_id=user_id,
                year=year,
                month=month,
                ledger_id=ledger_id,
            )

        return result

    def build_rank_payload(self, *, market: str, user_id: str | None, ledger_id: int | None = None):
        with trace_request_stage("analysis.rank.db", market=market):
            portfolio_data = self.db.get_rank_data("gain", market, user_id, ledger_id=ledger_id)
        if not portfolio_data:
            return {"gain": [], "loss": []}

        codes = [item["code"] for item in portfolio_data]
        with trace_request_stage("analysis.rank.quotes", code_count=len(codes)):
            prices = self.price_batch_getter(codes)

        rates: Dict[str, float] = {}
        if self.rates_getter is not None:
            try:
                rates = self.rates_getter() or {}
            except Exception:
                pass

        # result_items: list of (pnl_cny, item_dict)，pnl_cny 仅用于排序
        result_items = []
        with trace_request_stage("analysis.rank.assemble", item_count=len(portfolio_data)):
            for item in portfolio_data:
                code = item["code"]
                price_info = prices.get(code, (0, 0, 0, 0))
                yclose = float(price_info[1] or 0.0)
                cost_price = float(item["cost_price"] or 0.0)
                # 排行榜用昨收价计算累计盈亏，白天不随行情波动
                if yclose > 0:
                    current_price = yclose
                elif cost_price > 0:
                    current_price = cost_price
                else:
                    current_price = 0.0

                qty = float(item["qty"] or 0.0)
                cost = cost_price * qty
                current_value = current_price * qty
                pnl = current_value - cost + item["adjustment"]
                cost_abs = abs(cost)
                pnl_rate = (pnl / cost_abs * 100) if cost_abs > 0 else 0

                curr = item.get("curr", "CNY")
                # 换算为 CNY 用于跨货币排序，返回值保持原始货币
                pnl_cny = pnl
                if self.convert_amount is not None and curr and curr != "CNY":
                    try:
                        pnl_cny = self.convert_amount(pnl, curr, "CNY", rates)
                    except Exception:
                        pass

                result_items.append(
                    (
                        pnl_cny,
                        {
                            "code": code,
                            "name": item["name"],
                            "pnl": round(pnl, 2),
                            "pnl_rate": round(pnl_rate, 2),
                            "market": item["market"],
                            "curr": curr,
                            "ledger_name": item.get("ledger_name"),
                        },
                    )
                )

        gain_list = [x for _, x in sorted(
            [(cny, x) for cny, x in result_items if cny > 0],
            key=lambda t: t[0],
            reverse=True,
        )]
        loss_list = [x for _, x in sorted(
            [(cny, x) for cny, x in result_items if cny < 0],
            key=lambda t: t[0],
        )]
        return {"gain": gain_list, "loss": loss_list}

"""分析页读侧服务。"""

from __future__ import annotations

from typing import Any, Callable, Dict

from .request_trace import trace_request_stage


class AnalysisReadService:
    def __init__(
        self,
        *,
        db: Any,
        price_batch_getter: Callable[[list[str]], Dict[str, Any]],
        stats_getter: Callable[[str | None], Dict[str, Any]] | None = None,
    ) -> None:
        self.db = db
        self.price_batch_getter = price_batch_getter
        self.stats_getter = stats_getter

    def _get_day_overview(self, user_id: str | None) -> Dict[str, Any]:
        """获取当日盈亏。优先走实时计算，失败时 fallback 到快照表。"""
        if self.stats_getter is not None:
            try:
                stats = self.stats_getter(user_id)
                pnl = float(stats.get("day_pnl") or 0.0)
                # 分母用实时 total_invest（当前持仓市值），
                # 与快照路径的分母口径略有差异，属于设计取舍，不是 bug
                base = float(stats.get("total_invest") or 0.0) or 1.0
                return {
                    "pnl": round(pnl, 2),
                    "pnl_rate": round(pnl / base * 100, 2),
                    "base_value": round(base, 2),
                }
                # 注：前端只读 pnl 和 pnl_rate，base_value 不影响显示
            except Exception:
                pass  # fallback 到快照
        return self.db.get_pnl_overview("day", user_id)

    def build_overview_payload(self, *, period: str, user_id: str | None):
        if period == "all":
            with trace_request_stage("analysis.overview.day"):
                day = self._get_day_overview(user_id)
            with trace_request_stage("analysis.overview.month"):
                month = self.db.get_pnl_overview("month", user_id)
            with trace_request_stage("analysis.overview.year"):
                year = self.db.get_pnl_overview("year", user_id)
            with trace_request_stage("analysis.overview.all"):
                total = self.db.get_pnl_overview("all", user_id)
            return {
                "day": day,
                "month": month,
                "year": year,
                "all": total,
            }

        with trace_request_stage("analysis.overview.single", period=period):
            if period == "day":
                return {"day": self._get_day_overview(user_id)}
            return {period: self.db.get_pnl_overview(period, user_id)}

    def build_calendar_payload(
        self,
        *,
        time_type: str,
        user_id: str | None,
        year: int | None,
        month: int | None,
    ):
        with trace_request_stage("analysis.calendar.db", time_type=time_type):
            return self.db.get_calendar_data(time_type, user_id, year=year, month=month)

    def build_market_breakdown_payload(
        self,
        *,
        user_id: str | None,
        year: int | None,
        month: int | None,
    ):
        with trace_request_stage("analysis.market_breakdown.db", time_type="day"):
            return self.db.get_market_breakdown_calendar_data(
                time_type="day",
                user_id=user_id,
                year=year,
                month=month,
            )

    def build_rank_payload(self, *, market: str, user_id: str | None):
        with trace_request_stage("analysis.rank.db", market=market):
            portfolio_data = self.db.get_rank_data("gain", market, user_id)
        if not portfolio_data:
            return {"gain": [], "loss": []}

        codes = [item["code"] for item in portfolio_data]
        with trace_request_stage("analysis.rank.quotes", code_count=len(codes)):
            prices = self.price_batch_getter(codes)

        result_items = []
        with trace_request_stage("analysis.rank.assemble", item_count=len(portfolio_data)):
            for item in portfolio_data:
                code = item["code"]
                price_info = prices.get(code, (0, 0, 0, 0))
                current_price_raw = float(price_info[0] or 0.0)
                yclose = float(price_info[1] or 0.0)
                cost_price = float(item["cost_price"] or 0.0)
                if current_price_raw > 0:
                    current_price = current_price_raw
                elif yclose > 0:
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

                result_items.append(
                    {
                        "code": code,
                        "name": item["name"],
                        "pnl": round(pnl, 2),
                        "pnl_rate": round(pnl_rate, 2),
                        "market": item["market"],
                        "curr": item.get("curr", "CNY"),
                    }
                )

        gain_list = sorted(
            [x for x in result_items if x["pnl"] > 0],
            key=lambda x: x["pnl"],
            reverse=True,
        )
        loss_list = sorted([x for x in result_items if x["pnl"] < 0], key=lambda x: x["pnl"])
        return {"gain": gain_list, "loss": loss_list}

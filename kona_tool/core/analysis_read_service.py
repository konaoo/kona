"""分析页读侧服务。"""

import logging
import time as _time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FuturesTimeoutError
from typing import Any, Callable, Dict

from .request_trace import trace_request_stage

logger = logging.getLogger(__name__)

# 共享线程池，用于给 stats_getter 调用加超时
_stats_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="analysis_stats")

_DEFAULT_STATS_TIMEOUT = 20.0  # seconds — 待调优，先用宽松值观测实际耗时后再收紧


class AnalysisReadService:
    def __init__(
        self,
        *,
        db: Any,
        price_batch_getter: Callable[[list[str]], Dict[str, Any]],
        stats_getter: Callable[[str | None], Dict[str, Any]] | None = None,
        rates_getter: Callable[[], Dict[str, float]] | None = None,
        convert_amount: Callable[[float, str, str, Dict[str, float]], float] | None = None,
        all_markets_closed_getter: Callable[[], bool] | None = None,
        stats_timeout: float = _DEFAULT_STATS_TIMEOUT,
    ) -> None:
        self.db = db
        self.price_batch_getter = price_batch_getter
        self.stats_getter = stats_getter
        self.rates_getter = rates_getter
        self.convert_amount = convert_amount
        self.all_markets_closed_getter = all_markets_closed_getter
        self.stats_timeout = stats_timeout

    def _get_day_overview(self, user_id: str | None) -> Dict[str, Any]:
        """获取当日盈亏。

        当日概览统一认实时统计层：
        - 开市时显示盘中实时值
        - 休市后显示最后一个有效收益日的最终值

        只有 stats_getter 超时或失败时，才 fallback 到快照。
        """
        if self.stats_getter is not None:
            try:
                t0 = _time.monotonic()
                future = _stats_executor.submit(self.stats_getter, user_id)
                stats = future.result(timeout=self.stats_timeout)
                elapsed = _time.monotonic() - t0
                logger.info("stats_getter completed in %.3fs", elapsed)
                pnl = float(stats.get("day_pnl") or 0.0)
                # 分母用实时 total_invest，与快照口径略有差异，属于设计取舍
                base = float(stats.get("total_invest") or 0.0) or 1.0
                return {
                    "pnl": round(pnl, 2),
                    "pnl_rate": round(pnl / base * 100, 2),
                    "base_value": round(base, 2),
                }
            except _FuturesTimeoutError:
                elapsed = _time.monotonic() - t0
                logger.warning("stats_getter timed out after %.3fs, falling back to snapshot", elapsed)
                pass  # fallback 到快照
            except Exception as exc:
                logger.warning("stats_getter failed (%s), falling back to snapshot", exc)
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
        from datetime import datetime as _dt

        with trace_request_stage("analysis.calendar.db", time_type=time_type):
            result = self.db.get_calendar_data(time_type, user_id, year=year, month=month)

        # 仅在查询日视图且是当月时，把今天那格替换为实时值
        if time_type == "day" and self.stats_getter is not None:
            period = result.get("period") or {}
            if int(period.get("year") or 0) > 0 and int(period.get("month") or 0) > 0:
                try:
                    stats = self.stats_getter(user_id)
                    realtime_pnl = round(float(stats.get("day_pnl") or 0.0), 2)
                    effective_date = str(stats.get("day_pnl_effective_date") or "").strip()
                    if effective_date:
                        effective_dt = _dt.strptime(effective_date[:10], "%Y-%m-%d")
                    else:
                        effective_dt = _dt.now()
                    if int(period.get("year") or 0) != effective_dt.year or int(period.get("month") or 0) != effective_dt.month:
                        return result
                    today_label = f"{effective_dt.month}-{effective_dt.day}"
                    items = list(result.get("items") or [])
                    replaced = False
                    for item in items:
                        if item.get("label") == today_label:
                            item["pnl"] = realtime_pnl
                            replaced = True
                            break
                    if not replaced:
                        items.append({"label": today_label, "pnl": realtime_pnl})
                    result = {**result, "items": items}
                except Exception:
                    pass  # 实时拉取失败，保留快照值

        return result

    def build_market_breakdown_payload(
        self,
        *,
        user_id: str | None,
        year: int | None,
        month: int | None,
    ):
        from datetime import datetime as _dt

        with trace_request_stage("analysis.market_breakdown.db", time_type="day"):
            result = self.db.get_market_breakdown_calendar_data(
                time_type="day",
                user_id=user_id,
                year=year,
                month=month,
            )

        # 当月视图：把今天那条的 total_pnl 替换为实时值（per-market 拆分仍为快照）
        if self.stats_getter is not None:
            if int(result.get("year") or 0) > 0 and int(result.get("month") or 0) > 0:
                try:
                    stats = self.stats_getter(user_id)
                    realtime_pnl = round(float(stats.get("day_pnl") or 0.0), 2)
                    effective_date = str(stats.get("day_pnl_effective_date") or "").strip()
                    if effective_date:
                        effective_dt = _dt.strptime(effective_date[:10], "%Y-%m-%d")
                    else:
                        effective_dt = _dt.now()
                    if int(result.get("year") or 0) != effective_dt.year or int(result.get("month") or 0) != effective_dt.month:
                        return result
                    today_str = effective_dt.strftime("%Y-%m-%d")
                    items = list(result.get("items") or [])
                    new_items = []
                    replaced = False
                    for item in items:
                        if item.get("date") == today_str:
                            new_items.append({**item, "total_pnl": realtime_pnl, "source": "partial_realtime"})
                            replaced = True
                        else:
                            new_items.append(item)
                    if not replaced:
                        new_items.append({
                            "date": today_str,
                            "markets": {"a": None, "hk": None, "us": None, "fund": None, "unallocated": None},
                            "total_pnl": realtime_pnl,
                            "source": "partial_realtime",
                        })
                    result = {**result, "items": new_items}
                except Exception:
                    pass  # 实时拉取失败，保留快照值

        return result

    def build_rank_payload(self, *, market: str, user_id: str | None):
        with trace_request_stage("analysis.rank.db", market=market):
            portfolio_data = self.db.get_rank_data("gain", market, user_id)
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

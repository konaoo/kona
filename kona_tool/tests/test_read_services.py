import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import unittest

from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from core.analysis_read_service import AnalysisReadService  # noqa: E402
from core.history_read_service import HistoryReadService  # noqa: E402
from core.portfolio_read_service import PortfolioReadService  # noqa: E402
from core.request_trace import get_request_stages  # noqa: E402


class _FakeDb:
    def __init__(self):
        self.portfolio_items = [
            {
                "code": "AAPL",
                "name": "Apple",
                "qty": 10,
                "price": 10,
                "adjustment": 0,
                "curr": "USD",
                "asset_type": "us",
            }
        ]
        self.history_items = [{"date": "2026-03-17", "total_asset": 1000}]

    def get_portfolio(self, *args, **kwargs):
        return list(self.portfolio_items)

    def get_history(self, days, user_id):
        return list(self.history_items)

    def get_pnl_overview(self, period, user_id, ledger_id=None):
        return {"pnl": 12.34, "pnl_rate": 1.23, "period": period}

    def get_calendar_data(self, time_type, user_id, year=None, month=None, ledger_id=None):
        return {"items": [], "title": f"{time_type}-calendar"}

    def get_market_breakdown_calendar_data(self, time_type, user_id, year=None, month=None, ledger_id=None):
        return {"items": [], "title": "market-breakdown"}

    def get_rank_data(self, rank_type, market, user_id, ledger_id=None):
        return [
            {
                "code": "AAPL",
                "name": "Apple",
                "qty": 10,
                "cost_price": 10,
                "adjustment": 0,
                "market": "us",
                "curr": "USD",
            }
        ]

    def get_today_buy_transactions(self, date_str, user_id=None):
        return {}


class ReadServicesTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.db = _FakeDb()

    def test_portfolio_read_service_records_db_and_assembly_stages(self):
        service = PortfolioReadService(
            db=self.db,
            batch_get_prices_getter=lambda codes: {"AAPL": (12.0, 11.0, 1.0, 9.09)},
            rates_getter=lambda: {"USD": 7.2, "CNY": 1.0},
            convert_amount=lambda amount, from_curr, to_curr, rates: rates.get(from_curr, 1.0) if to_curr == "CNY" else amount,
            fund_latest_nav_date_getter=lambda code: None,
            market_status_getter=lambda now_utc, force_refresh=False: {
                "markets": {"us": {"open": True, "trading_day": True, "reason": "open"}}
            },
        )

        with self.app.test_request_context("/api/portfolio?with_metrics=1"):
            result = service.build_metrics_payload(
                user_id="u_1",
                now_utc=datetime(2026, 3, 17, tzinfo=timezone.utc),
            )
            stages = [item["stage"] for item in get_request_stages()]

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["code"], "AAPL")
        self.assertEqual(result[0]["current_price"], 12.0)
        self.assertAlmostEqual(result[0]["total_pnl"], 20.0)
        self.assertEqual(
            stages,
            [
                "portfolio.db",
                "portfolio.quotes",
                "portfolio.rates",
                "portfolio.market",
                "portfolio.today_buys",
                "portfolio.assemble",
            ],
        )

    def test_history_read_service_records_db_stage(self):
        service = HistoryReadService(db=self.db)

        with self.app.test_request_context("/api/history?days=30"):
            result = service.get_history(days=30, user_id="u_1")
            stages = get_request_stages()

        self.assertEqual(result, self.db.history_items)
        self.assertEqual(len(stages), 1)
        self.assertEqual(stages[0]["stage"], "history.db")
        self.assertEqual(stages[0]["days"], 30)

    def test_analysis_rank_service_records_rank_stages(self):
        service = AnalysisReadService(
            db=self.db,
            price_batch_getter=lambda codes: {"AAPL": (12.0, 11.0, 1.0, 9.09)},
        )

        with self.app.test_request_context("/api/analysis/rank?market=all"):
            result = service.build_rank_payload(market="all", user_id="u_1")
            stages = [item["stage"] for item in get_request_stages()]

        self.assertEqual(len(result["gain"]), 1)
        self.assertEqual(result["gain"][0]["code"], "AAPL")
        self.assertEqual(result["gain"][0]["pnl"], 10.0)  # 用昨收价(11.0)而非实时价(12.0)计算
        self.assertEqual(
            stages,
            [
                "analysis.rank.db",
                "analysis.rank.quotes",
                "analysis.rank.assemble",
            ],
        )


    def test_calendar_today_cell_uses_stats_getter(self):
        """日历当月视图里，今天那格应用实时 day_pnl 替换快照值"""
        today = datetime.now()
        today_label = str(today.day)

        # db 返回今天那格的快照值 10.0
        db = _FakeDb()
        db.get_calendar_data = lambda time_type, user_id, year=None, month=None, ledger_id=None: {
            "items": [{"label": today_label, "pnl": 10.0}],
            "total_pnl": 10.0,
            "total_rate": 1.0,
            "period": {"time_type": "day", "year": today.year, "month": today.month},
        }

        service = AnalysisReadService(
            db=db,
            price_batch_getter=lambda codes: {},
            stats_getter=lambda user_id: {"day_pnl": 55.0, "total_invest": 1000.0},
        )

        with self.app.test_request_context("/api/analysis/calendar?type=day"):
            result = service.build_calendar_payload(
                time_type="day", user_id="u_1", year=today.year, month=today.month
            )

        today_item = next((i for i in result["items"] if i["label"] == today_label), None)
        self.assertIsNotNone(today_item)
        self.assertAlmostEqual(today_item["pnl"], 55.0)
        # 底部汇总不变，仍是快照值
        self.assertAlmostEqual(result["total_pnl"], 10.0)

    def test_calendar_today_cell_added_when_no_snapshot_yet(self):
        """今天还没有快照时，今天那格应从实时计算补上"""
        today = datetime.now()
        today_label = str(today.day)

        db = _FakeDb()
        db.get_calendar_data = lambda time_type, user_id, year=None, month=None, ledger_id=None: {
            "items": [],  # 今天还没有快照
            "total_pnl": 0.0,
            "total_rate": 0.0,
            "period": {"time_type": "day", "year": today.year, "month": today.month},
        }

        service = AnalysisReadService(
            db=db,
            price_batch_getter=lambda codes: {},
            stats_getter=lambda user_id: {"day_pnl": 77.0, "total_invest": 1000.0},
        )

        with self.app.test_request_context("/api/analysis/calendar?type=day"):
            result = service.build_calendar_payload(
                time_type="day", user_id="u_1", year=today.year, month=today.month
            )

        today_item = next((i for i in result["items"] if i["label"] == today_label), None)
        self.assertIsNotNone(today_item)
        self.assertAlmostEqual(today_item["pnl"], 77.0)

    def test_calendar_effective_date_cell_uses_stats_getter(self):
        """跨时区夜盘应覆盖到收益归属日，不是北京时间今天。"""
        today = datetime.now()
        effective_dt = today - timedelta(days=1)
        effective_label = str(effective_dt.day)
        today_label = str(today.day)

        db = _FakeDb()
        db.get_calendar_data = lambda time_type, user_id, year=None, month=None, ledger_id=None: {
            "items": [
                {"label": effective_label, "pnl": 10.0},
                {"label": today_label, "pnl": 0.0},
            ],
            "total_pnl": 10.0,
            "total_rate": 1.0,
            "period": {"time_type": "day", "year": effective_dt.year, "month": effective_dt.month},
        }

        service = AnalysisReadService(
            db=db,
            price_batch_getter=lambda codes: {},
            stats_getter=lambda user_id: {
                "day_pnl": -794.0,
                "day_pnl_effective_date": effective_dt.strftime("%Y-%m-%d"),
                "total_invest": 1000.0,
            },
        )

        with self.app.test_request_context("/api/analysis/calendar?type=day"):
            result = service.build_calendar_payload(
                time_type="day",
                user_id="u_1",
                year=effective_dt.year,
                month=effective_dt.month,
            )

        effective_item = next((i for i in result["items"] if i["label"] == effective_label), None)
        today_item = next((i for i in result["items"] if i["label"] == today_label), None)
        self.assertIsNotNone(effective_item)
        self.assertAlmostEqual(effective_item["pnl"], -794.0)
        self.assertAlmostEqual(today_item["pnl"], 0.0)

    def test_calendar_past_month_not_affected_by_stats_getter(self):
        """查的是历史月份，今天那格不应被 stats_getter 修改"""
        db = _FakeDb()
        db.get_calendar_data = lambda time_type, user_id, year=None, month=None, ledger_id=None: {
            "items": [{"label": "1-15", "pnl": 20.0}],
            "total_pnl": 20.0,
            "total_rate": 2.0,
            "period": {"time_type": "day", "year": 2026, "month": 1},
        }

        service = AnalysisReadService(
            db=db,
            price_batch_getter=lambda codes: {},
            stats_getter=lambda user_id: {"day_pnl": 99.0, "total_invest": 1000.0},
        )

        with self.app.test_request_context("/api/analysis/calendar?type=day"):
            result = service.build_calendar_payload(
                time_type="day", user_id="u_1", year=2026, month=1
            )

        # 历史月份数据不应被修改
        self.assertEqual(result["items"][0]["pnl"], 20.0)

    def test_analysis_overview_day_uses_stats_getter(self):
        """stats_getter 存在时，day 数据应来自 stats_getter，不走 db.get_pnl_overview"""
        called_with = []

        def fake_stats_getter(user_id):
            called_with.append(user_id)
            return {"day_pnl": 99.0, "total_invest": 1000.0}

        service = AnalysisReadService(
            db=self.db,
            price_batch_getter=lambda codes: {},
            stats_getter=fake_stats_getter,
        )

        with self.app.test_request_context("/api/analysis/overview?period=day"):
            result = service.build_overview_payload(period="day", user_id="u_1")

        self.assertEqual(called_with, ["u_1"])
        self.assertAlmostEqual(result["day"]["pnl"], 99.0)
        self.assertAlmostEqual(result["day"]["pnl_rate"], 9.9)  # 99/1000*100

    def test_analysis_overview_day_prefers_day_pnl_base(self):
        """当实时层已经给出 day_pnl_base 时，day 概览应直接认这套分母。"""
        service = AnalysisReadService(
            db=self.db,
            price_batch_getter=lambda codes: {},
            stats_getter=lambda user_id: {
                "day_pnl": 90.0,
                "day_pnl_base": 600.0,
                "total_invest": 1000.0,
            },
        )

        with self.app.test_request_context("/api/analysis/overview?period=day"):
            result = service.build_overview_payload(period="day", user_id="u_1")

        self.assertAlmostEqual(result["day"]["base_value"], 600.0)
        self.assertAlmostEqual(result["day"]["pnl_rate"], 15.0)

    def test_analysis_overview_day_falls_back_to_snapshot_on_error(self):
        """stats_getter 抛异常时，应 fallback 回 db.get_pnl_overview"""
        def failing_stats_getter(user_id):
            raise RuntimeError("price fetch failed")

        service = AnalysisReadService(
            db=self.db,
            price_batch_getter=lambda codes: {},
            stats_getter=failing_stats_getter,
        )

        with self.app.test_request_context("/api/analysis/overview?period=day"):
            result = service.build_overview_payload(period="day", user_id="u_1")

        # _FakeDb.get_pnl_overview 返回 {"pnl": 12.34, ...}
        self.assertAlmostEqual(result["day"]["pnl"], 12.34)

    def test_overview_day_still_uses_stats_getter_when_all_markets_closed(self):
        """全市场休市后，当日概览仍应显示最后一个有效收益日的最终值"""
        stats_called = []

        def tracking_stats_getter(user_id):
            stats_called.append(user_id)
            return {"day_pnl": 99.0, "total_invest": 1000.0}

        service = AnalysisReadService(
            db=self.db,
            price_batch_getter=lambda codes: {},
            stats_getter=tracking_stats_getter,
            all_markets_closed_getter=lambda: True,  # 全部休市
        )

        with self.app.test_request_context("/api/analysis/overview?period=day"):
            result = service.build_overview_payload(period="day", user_id="u_1")

        self.assertEqual(stats_called, ["u_1"])
        self.assertAlmostEqual(result["day"]["pnl"], 99.0)

    def test_overview_day_uses_stats_getter_when_markets_open(self):
        """有市场开市时应调用 stats_getter 获取实时数据"""
        service = AnalysisReadService(
            db=self.db,
            price_batch_getter=lambda codes: {},
            stats_getter=lambda user_id: {"day_pnl": 88.0, "total_invest": 1000.0},
            all_markets_closed_getter=lambda: False,  # 有市场开市
        )

        with self.app.test_request_context("/api/analysis/overview?period=day"):
            result = service.build_overview_payload(period="day", user_id="u_1")

        self.assertAlmostEqual(result["day"]["pnl"], 88.0)

    def test_overview_day_falls_back_on_stats_getter_timeout(self):
        """stats_getter 超时应 fallback 到快照"""
        def slow_stats_getter(user_id):
            time.sleep(1.0)  # 比 timeout 慢
            return {"day_pnl": 99.0, "total_invest": 1000.0}

        service = AnalysisReadService(
            db=self.db,
            price_batch_getter=lambda codes: {},
            stats_getter=slow_stats_getter,
            all_markets_closed_getter=lambda: False,
            stats_timeout=0.1,  # 100ms 超时
        )

        with self.app.test_request_context("/api/analysis/overview?period=day"):
            result = service.build_overview_payload(period="day", user_id="u_1")

        # 超时后 fallback 到快照值
        self.assertAlmostEqual(result["day"]["pnl"], 12.34)

    def test_rank_uses_cny_for_cross_currency_sorting(self):
        """多货币持仓排行应换算为 CNY 后排序，返回值保持原始货币"""
        db = _FakeDb()
        db.get_rank_data = lambda rank_type, market, user_id, ledger_id=None: [
            {
                "code": "AAPL",
                "name": "Apple",
                "qty": 10,
                "cost_price": 10,
                "adjustment": 0,
                "market": "us",
                "curr": "USD",
            },
            {
                "code": "sh600000",
                "name": "工行",
                "qty": 100,
                "cost_price": 9,
                "adjustment": 0,
                "market": "a",
                "curr": "CNY",
            },
        ]
        service = AnalysisReadService(
            db=db,
            # AAPL: yclose=11, pnl=10*(11-10)=10 USD → 70 CNY
            # sh600000: yclose=9.5, pnl=100*(9.5-9)=50 CNY
            # 换算后 AAPL(70) > sh600000(50)，AAPL 应排第一
            price_batch_getter=lambda codes: {
                "AAPL": (0, 11.0, 0, 0),
                "sh600000": (0, 9.5, 0, 0),
            },
            rates_getter=lambda: {"USD": 7.0, "CNY": 1.0},
            convert_amount=lambda amount, from_curr, to_curr, rates: amount * rates.get(from_curr, 1.0)
            if to_curr == "CNY"
            else amount,
        )

        with self.app.test_request_context("/api/analysis/rank?market=all"):
            result = service.build_rank_payload(market="all", user_id="u_1")

        self.assertEqual(result["gain"][0]["code"], "AAPL")
        self.assertEqual(result["gain"][1]["code"], "sh600000")
        # pnl 应保持原始货币
        self.assertAlmostEqual(result["gain"][0]["pnl"], 10.0)  # USD
        self.assertAlmostEqual(result["gain"][1]["pnl"], 50.0)  # CNY

    def test_rank_without_currency_converter_falls_back_to_native_pnl_sort(self):
        """未注入 convert_amount 时，直接按原始货币 pnl 排序（兼容旧行为）"""
        db = _FakeDb()
        db.get_rank_data = lambda rank_type, market, user_id, ledger_id=None: [
            {"code": "AAPL", "name": "Apple", "qty": 10, "cost_price": 10, "adjustment": 0, "market": "us", "curr": "USD"},
            {"code": "sh600000", "name": "工行", "qty": 100, "cost_price": 9, "adjustment": 0, "market": "a", "curr": "CNY"},
        ]
        service = AnalysisReadService(
            db=db,
            price_batch_getter=lambda codes: {
                "AAPL": (0, 11.0, 0, 0),
                "sh600000": (0, 9.5, 0, 0),
            },
        )

        with self.app.test_request_context("/api/analysis/rank?market=all"):
            result = service.build_rank_payload(market="all", user_id="u_1")

        # 无换算时按原始 pnl 排：sh600000(50 CNY) > AAPL(10 USD)
        self.assertEqual(result["gain"][0]["code"], "sh600000")
        self.assertEqual(result["gain"][1]["code"], "AAPL")

    def test_market_breakdown_today_keeps_snapshot_row_consistent(self):
        """分市场日历同一行里的总值和分项都应保持快照口径。"""
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        db = _FakeDb()
        db.get_market_breakdown_calendar_data = lambda time_type, user_id, year=None, month=None, ledger_id=None: {
            "time_type": "day",
            "year": today.year,
            "month": today.month,
            "items": [
                {
                    "date": today_str,
                    "markets": {"a": 5.0, "hk": None, "us": None, "fund": None, "unallocated": None},
                    "total_pnl": 5.0,
                    "source": "estimated",
                }
            ],
        }

        service = AnalysisReadService(
            db=db,
            price_batch_getter=lambda codes: {},
            stats_getter=lambda user_id: {"day_pnl": 88.0, "total_invest": 1000.0},
        )

        with self.app.test_request_context("/api/analysis/market_breakdown"):
            result = service.build_market_breakdown_payload(
                user_id="u_1", year=today.year, month=today.month
            )

        today_item = next((i for i in result["items"] if i["date"] == today_str), None)
        self.assertIsNotNone(today_item)
        self.assertAlmostEqual(today_item["total_pnl"], 5.0)
        self.assertEqual(today_item["source"], "estimated")
        self.assertAlmostEqual(today_item["markets"]["a"], 5.0)

    def test_market_breakdown_past_month_not_affected_by_stats_getter(self):
        """历史月份不应被 stats_getter 修改"""
        db = _FakeDb()
        db.get_market_breakdown_calendar_data = lambda time_type, user_id, year=None, month=None, ledger_id=None: {
            "time_type": "day",
            "year": 2026,
            "month": 1,
            "items": [
                {
                    "date": "2026-01-15",
                    "markets": {"a": 10.0, "hk": None, "us": None, "fund": None, "unallocated": None},
                    "total_pnl": 10.0,
                    "source": "exact",
                }
            ],
        }

        service = AnalysisReadService(
            db=db,
            price_batch_getter=lambda codes: {},
            stats_getter=lambda user_id: {"day_pnl": 999.0, "total_invest": 1000.0},
        )

        with self.app.test_request_context("/api/analysis/market_breakdown"):
            result = service.build_market_breakdown_payload(user_id="u_1", year=2026, month=1)

        self.assertAlmostEqual(result["items"][0]["total_pnl"], 10.0)
        self.assertEqual(result["items"][0]["source"], "exact")


    def test_portfolio_day_pnl_excludes_intraday_buy_under_bookkeeping_rule(self):
        """记账口径下，今日新增买入不参与 day_pnl。"""
        # 持仓 10 股，今日加仓 4 股；当前价 12.0，昨收 11.0
        # 只看昨仓 6 股：预期 (12-11)*6 = 6
        db = _FakeDb()
        db.portfolio_items = [
            {"code": "sh600001", "name": "Test", "qty": 10, "price": 9.5, "adjustment": 0, "curr": "CNY", "asset_type": "a"}
        ]
        db.get_today_buy_transactions = lambda date_str, user_id=None: {
            "sh600001": {"qty": 4.0, "amount": 36.0}  # 4 股，均价 9.0
        }
        service = PortfolioReadService(
            db=db,
            batch_get_prices_getter=lambda codes: {"sh600001": (12.0, 11.0, 1.0, 0.1)},
            rates_getter=lambda: {},
            convert_amount=lambda amount, f, t, rates: amount,
            fund_latest_nav_date_getter=lambda code: None,
            market_status_getter=lambda now_utc, force_refresh=False: {
                "markets": {"a": {"open": True, "trading_day": True, "reason": "open"}}
            },
        )
        with self.app.test_request_context("/api/portfolio"):
            result = service.build_metrics_payload(user_id="u_1")
        item = result[0]
        self.assertAlmostEqual(item["day_pnl"], 6.0)
        self.assertAlmostEqual(item["day_pnl_rate"], (1.0 / 11.0) * 100)

    def test_portfolio_total_pnl_rate_uses_current_cost_base(self):
        """累计收益率只认当前这只持仓还压着的本金。"""
        # 持仓成本 cost=100*10=1000, 当前价 12, 市值 1200
        # adjustment=200 (已实现盈亏), total_pnl = (12-10)*100 + 200 = 400
        # 分母 = |1000|
        # rate = 400 / 1000 * 100 = 40%
        db = _FakeDb()
        db.portfolio_items = [
            {"code": "sh600002", "name": "Test2", "qty": 100, "price": 10.0, "adjustment": 200.0, "curr": "CNY", "asset_type": "a"}
        ]
        service = PortfolioReadService(
            db=db,
            batch_get_prices_getter=lambda codes: {"sh600002": (12.0, 11.0, 1.0, 0.1)},
            rates_getter=lambda: {},
            convert_amount=lambda amount, f, t, rates: amount,
            fund_latest_nav_date_getter=lambda code: None,
            market_status_getter=lambda now_utc, force_refresh=False: {
                "markets": {"a": {"open": False, "trading_day": False, "reason": "closed"}}
            },
        )
        with self.app.test_request_context("/api/portfolio"):
            result = service.build_metrics_payload(user_id="u_1")
        item = result[0]
        self.assertAlmostEqual(item["total_pnl"], 400.0)
        self.assertAlmostEqual(item["total_pnl_base"], 1000.0, places=4)
        self.assertAlmostEqual(item["total_pnl_rate"], 400.0 / 1000.0 * 100, places=4)

    def test_portfolio_read_service_includes_latest_nav_date_for_otc_fund(self):
        db = _FakeDb()
        db.portfolio_items = [
            {
                "code": "f_110017",
                "name": "基金A",
                "qty": 10,
                "price": 1.23,
                "adjustment": 0,
                "curr": "CNY",
                "asset_type": "fund",
            }
        ]
        service = PortfolioReadService(
            db=db,
            batch_get_prices_getter=lambda codes: {"f_110017": (1.25, 1.24, 0.01, 0.8)},
            rates_getter=lambda: {},
            convert_amount=lambda amount, f, t, rates: amount,
            fund_latest_nav_date_getter=lambda code: "2026-03-19" if code == "f_110017" else None,
            market_status_getter=lambda now_utc, force_refresh=False: {
                "markets": {"fund": {"open": False, "trading_day": False, "reason": "fund"}}
            },
        )

        with self.app.test_request_context("/api/portfolio"):
            result = service.build_metrics_payload(user_id="u_1")

        self.assertEqual(result[0]["latest_nav_date"], "2026-03-19")
        self.assertTrue(result[0]["nav_update_pending"])


if __name__ == "__main__":
    unittest.main()

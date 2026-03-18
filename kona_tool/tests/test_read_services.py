import sys
from datetime import datetime, timezone
from pathlib import Path
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

    def get_pnl_overview(self, period, user_id):
        return {"pnl": 12.34, "pnl_rate": 1.23, "period": period}

    def get_calendar_data(self, time_type, user_id, year=None, month=None):
        return {"items": [], "title": f"{time_type}-calendar"}

    def get_market_breakdown_calendar_data(self, time_type, user_id, year=None, month=None):
        return {"items": [], "title": "market-breakdown"}

    def get_rank_data(self, rank_type, market, user_id):
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
        self.assertEqual(result["gain"][0]["pnl"], 20.0)
        self.assertEqual(
            stages,
            [
                "analysis.rank.db",
                "analysis.rank.quotes",
                "analysis.rank.assemble",
            ],
        )


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


if __name__ == "__main__":
    unittest.main()

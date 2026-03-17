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


if __name__ == "__main__":
    unittest.main()

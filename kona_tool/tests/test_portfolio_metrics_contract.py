import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_metrics.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


def _seed_user(
    user_id: str,
    username: str,
    is_admin: int = 0,
    status: str = "active",
    password_hash: str = "scrypt$16384$8$1$U0FMVA==$SEFTSA==",
) -> None:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
        VALUES (?, ?, ?, 0, ?, ?)
        """,
        (user_id, username, password_hash, is_admin, status),
    )
    conn.commit()
    conn.close()


def _seed_portfolio(
    user_id: str,
    code: str = "sh600000",
    name: str = "Test",
    qty: float = 10.0,
    price: float = 10.0,
    curr: str = "CNY",
    adjustment: float = 0.0,
    asset_type: str = "a",
) -> None:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (code, name, qty, price, curr, adjustment, asset_type, user_id),
    )
    conn.commit()
    conn.close()


def _seed_portfolio_adjustment_event(
    user_id: str,
    code: str,
    amount: float,
    event_type: str = "dividend",
    curr: str = "CNY",
) -> None:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO portfolio_adjustment_ledger (user_id, code, event_type, amount, curr, note, source)
        VALUES (?, ?, ?, ?, ?, '', 'test')
        """,
        (user_id, code, event_type, amount, curr),
    )
    conn.commit()
    conn.close()


def _auth_headers(user_id: str, username: str) -> dict:
    token = app_module.generate_token(user_id, username)
    return {"Authorization": f"Bearer {token}"}


class PortfolioMetricsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        app_module.request_runtime.reset_transient_state()
        with app_module.market_runtime._market_status_lock:
            app_module.market_runtime._market_status_cache.clear()
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio_adjustment_ledger")
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM runtime_configs")
        conn.commit()
        conn.close()

    def test_portfolio_with_metrics_includes_expected_fields(self):
        _seed_user("u_metrics", "metrics_user")
        _seed_portfolio("u_metrics")
        headers = _auth_headers("u_metrics", "metrics_user")

        with patch(
            "app.batch_get_prices",
            return_value={"sh600000": (12.0, 11.0, 1.0, 0.1, None)},
        ), patch(
            "app.get_market_statuses",
            return_value={"a": {"open": False, "trading_day": False, "reason": "test"}},
        ):
            resp = self.client.get("/api/portfolio?with_metrics=1", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(isinstance(data, list))
        self.assertTrue(data)
        item = data[0]
        for key in (
            "current_price",
            "display_cost_price",
            "value_cny",
            "position_pct",
            "cost_cny",
            "total_pnl_cny",
            "total_pnl_base_cny",
            "day_pnl_aggregate_cny",
            "day_pnl_base_aggregate_cny",
            "day_pnl_rate_aggregate",
            "market",
            "market_open",
            "market_trading_day",
        ):
            self.assertIn(key, item)

    def test_sync_bootstrap_portfolio_metrics_includes_expected_fields(self):
        _seed_user("u_sync", "sync_user")
        _seed_portfolio("u_sync")
        headers = _auth_headers("u_sync", "sync_user")
        payload = {
            "include": ["portfolio"],
            "client_versions": {"portfolio": ""},
            "portfolio_metrics": True,
        }

        with patch(
            "app.batch_get_prices",
            return_value={"sh600000": (12.0, 11.0, 1.0, 0.1, None)},
        ), patch(
            "app.get_market_statuses",
            return_value={"a": {"open": False, "trading_day": False, "reason": "test"}},
        ):
            resp = self.client.post("/api/sync/bootstrap", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        data = body.get("data") or {}
        portfolio = data.get("portfolio") or []
        self.assertTrue(portfolio)
        item = portfolio[0]
        for key in (
            "current_price",
            "display_cost_price",
            "value_cny",
            "position_pct",
            "cost_cny",
            "total_pnl_cny",
            "total_pnl_base_cny",
            "day_pnl_aggregate_cny",
            "day_pnl_base_aggregate_cny",
            "day_pnl_rate_aggregate",
        ):
            self.assertIn(key, item)

    def test_exchange_fund_uses_a_market_status_and_realtime_day_pnl(self):
        _seed_user("u_etf", "etf_user")
        _seed_portfolio(
            "u_etf",
            code="f_511360",
            name="海富通中证短融ETF",
            qty=100.0,
            price=1.0,
            curr="CNY",
            asset_type="fund",
        )
        headers = _auth_headers("u_etf", "etf_user")

        with patch(
            "app.batch_get_prices",
            return_value={"f_511360": (1.02, 1.0, 0.02, 2.0, None)},
        ), patch(
            "app.get_market_statuses",
            return_value={
                "a": {"open": True, "trading_day": True, "reason": "a_test"},
                "fund": {
                    "open": False,
                    "trading_day": False,
                    "reason": "fund_test",
                },
            },
        ):
            resp = self.client.get("/api/portfolio?with_metrics=1", headers=headers)

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data)
        item = data[0]
        self.assertEqual(item.get("market"), "fund")
        self.assertFalse(item.get("nav_update_pending"))
        self.assertTrue(item.get("day_pnl_display_enabled"))
        self.assertTrue(item.get("market_trading_day"))
        self.assertTrue(item.get("market_open"))

    def test_portfolio_metrics_aggregates_ledger_adjustment_into_total_pnl(self):
        _seed_user("u_ledger", "ledger_user")
        _seed_portfolio("u_ledger", code="sh600001", qty=10.0, price=10.0, adjustment=5.0)
        _seed_portfolio_adjustment_event("u_ledger", "sh600001", 15.0)
        headers = _auth_headers("u_ledger", "ledger_user")

        with patch(
            "app.batch_get_prices",
            return_value={"sh600001": (12.0, 11.0, 1.0, 0.1, None)},
        ), patch(
            "app.get_market_statuses",
            return_value={"a": {"open": False, "trading_day": False, "reason": "test"}},
        ):
            resp = self.client.get("/api/portfolio?with_metrics=1", headers=headers)

        self.assertEqual(resp.status_code, 200)
        item = (resp.get_json() or [])[0]
        self.assertAlmostEqual(float(item.get("legacy_adjustment") or 0.0), 5.0, places=6)
        self.assertAlmostEqual(float(item.get("ledger_adjustment") or 0.0), 15.0, places=6)
        self.assertAlmostEqual(float(item.get("adjustment_total") or 0.0), 20.0, places=6)
        self.assertAlmostEqual(float(item.get("total_pnl") or 0.0), 40.0, places=6)
        self.assertAlmostEqual(float(item.get("total_pnl_base") or 0.0), 100.0, places=6)

    def test_portfolio_metrics_ignore_legacy_adjustment_after_migration_switch(self):
        _seed_user("u_ledger_cutover", "ledger_cutover_user")
        _seed_portfolio("u_ledger_cutover", code="sh600009", qty=10.0, price=10.0, adjustment=5.0)
        _seed_portfolio_adjustment_event("u_ledger_cutover", "sh600009", 15.0)
        app_module.db.set_portfolio_legacy_adjustment_ignored(
            True,
            user_id="u_ledger_cutover",
            note="切到新口径",
        )
        headers = _auth_headers("u_ledger_cutover", "ledger_cutover_user")

        with patch(
            "app.batch_get_prices",
            return_value={"sh600009": (12.0, 11.0, 1.0, 0.1, None)},
        ), patch(
            "app.get_market_statuses",
            return_value={"a": {"open": False, "trading_day": False, "reason": "test"}},
        ):
            resp = self.client.get("/api/portfolio?with_metrics=1", headers=headers)

        self.assertEqual(resp.status_code, 200)
        item = (resp.get_json() or [])[0]
        self.assertTrue(bool(item.get("legacy_adjustment_ignored")))
        self.assertAlmostEqual(float(item.get("legacy_adjustment") or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(item.get("ledger_adjustment") or 0.0), 15.0, places=6)
        self.assertAlmostEqual(float(item.get("adjustment_total") or 0.0), 15.0, places=6)
        self.assertAlmostEqual(float(item.get("total_pnl") or 0.0), 35.0, places=6)
        self.assertAlmostEqual(float(item.get("total_pnl_base") or 0.0), 100.0, places=6)

    def test_today_buy_is_excluded_from_day_pnl_by_bookkeeping_rule(self):
        _seed_user("u_today_buy", "today_buy_user")
        _seed_portfolio(
            "u_today_buy",
            code="f_159687",
            name="南方基金南方东英富时亚太低碳精选ETF(QDII)",
            qty=1581.7335,
            price=2.1,
            curr="CNY",
            asset_type="fund",
            adjustment=1.0,
        )
        headers = _auth_headers("u_today_buy", "today_buy_user")

        with patch.object(
            app_module.db,
            "get_today_buy_transactions",
            return_value={"f_159687": {"qty": 1000.0, "amount": 1550.0}},
        ), patch(
            "app.batch_get_prices",
            return_value={"f_159687": (1.602, 1.607, -0.005, -0.3111387678904725, None)},
        ), patch(
            "app.get_market_statuses",
            return_value={
                "fund": {"open": False, "trading_day": False, "reason": "test"},
            },
        ):
            resp = self.client.get("/api/portfolio?with_metrics=1", headers=headers)

        self.assertEqual(resp.status_code, 200)
        item = (resp.get_json() or [])[0]
        self.assertAlmostEqual(float(item.get("day_pnl") or 0.0), -2.9086675, places=6)
        self.assertAlmostEqual(float(item.get("day_pnl_base") or 0.0), 934.8457345, places=6)
        self.assertAlmostEqual(float(item.get("day_pnl_rate") or 0.0), -0.3111387678904725, places=6)
        self.assertLess(float(item.get("quote_change_pct") or 0.0), 0.0)

    def test_same_day_new_position_does_not_show_day_pnl(self):
        _seed_user("u_same_day_only", "same_day_only_user")
        _seed_portfolio(
            "u_same_day_only",
            code="f_520870",
            name="易方达伊塔乌巴西IBOVESPAETF(QDII)",
            qty=500.0,
            price=1.88,
            curr="CNY",
            asset_type="fund",
        )
        headers = _auth_headers("u_same_day_only", "same_day_only_user")

        with patch.object(
            app_module.db,
            "get_today_buy_transactions",
            return_value={"f_520870": {"qty": 500.0, "amount": 940.0}},
        ), patch(
            "app.batch_get_prices",
            return_value={"f_520870": (1.166, 1.165, 0.001, 0.08583690987123517, None)},
        ), patch(
            "app.get_market_statuses",
            return_value={
                "fund": {"open": False, "trading_day": False, "reason": "test"},
            },
        ):
            resp = self.client.get("/api/portfolio?with_metrics=1", headers=headers)

        self.assertEqual(resp.status_code, 200)
        item = (resp.get_json() or [])[0]
        self.assertAlmostEqual(float(item.get("day_pnl") or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(item.get("day_pnl_rate") or 0.0), 0.0, places=6)
        self.assertFalse(bool(item.get("day_pnl_display_enabled")))


if __name__ == "__main__":
    unittest.main()

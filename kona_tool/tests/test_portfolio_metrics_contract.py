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


def _auth_headers(user_id: str, username: str) -> dict:
    token = app_module.generate_token(user_id, username)
    return {"Authorization": f"Bearer {token}"}


class PortfolioMetricsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_portfolio_with_metrics_includes_expected_fields(self):
        _seed_user("u_metrics", "metrics_user")
        _seed_portfolio("u_metrics")
        headers = _auth_headers("u_metrics", "metrics_user")

        with patch(
            "app.batch_get_prices",
            return_value={"sh600000": (12.0, 11.0, 1.0, 0.1)},
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
            "day_pnl_aggregate_cny",
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
            return_value={"sh600000": (12.0, 11.0, 1.0, 0.1)},
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
            "day_pnl_aggregate_cny",
            "day_pnl_rate_aggregate",
        ):
            self.assertIn(key, item)


if __name__ == "__main__":
    unittest.main()

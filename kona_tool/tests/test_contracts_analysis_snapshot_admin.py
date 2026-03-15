import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_contracts.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402
import admin_routes as admin_routes_module  # noqa: E402


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


def _auth_headers(user_id: str, username: str) -> dict:
    token = app_module.generate_token(user_id, username)
    return {"Authorization": f"Bearer {token}"}


def _insert_snapshot(
    date: str,
    *,
    total_asset: float = 1.0,
    total_invest: float = 100.0,
    total_cash: float = 1.0,
    total_other: float = 0.0,
    total_liability: float = 0.0,
    total_pnl: float = 10.0,
    day_pnl: float = 2.0,
    user_id: str = "",
) -> None:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO daily_snapshots
        (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            date,
            total_asset,
            total_invest,
            total_cash,
            total_other,
            total_liability,
            total_pnl,
            day_pnl,
            user_id,
        ),
    )
    conn.commit()
    conn.close()


def _insert_portfolio(
    user_id: str = "",
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


class AnalysisContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM daily_snapshot_market_breakdowns")
        cursor.execute("DELETE FROM daily_snapshots")
        conn.commit()
        conn.close()

    def test_analysis_overview_contract(self):
        _insert_snapshot("2026-02-01", total_pnl=10.0, day_pnl=1.0)
        _insert_snapshot("2026-02-02", total_pnl=12.0, day_pnl=2.0)
        resp = self.client.get("/api/analysis/overview?period=all")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        for key in ("day", "month", "year", "all"):
            self.assertIn(key, payload)
            item = payload.get(key) or {}
            self.assertIn("pnl", item)
            self.assertIn("pnl_rate", item)
            self.assertIn("base_value", item)

    def test_analysis_calendar_contract(self):
        _insert_snapshot("2026-02-03", total_pnl=100.0, day_pnl=10.0)
        _insert_snapshot("2026-02-04", total_pnl=120.0, day_pnl=20.0)
        resp = self.client.get("/api/analysis/calendar?type=day&year=2026&month=2")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertIn("items", payload)
        self.assertIn("total_pnl", payload)
        self.assertIn("total_rate", payload)
        self.assertIn("title", payload)
        period = payload.get("period") or {}
        self.assertEqual(period.get("time_type"), "day")
        self.assertEqual(period.get("year"), 2026)
        self.assertEqual(period.get("month"), 2)
        selectable = payload.get("selectable") or {}
        self.assertIn("day", selectable)
        self.assertIn("month", selectable)
        if payload.get("items"):
            first = payload["items"][0]
            self.assertIn("label", first)
            self.assertIn("pnl", first)

    def test_analysis_rank_contract(self):
        _insert_portfolio(code="sh600000", name="Test", qty=10, price=10, curr="CNY", adjustment=0.0)
        with patch(
            "app.batch_get_prices",
            return_value={"sh600000": (12.0, 11.0, 1.0, 0.1)},
        ):
            resp = self.client.get("/api/analysis/rank?type=all&market=all")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertIn("gain", payload)
        self.assertIn("loss", payload)
        if payload["gain"]:
            item = payload["gain"][0]
            for key in ("code", "name", "pnl", "pnl_rate", "market", "curr"):
                self.assertIn(key, item)

    def test_analysis_market_breakdown_contract(self):
        _insert_snapshot("2026-02-03", total_pnl=100.0, day_pnl=10.0)
        app_module.db.save_daily_snapshot_market_breakdown(
            date_str="2026-02-03",
            day_pnl_by_market={"a": 5, "hk": 0, "us": 0, "fund": 0, "unallocated": 5},
            total_day_pnl=10.0,
            user_id="",
            source="exact",
            confidence=1.0,
            meta_by_market=None,
        )
        resp = self.client.get("/api/analysis/calendar/market_breakdown?type=day&year=2026&month=2")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        for key in ("time_type", "year", "month", "items"):
            self.assertIn(key, payload)
        if payload.get("items"):
            item = payload["items"][0]
            for key in ("date", "markets", "total_pnl", "source"):
                self.assertIn(key, item)
            markets = item.get("markets") or {}
            for key in ("a", "hk", "us", "fund", "unallocated"):
                self.assertIn(key, markets)


class SnapshotContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_snapshot_market_breakdowns")
        cursor.execute("DELETE FROM daily_snapshots")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_snapshot_save_contract(self):
        payload = {
            "total_asset": 100.0,
            "total_invest": 80.0,
            "total_cash": 20.0,
            "total_other": 0.0,
            "total_liability": 0.0,
            "total_pnl": 5.0,
            "day_pnl": 1.0,
            "day_pnl_by_market": {"a": 1.0, "hk": 0.0, "us": 0.0, "fund": 0.0, "unallocated": 0.0},
        }
        resp = self.client.post("/api/snapshot/save", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertEqual(data.get("status"), "ok")

    def test_snapshot_trigger_contract(self):
        with patch("app.take_snapshot", return_value=True):
            resp = self.client.post("/api/snapshot/trigger", json={})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("message", data)

    def test_snapshot_fix_contract(self):
        with patch.object(app_module.db, "fix_snapshot_day_pnl", return_value=True):
            resp = self.client.post("/api/snapshot/fix", json={"dates": ["2026-02-01", "2026-02-02"]})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("message", data)


class AdminContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_admin_users_metrics_contract(self):
        _seed_user("u_admin", "admin_user", is_admin=1)
        headers = _auth_headers("u_admin", "admin_user")
        with patch.object(
            admin_routes_module,
            "_get_user_ops_metrics",
            return_value={
                "user_total": 1,
                "new_today": 0,
                "new_7d": 0,
                "new_30d": 0,
                "dau": 0,
                "wau": 0,
                "mau": 0,
                "last_login_distribution": {
                    "within_1d": 0,
                    "within_7d": 0,
                    "within_30d": 0,
                    "over_30d": 0,
                    "never_login": 1,
                },
            },
        ):
            resp = self.client.get("/api/admin/users/metrics", headers=headers)
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        for key in (
            "user_total",
            "new_today",
            "new_7d",
            "new_30d",
            "dau",
            "wau",
            "mau",
            "last_login_distribution",
            "as_of",
        ):
            self.assertIn(key, payload)

    def test_admin_apis_health_contract(self):
        _seed_user("u_admin", "admin_user", is_admin=1)
        headers = _auth_headers("u_admin", "admin_user")
        with patch.object(
            admin_routes_module.system_manager,
            "check_api_status",
            return_value={"price": {"ok": True}},
        ), patch.object(
            admin_routes_module.system_manager,
            "get_version_info",
            return_value={"version": "test", "commit_hash": "abc", "last_update": "now"},
        ), patch.object(
            app_module.db,
            "list_admin_api_policies",
            return_value=[],
        ), patch.object(
            admin_routes_module,
            "get_price_runtime_metrics",
            return_value={"cache_hits": 1},
        ), patch.object(
            admin_routes_module,
            "get_price_source_health",
            return_value={"sina_stock": {"ok": 1}},
        ):
            resp = self.client.get("/api/admin/apis/health", headers=headers)
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        for key in (
            "status",
            "server_time_utc",
            "db",
            "upstream",
            "policies",
            "runtime",
            "sources",
            "version_info",
        ):
            self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()

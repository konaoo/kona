import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_admin.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402
import admin_routes  # noqa: E402
from core.auth import hash_password  # noqa: E402


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


class AdminApiFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        if hasattr(admin_routes, "_admin_cache_clear"):
            admin_routes._admin_cache_clear()
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM admin_audit_logs")
        cursor.execute("DELETE FROM daily_snapshots")
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def _latest_audit(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT admin_user_id, action, result, status_code
            FROM admin_audit_logs
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()
        return row

    def test_non_admin_access_any_admin_api_returns_403(self):
        _seed_user("u_non_admin", "nonadmin_user", is_admin=0, status="active")
        resp = self.client.get(
            "/api/admin/overview",
            headers=_auth_headers("u_non_admin", "nonadmin_user"),
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json().get("error"), "Admin privileges required")

    @patch("core.auth.config.ALLOW_LOCAL_ADMIN_BYPASS", True)
    def test_local_bypass_allows_admin_overview_without_token(self):
        resp = self.client.get("/api/admin/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("users", data)
        self.assertIn("snapshots", data)

    def test_admin_overview_for_admin_user(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.get(
            "/api/admin/overview",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("users", data)
        self.assertIn("snapshots", data)

    def test_admin_overview_returns_dashboard_and_retention_rows(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_u1", "user_u1", is_admin=0, status="active")
        _seed_user("u_u2", "user_u2", is_admin=0, status="active")

        today = datetime.now().date()
        cohort_day = today - timedelta(days=40)
        retained_day = cohort_day + timedelta(days=8)
        today_str = today.isoformat()
        cohort_str = cohort_day.isoformat()
        retained_str = retained_day.isoformat()

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET created_at = ?, last_login = ?
            WHERE id = ?
            """,
            (f"{cohort_str} 09:00:00", f"{retained_str} 09:00:00", "u_u1"),
        )
        cursor.execute(
            """
            UPDATE users
            SET created_at = ?, last_login = NULL
            WHERE id = ?
            """,
            (f"{cohort_str} 10:00:00", "u_u2"),
        )
        cursor.execute(
            """
            UPDATE users
            SET created_at = ?, last_login = ?
            WHERE id = ?
            """,
            (f"{today_str} 11:00:00", f"{today_str} 12:00:00", "u_admin"),
        )
        conn.commit()
        conn.close()

        resp = self.client.get(
            "/api/admin/overview",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        dashboard = data.get("dashboard") or {}
        self.assertIn("new_users_today", dashboard)
        self.assertIn("active_users_today", dashboard)
        self.assertIn("total_users", dashboard)

        rows = data.get("retention_rows") or []
        self.assertTrue(rows)
        cohort_row = next((r for r in rows if (r.get("date") or "") == cohort_str), None)
        self.assertIsNotNone(cohort_row)
        self.assertEqual(int(cohort_row.get("new_users") or 0), 2)
        self.assertIn("active_users", cohort_row)
        self.assertAlmostEqual(float(cohort_row.get("retention_1d") or 0), 0.5, places=3)
        self.assertAlmostEqual(float(cohort_row.get("retention_3d") or 0), 0.5, places=3)
        self.assertAlmostEqual(float(cohort_row.get("retention_7d") or 0), 0.5, places=3)
        self.assertAlmostEqual(float(cohort_row.get("retention_14d") or 0), 0.0, places=3)
        self.assertAlmostEqual(float(cohort_row.get("retention_30d") or 0), 0.0, places=3)

    def test_admin_overview_force_param_bypasses_read_cache(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        header = _auth_headers("u_admin", "admin_user")
        if hasattr(admin_routes, "_admin_cache_clear"):
            admin_routes._admin_cache_clear()

        metrics_side_effect = [
            {
                "user_total": 11,
                "new_today": 1,
                "new_7d": 1,
                "new_30d": 1,
                "dau": 2,
                "wau": 2,
                "mau": 2,
                "last_login_distribution": {
                    "within_1d": 1,
                    "within_7d": 1,
                    "within_30d": 0,
                    "over_30d": 0,
                    "never_login": 0,
                },
            },
            {
                "user_total": 22,
                "new_today": 2,
                "new_7d": 2,
                "new_30d": 2,
                "dau": 3,
                "wau": 3,
                "mau": 3,
                "last_login_distribution": {
                    "within_1d": 2,
                    "within_7d": 1,
                    "within_30d": 0,
                    "over_30d": 0,
                    "never_login": 0,
                },
            },
        ]
        with patch.object(admin_routes, "_get_user_ops_metrics", side_effect=metrics_side_effect) as mock_metrics, patch.object(
            admin_routes, "_get_user_retention_rows", return_value=[]
        ), patch.object(admin_routes, "_recent_admin_audits", return_value=[]):
            first = self.client.get("/api/admin/overview", headers=header)
            second = self.client.get("/api/admin/overview", headers=header)
            forced = self.client.get("/api/admin/overview?force=1", headers=header)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(forced.status_code, 200)
        self.assertEqual((first.get_json() or {}).get("dashboard", {}).get("total_users"), 11)
        self.assertEqual((second.get_json() or {}).get("dashboard", {}).get("total_users"), 11)
        self.assertEqual((forced.get_json() or {}).get("dashboard", {}).get("total_users"), 22)
        self.assertEqual(mock_metrics.call_count, 2)

    def test_admin_disable_enable_user_writes_audit(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_target", "target_user", is_admin=0, status="active")

        disable_resp = self.client.post(
            "/api/admin/users/disable",
            json={"user_id": "u_target"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(disable_resp.status_code, 200)
        self.assertEqual(disable_resp.get_json().get("new_status"), "disabled")

        row = self._latest_audit()
        self.assertIsNotNone(row)
        self.assertEqual(row["admin_user_id"], "u_admin")
        self.assertEqual(row["action"], "admin.users.disable")
        self.assertEqual(row["result"], "success")
        self.assertEqual(row["status_code"], 200)

        enable_resp = self.client.post(
            "/api/admin/users/enable",
            json={"user_id": "u_target"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(enable_resp.status_code, 200)
        self.assertEqual(enable_resp.get_json().get("new_status"), "active")

        row = self._latest_audit()
        self.assertIsNotNone(row)
        self.assertEqual(row["action"], "admin.users.enable")

    def test_admin_users_support_include_local_and_amount_fields(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_target", "target_user", is_admin=0, status="active")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-02-28", 12345, 6789, 1000, 500, 200, 300, 20, "u_target"),
        )
        cursor.execute(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-02-28", 888, 777, 0, 0, 0, 0, 0, ""),
        )
        conn.commit()
        conn.close()

        resp = self.client.get(
            "/api/admin/users?q=target&include_local=0",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        items = payload.get("items") or []
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].get("id"), "u_target")
        self.assertAlmostEqual(float(items[0].get("total_asset_cny") or 0), 12345.0, places=3)
        self.assertAlmostEqual(float(items[0].get("total_invest_cny") or 0), 6789.0, places=3)
        self.assertIn("last_login_region", items[0])
        self.assertEqual(items[0].get("last_login_region"), "未知")
        self.assertIn("last_active_region", items[0])
        self.assertEqual(items[0].get("last_active_region"), "未知")
        self.assertNotIn("__local__", {str(i.get("id")) for i in items})

    def test_admin_users_region_display_is_normalized(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_target", "target_user", is_admin=0, status="active")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login_region = ? WHERE id = ?",
            ("广东省-深圳市", "u_target"),
        )
        conn.commit()
        conn.close()

        resp = self.client.get(
            "/api/admin/users?q=target&include_local=0",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        items = (resp.get_json() or {}).get("items") or []
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].get("last_login_region"), "广东-深圳")
        self.assertEqual(items[0].get("last_active_region"), "广东-深圳")

    def test_admin_users_support_sort_by_total_asset_desc_with_pagination(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_t1", "target_1", is_admin=0, status="active")
        _seed_user("u_t2", "target_2", is_admin=0, status="active")
        _seed_user("u_t3", "target_3", is_admin=0, status="active")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("2026-02-28", 100.0, 90.0, 0, 0, 0, 0, 0, "u_t1"),
                ("2026-02-28", 300.0, 290.0, 0, 0, 0, 0, 0, "u_t2"),
                ("2026-02-28", 200.0, 190.0, 0, 0, 0, 0, 0, "u_t3"),
            ],
        )
        conn.commit()
        conn.close()

        resp_page1 = self.client.get(
            "/api/admin/users?q=target&include_local=0&sort_by=total_asset_cny&sort_dir=desc&limit=2&offset=0",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp_page1.status_code, 200)
        payload_page1 = resp_page1.get_json() or {}
        items_page1 = payload_page1.get("items") or []
        self.assertEqual(payload_page1.get("total"), 3)
        self.assertEqual(len(items_page1), 2)
        self.assertEqual([str(i.get("id")) for i in items_page1], ["u_t2", "u_t3"])

        resp_page2 = self.client.get(
            "/api/admin/users?q=target&include_local=0&sort_by=total_asset_cny&sort_dir=desc&limit=2&offset=2",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp_page2.status_code, 200)
        payload_page2 = resp_page2.get_json() or {}
        items_page2 = payload_page2.get("items") or []
        self.assertEqual(payload_page2.get("total"), 3)
        self.assertEqual([str(i.get("id")) for i in items_page2], ["u_t1"])

    def test_admin_users_support_sort_by_created_at_desc(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_t1", "target_1", is_admin=0, status="active")
        _seed_user("u_t2", "target_2", is_admin=0, status="active")
        _seed_user("u_t3", "target_3", is_admin=0, status="active")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET created_at = ? WHERE id = ?", ("2026-02-01 10:00:00", "u_t1"))
        cursor.execute("UPDATE users SET created_at = ? WHERE id = ?", ("2026-02-03 10:00:00", "u_t2"))
        cursor.execute("UPDATE users SET created_at = ? WHERE id = ?", ("2026-02-02 10:00:00", "u_t3"))
        conn.commit()
        conn.close()

        resp = self.client.get(
            "/api/admin/users?q=target&include_local=0&sort_by=created_at&sort_dir=desc&limit=10&offset=0",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        items = (resp.get_json() or {}).get("items") or []
        self.assertEqual([str(i.get("id")) for i in items], ["u_t2", "u_t3", "u_t1"])

    def test_admin_users_support_sort_by_last_active_at_desc_with_fallback(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_t1", "target_1", is_admin=0, status="active")
        _seed_user("u_t2", "target_2", is_admin=0, status="active")
        _seed_user("u_t3", "target_3", is_admin=0, status="active")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET created_at = ?, last_login = ?, last_active_at = NULL WHERE id = ?",
            ("2026-02-10 10:00:00", "2026-02-20 10:00:00", "u_t1"),
        )
        cursor.execute(
            "UPDATE users SET created_at = ?, last_login = ?, last_active_at = ? WHERE id = ?",
            ("2026-02-09 10:00:00", "2026-02-19 10:00:00", "2026-02-21 10:00:00", "u_t2"),
        )
        cursor.execute(
            "UPDATE users SET created_at = ?, last_login = NULL, last_active_at = NULL WHERE id = ?",
            ("2026-02-22 10:00:00", "u_t3"),
        )
        conn.commit()
        conn.close()

        resp = self.client.get(
            "/api/admin/users?q=target&include_local=0&sort_by=last_active_at&sort_dir=desc&limit=10&offset=0",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        items = (resp.get_json() or {}).get("items") or []
        self.assertEqual([str(i.get("id")) for i in items], ["u_t3", "u_t2", "u_t1"])

    def test_admin_users_invalid_sort_params_return_400(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_t1", "target_1", is_admin=0, status="active")

        bad_sort_by = self.client.get(
            "/api/admin/users?include_local=0&sort_by=unknown",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(bad_sort_by.status_code, 400)
        self.assertEqual((bad_sort_by.get_json() or {}).get("error"), "Invalid sort_by")

        bad_sort_dir = self.client.get(
            "/api/admin/users?include_local=0&sort_dir=down",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(bad_sort_dir.status_code, 400)
        self.assertEqual((bad_sort_dir.get_json() or {}).get("error"), "Invalid sort_dir")

    def test_admin_user_portfolio_endpoint_returns_holdings(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_target", "target_user", is_admin=0, status="active")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("gb_tsla", "特斯拉", 3, 220.5, "USD", 0, "us", "u_target"),
        )
        conn.commit()
        conn.close()

        resp = self.client.get(
            "/api/admin/users/u_target/portfolio",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        items = payload.get("items") or []
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.get("code"), "gb_tsla")
        self.assertEqual(item.get("name"), "特斯拉")
        self.assertAlmostEqual(float(item.get("qty") or 0), 3.0, places=3)
        self.assertAlmostEqual(float(item.get("price") or 0), 220.5, places=3)
        self.assertEqual(item.get("curr"), "USD")

    def test_disabled_user_cannot_login(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user(
            "u_target",
            "target_user",
            is_admin=0,
            status="active",
            password_hash=hash_password("Aa123456"),
        )

        disable_resp = self.client.post(
            "/api/admin/users/status",
            json={"user_id": "u_target", "status": "disabled"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(disable_resp.status_code, 200)

        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "target_user", "password": "Aa123456"},
        )
        self.assertEqual(login_resp.status_code, 403)
        self.assertEqual((login_resp.get_json() or {}).get("error"), "User is disabled")

    def test_admin_config_update_writes_audit(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/config/update",
            json={"key": "API_TIMEOUT", "value": 9},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json().get("status"), "ok")

        conf_resp = self.client.get(
            "/api/admin/config",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(conf_resp.status_code, 200)
        items = conf_resp.get_json().get("items", [])
        timeout_item = [i for i in items if i.get("key") == "API_TIMEOUT"][0]
        self.assertEqual(timeout_item.get("value"), 9)

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.config.update")
        self.assertEqual(row["status_code"], 200)

    def test_admin_cleanup_weekend_writes_audit(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-02-07", 1, 1, 0, 0, 0, 1, 12, "u_admin"),
        )
        conn.commit()
        conn.close()

        resp = self.client.post(
            "/api/admin/data/snapshot/cleanup_weekend",
            json={"user_id": "u_admin"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json().get("status"), "ok")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT day_pnl FROM daily_snapshots WHERE date = ? AND user_id = ?", ("2026-02-07", "u_admin"))
        day_pnl = cursor.fetchone()["day_pnl"]
        conn.close()
        self.assertEqual(day_pnl, 0)

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.data.snapshot.cleanup_weekend")

    def test_admin_cleanup_market_closed_writes_audit(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-02-07", 1, 1, 0, 0, 0, 1, 12, "u_admin"),
        )
        conn.commit()
        conn.close()

        preview_resp = self.client.post(
            "/api/admin/data/snapshot/cleanup_market_closed/preview",
            json={"user_id": "u_admin", "markets": ["a", "hk", "us", "fund"]},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(preview_resp.status_code, 200)
        self.assertGreaterEqual(int(preview_resp.get_json().get("affected", 0)), 1)

        resp = self.client.post(
            "/api/admin/data/snapshot/cleanup_market_closed",
            json={"user_id": "u_admin", "markets": ["a", "hk", "us", "fund"]},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json().get("status"), "ok")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT day_pnl FROM daily_snapshots WHERE date = ? AND user_id = ?", ("2026-02-07", "u_admin"))
        day_pnl = cursor.fetchone()["day_pnl"]
        conn.close()
        self.assertEqual(day_pnl, 0)

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.data.snapshot.cleanup_market_closed")

    @patch.object(admin_routes, "take_snapshot", return_value=True)
    def test_admin_snapshot_trigger_writes_audit(self, _mock_take_snapshot):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/data/snapshot/trigger",
            json={},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json().get("status"), "ok")

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.data.snapshot.trigger")
        self.assertEqual(row["result"], "success")
        self.assertEqual(row["status_code"], 200)

    @patch.object(admin_routes.system_manager, "check_api_status", return_value={"price": {"ok": True}})
    def test_admin_smoke_test_writes_audit(self, _mock_check):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/apis/smoke_test",
            json={},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(resp.get_json().get("status"), {"ok", "degraded"})

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.apis.smoke_test")
        self.assertEqual(row["status_code"], 200)

    @patch.object(
        admin_routes,
        "_run_market_provider_test",
        return_value={
            "provider_key": "sina_quote",
            "provider_label": "新浪行情",
            "status": "ok",
            "tested_at_utc": "2026-02-28T10:00:00+00:00",
            "items": [{"name": "腾讯", "code": "hk00700", "ok": True, "latency_ms": 20}],
        },
    )
    def test_admin_provider_test_market_success(self, _mock_run):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/apis/provider_test",
            json={"provider_key": "sina_quote"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body.get("provider_key"), "sina_quote")
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual((body.get("items") or [{}])[0].get("code"), "hk00700")

    @patch.object(
        admin_routes,
        "_run_forex_provider_test",
        return_value={
            "provider_key": "forex_rate",
            "provider_label": "汇率",
            "status": "ok",
            "tested_at_utc": "2026-02-28T10:00:00+00:00",
            "items": [{"name": "USD/CNY", "code": "USD", "ok": True, "rate": 7.2, "latency_ms": 15}],
        },
    )
    def test_admin_provider_test_forex_success(self, _mock_run):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/apis/provider_test",
            json={"provider_key": "forex_rate"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body.get("provider_key"), "forex_rate")
        self.assertEqual((body.get("items") or [{}])[0].get("name"), "USD/CNY")

    def test_admin_provider_test_invalid_provider_returns_400(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/apis/provider_test",
            json={"provider_key": "unknown"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json().get("error"), "Invalid provider_key")

    def test_admin_policy_update_writes_audit(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/apis/policies/update",
            json={"scope_key": "api.news", "enabled": False, "note": "test"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("policy", {}).get("scope_key"), "api.news")

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.apis.policies.update")
        self.assertEqual(row["status_code"], 200)


if __name__ == "__main__":
    unittest.main()

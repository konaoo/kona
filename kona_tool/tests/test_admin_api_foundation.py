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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_admin.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402
import admin_routes  # noqa: E402


def _seed_user(user_id: str, username: str, is_admin: int = 0, status: str = "active") -> None:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
        VALUES (?, ?, ?, 0, ?, ?)
        """,
        (user_id, username, "scrypt$16384$8$1$U0FMVA==$SEFTSA==", is_admin, status),
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
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM admin_audit_logs")
        cursor.execute("DELETE FROM daily_snapshots")
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

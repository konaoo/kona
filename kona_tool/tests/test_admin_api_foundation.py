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
        cursor.execute("DELETE FROM user_daily_activity")
        cursor.execute("DELETE FROM daily_snapshots")
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM runtime_configs")
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
        self.assertEqual(resp.get_json().get("error"), "当前账号没有后台权限")

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
        today_str = today.isoformat()
        cohort_str = cohort_day.isoformat()
        day1_str = (cohort_day + timedelta(days=1)).isoformat()
        day3_str = (cohort_day + timedelta(days=3)).isoformat()
        day7_str = (cohort_day + timedelta(days=7)).isoformat()

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET created_at = ?, last_login = ?, last_active_at = ?
            WHERE id = ?
            """,
            (f"{cohort_str} 09:00:00", f"{day7_str} 09:00:00", f"{day7_str} 09:00:00", "u_u1"),
        )
        cursor.execute(
            """
            UPDATE users
            SET created_at = ?, last_login = ?, last_active_at = ?
            WHERE id = ?
            """,
            (f"{cohort_str} 10:00:00", f"{day3_str} 10:00:00", f"{day3_str} 10:00:00", "u_u2"),
        )
        cursor.execute(
            """
            UPDATE users
            SET created_at = ?, last_login = ?, last_active_at = ?
            WHERE id = ?
            """,
            (f"{today_str} 11:00:00", f"{today_str} 12:00:00", f"{today_str} 12:00:00", "u_admin"),
        )
        cursor.executemany(
            """
            INSERT INTO user_daily_activity (user_id, activity_date, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, activity_date) DO UPDATE SET last_seen_at = excluded.last_seen_at
            """,
            [
                ("u_u1", cohort_str, f"{cohort_str} 09:00:00", f"{cohort_str} 09:00:00"),
                ("u_u1", day1_str, f"{day1_str} 09:00:00", f"{day1_str} 09:00:00"),
                ("u_u1", day7_str, f"{day7_str} 09:00:00", f"{day7_str} 09:00:00"),
                ("u_u2", cohort_str, f"{cohort_str} 10:00:00", f"{cohort_str} 10:00:00"),
                ("u_u2", day3_str, f"{day3_str} 10:00:00", f"{day3_str} 10:00:00"),
                ("u_admin", today_str, f"{today_str} 12:00:00", f"{today_str} 12:00:00"),
            ],
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
        self.assertEqual(int(dashboard.get("active_users_today") or 0), 1)

        rows = data.get("retention_rows") or []
        self.assertTrue(rows)
        cohort_row = next((r for r in rows if (r.get("date") or "") == cohort_str), None)
        self.assertIsNotNone(cohort_row)
        self.assertEqual(int(cohort_row.get("new_users") or 0), 2)
        self.assertEqual(int(cohort_row.get("active_users") or 0), 2)
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

    def test_admin_price_probe_requires_code(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/apis/price_probe",
            json={},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual((resp.get_json() or {}).get("error"), "Missing code")

    def test_admin_price_probe_returns_probe_payload(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        fake_payload = {
            "code": "00700",
            "asset_type": "hk",
            "asset_type_label": "港股",
            "current": {"price": 519.0, "yclose": 502.0, "amt": 17.0, "chg": 3.39, "source_hint": "腾讯财经"},
            "sources": [
                {"source_key": "tencent_quote", "source_label": "腾讯财经", "price": 519.0, "ok": True, "delta_pct": 0.0},
                {"source_key": "sina_quote", "source_label": "新浪财经", "price": 518.9, "ok": True, "delta_pct": 0.0193},
            ],
            "diagnosis": {"status": "ok", "summary": "主价与各源基本一致。"},
        }
        with patch.object(admin_routes, "_build_price_probe_payload", return_value=fake_payload) as mock_probe:
            resp = self.client.post(
                "/api/admin/apis/price_probe",
                json={"code": "00700"},
                headers=_auth_headers("u_admin", "admin_user"),
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), fake_payload)
        mock_probe.assert_called_once_with("00700")

    def test_market_provider_test_excludes_fund_for_stock_only_sources(self):
        payload = admin_routes._run_market_provider_test("sina_quote")
        codes = {str(item.get("code")) for item in (payload.get("items") or [])}
        self.assertNotIn("f_110017", codes)

    def test_market_provider_test_keeps_fund_for_eastmoney_quote(self):
        payload = admin_routes._run_market_provider_test("eastmoney_quote")
        items = payload.get("items") or []
        codes = {str(item.get("code")) for item in items}
        self.assertIn("f_110017", codes)
        fund_item = next(item for item in items if str(item.get("code")) == "f_110017")
        self.assertEqual(str(fund_item.get("status")), "ok")
        self.assertIn(str(payload.get("status")), {"ok", "degraded"})

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
        cursor.execute(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-02-28", 1.0, 1.0, 0, 0, 0, 0, 0, "u_target"),
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

    def test_admin_users_status_all_only_returns_total_asset_gt_zero(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_t1", "target_1", is_admin=0, status="active")
        _seed_user("u_t2", "target_2", is_admin=0, status="active")

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
                ("2026-02-28", 0.0, 0.0, 0, 0, 0, 0, 0, "u_t2"),
            ],
        )
        conn.commit()
        conn.close()

        resp = self.client.get(
            "/api/admin/users?include_local=0&status=all&sort_by=total_asset_cny&sort_dir=desc",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        items = (resp.get_json() or {}).get("items") or []
        ids = [str(i.get("id")) for i in items]
        self.assertIn("u_t1", ids)
        self.assertNotIn("u_t2", ids)

    def test_admin_users_support_sort_by_total_invest_desc(self):
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
                ("2026-02-28", 10.0, 200.0, 0, 0, 0, 0, 0, "u_t1"),
                ("2026-02-28", 10.0, 300.0, 0, 0, 0, 0, 0, "u_t2"),
                ("2026-02-28", 10.0, 100.0, 0, 0, 0, 0, 0, "u_t3"),
            ],
        )
        conn.commit()
        conn.close()

        resp = self.client.get(
            "/api/admin/users?q=target&include_local=0&sort_by=total_invest_cny&sort_dir=desc&limit=10&offset=0",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        items = (resp.get_json() or {}).get("items") or []
        self.assertEqual([str(i.get("id")) for i in items], ["u_t2", "u_t1", "u_t3"])

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
        cursor.executemany(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("2026-02-28", 10.0, 9.0, 0, 0, 0, 0, 0, "u_t1"),
                ("2026-02-28", 10.0, 9.0, 0, 0, 0, 0, 0, "u_t2"),
                ("2026-02-28", 10.0, 9.0, 0, 0, 0, 0, 0, "u_t3"),
            ],
        )
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
        cursor.executemany(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("2026-02-28", 10.0, 9.0, 0, 0, 0, 0, 0, "u_t1"),
                ("2026-02-28", 10.0, 9.0, 0, 0, 0, 0, 0, "u_t2"),
                ("2026-02-28", 10.0, 9.0, 0, 0, 0, 0, 0, "u_t3"),
            ],
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

    @patch.object(admin_routes, "batch_get_prices", return_value={"gb_tsla": (240.5, 230.0, 0, 0)})
    @patch.object(admin_routes, "get_forex_rates", return_value={"USD": 7.2, "HKD": 0.91, "CNY": 1.0})
    def test_admin_user_portfolio_endpoint_returns_holdings(self, _mock_rates, _mock_prices):
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
        cursor.execute(
            "INSERT INTO cash_assets (name, amount, curr, user_id) VALUES (?, ?, ?, ?)",
            ("现金账户", 100.0, "USD", "u_target"),
        )
        cursor.execute(
            "INSERT INTO other_assets (name, amount, curr, user_id) VALUES (?, ?, ?, ?)",
            ("其他资产", 50.0, "CNY", "u_target"),
        )
        cursor.execute(
            "INSERT INTO liabilities (name, amount, curr, user_id) VALUES (?, ?, ?, ?)",
            ("信用卡", 10.0, "USD", "u_target"),
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
        self.assertIn("pnl_cny", item)
        self.assertIn("pnl_rate", item)
        self.assertEqual(item.get("type_label"), "美股")
        self.assertIn("summary", payload)
        self.assertAlmostEqual(float(payload.get("summary", {}).get("cash_cny") or 0), 720.0, places=2)
        self.assertAlmostEqual(float(payload.get("summary", {}).get("other_cny") or 0), 50.0, places=2)
        self.assertAlmostEqual(float(payload.get("summary", {}).get("liability_cny") or 0), 72.0, places=2)
        self.assertIn("as_of", payload.get("summary", {}))
        self.assertIn("cache", payload)
        self.assertIn("cached_at", payload.get("cache", {}))
        self.assertIn("expires_at", payload.get("cache", {}))

    @patch.object(admin_routes, "batch_get_prices", return_value={"gb_neg": (0.0, 0.0, 0, 0)})
    @patch.object(admin_routes, "get_forex_rates", return_value={"USD": 7.0, "CNY": 1.0})
    def test_admin_user_portfolio_negative_cost_uses_abs_rate_denominator(self, _mock_rates, _mock_prices):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        _seed_user("u_target", "target_user", is_admin=0, status="active")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("gb_neg", "负成本样本", 2.0, -5.0, "USD", 0.0, "us", "u_target"),
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
        self.assertAlmostEqual(float(item.get("latest_price") or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(item.get("pnl_rate") or 0.0), 100.0, places=2)

    def test_admin_audit_endpoints_are_removed(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")

        logs_resp = self.client.get(
            "/api/admin/audit/logs",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(logs_resp.status_code, 404)

        export_resp = self.client.get(
            "/api/admin/audit/export",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(export_resp.status_code, 404)

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
        self.assertEqual((login_resp.get_json() or {}).get("error"), "账号已停用，请联系管理员")

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

    def test_admin_ops_invite_acquire_requires_auth_and_admin(self):
        no_auth = self.client.get("/api/admin/ops/invite_acquire")
        self.assertEqual(no_auth.status_code, 401)

        _seed_user("u_user", "normal_user", is_admin=0, status="active")
        non_admin = self.client.get(
            "/api/admin/ops/invite_acquire",
            headers=_auth_headers("u_user", "normal_user"),
        )
        self.assertEqual(non_admin.status_code, 403)
        self.assertEqual((non_admin.get_json() or {}).get("error"), "当前账号没有后台权限")

    def test_admin_ops_invite_acquire_update_persists_and_writes_audit(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        payload = {
            "text": "小红书被限制了，进微信群领邀请码。",
            "image_url": "https://example.com/invite_qr.png",
        }
        update_resp = self.client.post(
            "/api/admin/ops/invite_acquire/update",
            json=payload,
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(update_resp.status_code, 200)
        body = update_resp.get_json() or {}
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("text"), payload["text"])
        self.assertEqual(body.get("image_url"), payload["image_url"])

        get_resp = self.client.get(
            "/api/admin/ops/invite_acquire",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(get_resp.status_code, 200)
        current = get_resp.get_json() or {}
        self.assertEqual(current.get("text"), payload["text"])
        self.assertEqual(current.get("image_url"), payload["image_url"])

        self.assertEqual(
            app_module.db.get_runtime_config("ops.invite_acquire.text"),
            payload["text"],
        )
        self.assertEqual(
            app_module.db.get_runtime_config("ops.invite_acquire.image_url"),
            payload["image_url"],
        )

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.ops.invite_acquire.update")
        self.assertEqual(row["status_code"], 200)

    def test_admin_ops_invite_acquire_update_rejects_invalid_image_url(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/ops/invite_acquire/update",
            json={
                "text": "文案正常",
                "image_url": "ftp://example.com/a.png",
            },
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("image_url", str((resp.get_json() or {}).get("error", "")).lower())

    def test_admin_ops_user_group_requires_auth_and_admin(self):
        no_auth = self.client.get("/api/admin/ops/user_group")
        self.assertEqual(no_auth.status_code, 401)

        _seed_user("u_user", "normal_user", is_admin=0, status="active")
        non_admin = self.client.get(
            "/api/admin/ops/user_group",
            headers=_auth_headers("u_user", "normal_user"),
        )
        self.assertEqual(non_admin.status_code, 403)
        self.assertEqual((non_admin.get_json() or {}).get("error"), "当前账号没有后台权限")

    def test_admin_ops_user_group_update_persists_and_writes_audit(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        payload = {
            "text": "加入咔咔用户群",
            "image_url": "https://example.com/user_group_qr.png",
        }
        update_resp = self.client.post(
            "/api/admin/ops/user_group/update",
            json=payload,
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(update_resp.status_code, 200)
        body = update_resp.get_json() or {}
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("text"), payload["text"])
        self.assertEqual(body.get("image_url"), payload["image_url"])

        get_resp = self.client.get(
            "/api/admin/ops/user_group",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(get_resp.status_code, 200)
        current = get_resp.get_json() or {}
        self.assertEqual(current.get("text"), payload["text"])
        self.assertEqual(current.get("image_url"), payload["image_url"])

        self.assertEqual(
            app_module.db.get_runtime_config("ops.user_group.text"),
            payload["text"],
        )
        self.assertEqual(
            app_module.db.get_runtime_config("ops.user_group.image_url"),
            payload["image_url"],
        )

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.ops.user_group.update")
        self.assertEqual(row["status_code"], 200)

    def test_admin_ops_user_group_update_rejects_invalid_image_url(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/ops/user_group/update",
            json={
                "text": "用户群文案",
                "image_url": "ftp://example.com/a.png",
            },
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("image_url", str((resp.get_json() or {}).get("error", "")).lower())

    def test_admin_ops_app_update_requires_auth_and_admin(self):
        no_auth = self.client.get("/api/admin/ops/app_update")
        self.assertEqual(no_auth.status_code, 401)

        _seed_user("u_user", "normal_user", is_admin=0, status="active")
        non_admin = self.client.get(
            "/api/admin/ops/app_update",
            headers=_auth_headers("u_user", "normal_user"),
        )
        self.assertEqual(non_admin.status_code, 403)
        self.assertEqual((non_admin.get_json() or {}).get("error"), "当前账号没有后台权限")

    def test_admin_ops_app_update_update_persists_and_writes_audit(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        payload = {
            "text": "1. 修复已知问题\n2. 优化启动速度",
            "download_url": "https://example.com/kaka-latest.apk",
        }
        update_resp = self.client.post(
            "/api/admin/ops/app_update/update",
            json=payload,
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(update_resp.status_code, 200)
        body = update_resp.get_json() or {}
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("text"), payload["text"])
        self.assertEqual(body.get("download_url"), payload["download_url"])

        get_resp = self.client.get(
            "/api/admin/ops/app_update",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(get_resp.status_code, 200)
        current = get_resp.get_json() or {}
        self.assertEqual(current.get("text"), payload["text"])
        self.assertEqual(current.get("download_url"), payload["download_url"])

        self.assertEqual(
            app_module.db.get_runtime_config("ops.app_update.text"),
            payload["text"],
        )
        self.assertEqual(
            app_module.db.get_runtime_config("ops.app_update.download_url"),
            payload["download_url"],
        )

        row = self._latest_audit()
        self.assertEqual(row["action"], "admin.ops.app_update.update")
        self.assertEqual(row["status_code"], 200)

    def test_admin_ops_app_update_update_rejects_invalid_download_url(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/ops/app_update/update",
            json={
                "text": "版本更新",
                "download_url": "ftp://example.com/a.apk",
            },
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("download_url", str((resp.get_json() or {}).get("error", "")).lower())

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

    @patch.object(
        admin_routes,
        "_get_latest_provider_test_report",
        return_value={
            "report_slot": "2026-03-08T18",
            "tested_at_utc": "2026-03-08T10:00:00+00:00",
            "summary": {"status": "alert", "label": "新浪行情告警", "alert_keys": ["sina_quote"]},
            "providers": {
                "sina_quote": {
                    "provider_key": "sina_quote",
                    "provider_label": "新浪财经行情",
                    "status": "degraded",
                    "tested_at_utc": "2026-03-08T10:00:00+00:00",
                    "items": [{"name": "工商银行", "code": "sh601398", "ok": False, "latency_ms": 20}],
                }
            },
        },
    )
    def test_admin_provider_tests_latest_returns_snapshot(self, _mock_latest):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.get(
            "/api/admin/apis/provider_tests/latest",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        self.assertEqual((body.get("summary") or {}).get("label"), "新浪行情告警")
        self.assertEqual(((body.get("providers") or {}).get("sina_quote") or {}).get("status"), "degraded")

    @patch.object(
        admin_routes,
        "run_provider_test_report_job",
        return_value={
            "tested_at_utc": "2026-03-08T10:00:00+00:00",
            "summary": {"status": "ok", "label": "正常", "alert_keys": []},
            "providers": {
                "sina_quote": {
                    "provider_key": "sina_quote",
                    "provider_label": "新浪财经行情",
                    "status": "ok",
                    "tested_at_utc": "2026-03-08T10:00:00+00:00",
                    "items": [{"name": "工商银行", "code": "sh601398", "ok": True, "latency_ms": 20}],
                }
            },
        },
    )
    def test_admin_provider_tests_run_returns_batch_payload(self, _mock_run_job):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/apis/provider_tests/run",
            json={},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        self.assertEqual((body.get("summary") or {}).get("label"), "正常")
        self.assertEqual(((body.get("providers") or {}).get("sina_quote") or {}).get("status"), "ok")
        _mock_run_job.assert_called_once()

    @patch.object(
        admin_routes,
        "_load_price_alerts_payload",
        return_value={
            "tested_at_utc": "2026-03-06T08:00:00+00:00",
            "total_assets": 3,
            "alert_count": 1,
            "summary": {"critical": 1, "warning": 0, "info": 0},
            "items": [
                {
                    "code": "f_968048",
                    "name": "摩根基金",
                    "curr": "CNY",
                    "user_count": 2,
                    "usernames": ["kona", "x"],
                    "current_price": 17.85,
                    "baseline_price": 17.96,
                    "baseline_source": "海外基金页",
                    "baseline_source_key": "overseas_1234567",
                    "delta_pct": 0.61,
                    "severity": "critical",
                    "alert_type": "price_mismatch",
                    "reason": "当前主价格与可信基准源偏差过大。",
                    "suggestion": "检查源优先级。",
                    "sources": [],
                }
            ],
        },
    )
    @patch.object(
        admin_routes,
        "_list_price_alert_report_history",
        return_value=[
            {
                "report_date": "2026-03-06",
                "tested_at_utc": "2026-03-06T08:00:00+00:00",
                "total_assets": 3,
                "alert_count": 1,
                "updated_at": "2026-03-06 16:00:00",
                "summary": {"critical": 1, "warning": 0, "info": 0},
            }
        ],
    )
    @patch.object(admin_routes, "_save_price_alert_report_snapshot")
    def test_admin_price_alerts_success(self, _mock_save, _mock_history, _mock_loader):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.get(
            "/api/admin/apis/price_alerts?force=1",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        self.assertEqual(body.get("alert_count"), 1)
        self.assertEqual((body.get("items") or [{}])[0].get("code"), "f_968048")
        self.assertEqual((body.get("history") or [{}])[0].get("report_date"), "2026-03-06")
        self.assertEqual((body.get("cache") or {}).get("state"), "bypass")
        _mock_save.assert_called_once()

    @patch.object(
        admin_routes,
        "_list_price_alert_report_history",
        return_value=[
            {
                "report_date": "2026-03-07",
                "tested_at_utc": "2026-03-07T08:00:00+00:00",
                "total_assets": 12,
                "alert_count": 2,
                "updated_at": "2026-03-07 16:00:00",
                "summary": {"critical": 1, "warning": 1, "info": 0},
            }
        ],
    )
    @patch.object(
        admin_routes,
        "_get_latest_price_alert_report",
        return_value={
            "report_date": "2026-03-07",
            "tested_at_utc": "2026-03-07T08:00:00+00:00",
            "total_assets": 12,
            "alert_count": 2,
            "updated_at": "2026-03-07 16:00:00",
            "summary": {"critical": 1, "warning": 1, "info": 0},
            "items": [{"code": "f_968048", "alert_type": "price_mismatch"}],
        },
    )
    @patch.object(admin_routes, "_load_price_alerts_payload")
    def test_admin_price_alerts_prefers_latest_snapshot_without_force(
        self,
        _mock_loader,
        _mock_latest,
        _mock_history,
    ):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.get(
            "/api/admin/apis/price_alerts",
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        self.assertEqual(body.get("report_date"), "2026-03-07")
        self.assertEqual(body.get("alert_count"), 2)
        self.assertEqual((body.get("items") or [{}])[0].get("code"), "f_968048")
        self.assertEqual((body.get("cache") or {}).get("state"), "snapshot")
        _mock_loader.assert_not_called()

    def test_admin_provider_test_invalid_provider_returns_400(self):
        _seed_user("u_admin", "admin_user", is_admin=1, status="active")
        resp = self.client.post(
            "/api/admin/apis/provider_test",
            json={"provider_key": "unknown"},
            headers=_auth_headers("u_admin", "admin_user"),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json().get("error"), "Invalid provider_key")

    def test_tencent_quote_code_for_us_symbols_has_no_dot(self):
        self.assertEqual(admin_routes._to_tencent_quote_code("gb_aapl"), "usAAPL")
        self.assertEqual(admin_routes._to_tencent_quote_code("gb_tsla"), "usTSLA")
        self.assertEqual(admin_routes._to_tencent_quote_code("aapl"), "usAAPL")

    @patch.object(admin_routes, "get_forex_rates", return_value={"USD": 7.12, "HKD": 0.91, "CNY": 1.0})
    def test_forex_provider_returns_two_pairs_only(self, _mock_rates):
        payload = admin_routes._run_forex_provider_test()
        self.assertEqual(payload.get("provider_key"), "forex_rate")
        items = payload.get("items") or []
        self.assertEqual(len(items), 2)
        self.assertEqual([item.get("code") for item in items], ["USD/CNY", "HKD/CNY"])
        self.assertNotIn("CNY/CNY", [item.get("code") for item in items])

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

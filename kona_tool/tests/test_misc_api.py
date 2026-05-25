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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class MiscApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cash_assets")
        cursor.execute("DELETE FROM other_assets")
        cursor.execute("DELETE FROM liabilities")
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM daily_snapshots")
        cursor.execute("DELETE FROM runtime_configs")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_health(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'ok')

    def test_history_respects_user_build_start_at(self):
        created = app_module.db.create_user(
            username="history_user",
            password_hash=app_module.hash_password("Abcd1234"),
            user_id="u_history",
        )
        self.assertEqual(created.get("id"), "u_history")
        self.assertTrue(app_module.db.set_user_build_start_at("u_history", "2026-02-12"))

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-02-04', 100, 80, 20, 0, 0, 10, 1, 'u_history')
            """
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-02-12', 200, 160, 40, 0, 0, 20, 2, 'u_history')
            """
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-02-13', 220, 170, 50, 0, 0, 30, 3, 'u_history')
            """
        )
        conn.commit()
        conn.close()

        access_token = app_module._issue_auth_tokens("u_history", "history_user")["access_token"]
        resp = self.client.get(
            "/api/history?days=5000",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or []
        self.assertEqual([item.get("date") for item in payload], ["2026-02-12", "2026-02-13"])

    def test_history_default_limit_keeps_more_than_one_year_for_old_clients(self):
        created = app_module.db.create_user(
            username="history_old_client",
            password_hash=app_module.hash_password("Abcd1234"),
            user_id="u_history_old_client",
        )
        self.assertEqual(created.get("id"), "u_history_old_client")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        for day in range(370):
            cursor.execute(
                """
                INSERT OR REPLACE INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES (date('2025-01-01', ?), ?, 0, 0, 0, 0, 0, 0, 'u_history_old_client')
                """,
                (f"+{day} day", 1000 + day),
            )
        conn.commit()
        conn.close()

        access_token = app_module._issue_auth_tokens(
            "u_history_old_client",
            "history_old_client",
        )["access_token"]
        resp = self.client.get(
            "/api/history",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or []
        self.assertEqual(len(payload), 370)

    def test_asset_trends_endpoint_normalizes_items_and_points(self):
        mocked_trends = [{"code": "sh600000", "points": [1, 2, 3]}]
        with patch.object(app_module, "batch_get_asset_trends", return_value=mocked_trends) as mocked:
            resp = self.client.post(
                "/api/asset/trends",
                json={
                    "items": [
                        {"code": "sh600000", "name": "浦发银行", "market": "a"},
                        "gb_aapl",
                    ],
                    "points": 99,
                },
            )

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertEqual(payload.get("items"), mocked_trends)
        self.assertEqual(payload.get("points"), 60)
        self.assertEqual(payload.get("label"), "近期估值趋势")
        mocked.assert_called_once_with(
            [
                {"code": "sh600000", "name": "浦发银行", "market": "a"},
                {"code": "gb_aapl", "name": "", "market": ""},
            ],
            points=99,
        )


if __name__ == '__main__':
    unittest.main()

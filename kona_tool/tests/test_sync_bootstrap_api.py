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


class SyncBootstrapApiTests(unittest.TestCase):
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
        conn.commit()
        conn.close()

    def test_sync_bootstrap_returns_changed_domains_and_versions(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cash_assets (name, amount, curr, user_id)
            VALUES ('测试现金', 1000, 'CNY', '')
            """
        )
        conn.commit()
        conn.close()

        fixed_rates = {'USD': 7.0, 'HKD': 0.9, 'CNY': 1.0}
        with patch.object(app_module, 'get_forex_rates', return_value=fixed_rates):
            first = self.client.post(
                '/api/sync/bootstrap',
                json={
                    'include': ['cash_assets', 'rates'],
                    'client_versions': {},
                },
            )
            self.assertEqual(first.status_code, 200)
            first_payload = first.get_json() or {}
            self.assertEqual(set(first_payload.get('changed') or []), {'cash_assets', 'rates'})
            self.assertIn('cash_assets', first_payload.get('data') or {})
            self.assertIn('rates', first_payload.get('data') or {})
            self.assertIn('quote_policy', first_payload)
            self.assertIn('market_status', first_payload)
            self.assertIn('market_statuses', first_payload)
            self.assertGreater(int(first.headers.get('X-Trace-Stage-Count', '0')), 0)
            detailed = first_payload.get('market_statuses') or {}
            self.assertIn('hk', detailed)
            self.assertIn('trading_day', detailed.get('hk') or {})
            versions = first_payload.get('versions') or {}
            self.assertTrue(str(versions.get('cash_assets', '')).strip())
            self.assertTrue(str(versions.get('rates', '')).strip())

            second = self.client.post(
                '/api/sync/bootstrap',
                json={
                    'include': ['cash_assets', 'rates'],
                    'client_versions': {
                        'cash_assets': versions.get('cash_assets'),
                        'rates': versions.get('rates'),
                    },
                },
            )
            self.assertEqual(second.status_code, 200)
            second_payload = second.get_json() or {}
            self.assertEqual(second_payload.get('changed'), [])
            self.assertEqual(second_payload.get('data'), {})

    def test_sync_bootstrap_history_keeps_more_than_one_year(self):
        user_id = "u_sync_history"
        created = app_module.db.create_user(
            username="sync_history_user",
            password_hash=app_module.hash_password("Abcd1234"),
            user_id=user_id,
        )
        self.assertEqual(created.get("id"), user_id)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        for idx in range(420):
            cursor.execute(
                """
                INSERT INTO daily_snapshots (
                    date, total_asset, total_invest, total_cash, total_other,
                    total_liability, total_pnl, day_pnl, user_id
                )
                VALUES (date('2025-01-01', ?), ?, 0, 0, 0, 0, 0, 0, ?)
                """,
                (f"+{idx} day", 1000 + idx, user_id),
            )
        conn.commit()
        conn.close()

        access_token = app_module._issue_auth_tokens(user_id, "sync_history_user")["access_token"]
        resp = self.client.post(
            "/api/sync/bootstrap",
            json={
                "include": ["history"],
                "client_versions": {},
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        history = ((payload.get("data") or {}).get("history") or [])
        self.assertGreater(len(history), 365)


if __name__ == '__main__':
    unittest.main()

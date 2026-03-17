import os
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class AssetAccountApiTests(unittest.TestCase):
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

    def test_transactions_endpoint_respects_limit(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
            VALUES ('2026-03-14 10:00:00', 'sh600000', '浦发银行', 'buy', 10, 1, 10, 0, '')
            """
        )
        cursor.execute(
            """
            INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
            VALUES ('2026-03-14 11:00:00', 'sh600001', '上证测试', 'sell', 12, 2, 24, 4, '')
            """
        )
        conn.commit()
        conn.close()

        resp = self.client.get('/api/transactions?limit=1')
        self.assertEqual(resp.status_code, 200)
        items = resp.get_json() or []
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].get('code'), 'sh600001')

    def test_cash_asset_add_update_delete(self):
        add_resp = self.client.post('/api/cash_assets/add', json={
            'name': '测试现金',
            'amount': 1234.56,
            'curr': 'CNY',
        })
        self.assertEqual(add_resp.status_code, 200)
        self.assertEqual(add_resp.get_json().get('status'), 'ok')
        self.assertGreater(int(add_resp.headers.get('X-Trace-Stage-Count') or 0), 0)

        list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        self.assertTrue(len(items) > 0)
        asset_id = items[-1]['id']

        update_resp = self.client.post('/api/cash_assets/update', json={
            'id': asset_id,
            'name': '测试现金-更新',
            'amount': 2345.67,
            'curr': 'CNY',
        })
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.get_json().get('status'), 'ok')
        self.assertGreater(int(update_resp.headers.get('X-Trace-Stage-Count') or 0), 0)

        delete_resp = self.client.post('/api/cash_assets/delete', json={'id': asset_id})
        self.assertEqual(delete_resp.status_code, 200)
        self.assertEqual(delete_resp.get_json().get('status'), 'ok')
        self.assertGreater(int(delete_resp.headers.get('X-Trace-Stage-Count') or 0), 0)

    def test_cash_asset_amount_allows_zero(self):
        add_resp = self.client.post('/api/cash_assets/add', json={
            'name': '零余额现金',
            'amount': 0,
            'curr': 'CNY',
        })
        self.assertEqual(add_resp.status_code, 200)
        self.assertEqual((add_resp.get_json() or {}).get('status'), 'ok')

        list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('name') == '零余额现金'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('amount', 0)), 0.0)

        update_resp = self.client.post('/api/cash_assets/update', json={
            'id': target['id'],
            'name': '零余额现金-更新',
            'amount': 0,
            'curr': 'CNY',
        })
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual((update_resp.get_json() or {}).get('status'), 'ok')

    def test_cash_asset_negative_amount_rejected(self):
        add_resp = self.client.post('/api/cash_assets/add', json={
            'name': '负余额现金',
            'amount': -1,
            'curr': 'CNY',
        })
        self.assertEqual(add_resp.status_code, 400)
        self.assertEqual((add_resp.get_json() or {}).get('code'), 'INVALID_AMOUNT')

    def test_other_asset_missing_required_fields_has_code(self):
        resp = self.client.post('/api/other_assets/add', json={'name': '缺少金额'})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get('error'), 'Missing required fields')
        self.assertEqual(data.get('code'), 'MISSING_REQUIRED_FIELDS')

    def test_liability_invalid_amount_has_code(self):
        resp = self.client.post('/api/liabilities/add', json={
            'name': '测试负债',
            'amount': 0,
            'curr': 'CNY',
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get('error'), 'Invalid amount')
        self.assertEqual(data.get('code'), 'INVALID_AMOUNT')


if __name__ == '__main__':
    unittest.main()

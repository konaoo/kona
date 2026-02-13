import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

# Ensure kona_tool is on sys.path so app.py can import config/core
ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

# Use a temporary database to avoid local schema conflicts
_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class ApiBaselineTests(unittest.TestCase):
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
        conn.commit()
        conn.close()

    def test_health(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'ok')

    def test_price_missing_code(self):
        resp = self.client.get('/api/price')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json().get('error'), 'Missing code')

    def test_prices_batch_missing_codes(self):
        resp = self.client.post('/api/prices/batch', json={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json().get('error'), 'Missing codes')

    def test_rates_mocked(self):
        with patch.object(app_module, 'get_forex_rates', return_value={'USD': 7.0}):
            resp = self.client.get('/api/rates')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json().get('USD'), 7.0)

    def test_price_mocked(self):
        with patch.object(app_module, 'get_price', return_value=(10, 9, 0, 0)):
            resp = self.client.get('/api/price?code=sh600000')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual(data.get('price'), 10)

    def test_prices_batch_mocked(self):
        with patch.object(app_module, 'batch_get_prices', return_value={'sh600000': (10, 9, 0, 0)}):
            resp = self.client.post('/api/prices/batch', json={'codes': ['sh600000']})
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn('sh600000', data)
            self.assertEqual(data['sh600000']['price'], 10)

    def test_cash_asset_add_update_delete(self):
        add_resp = self.client.post('/api/cash_assets/add', json={
            'name': '测试现金',
            'amount': 1234.56,
            'curr': 'CNY',
        })
        self.assertEqual(add_resp.status_code, 200)
        self.assertEqual(add_resp.get_json().get('status'), 'ok')

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

        delete_resp = self.client.post('/api/cash_assets/delete', json={'id': asset_id})
        self.assertEqual(delete_resp.status_code, 200)
        self.assertEqual(delete_resp.get_json().get('status'), 'ok')

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

    def test_buy_idempotent_request_id_prevents_duplicate_qty(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600000',
            'name': '浦发银行',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        request_id = 'req-buy-dedup-1'
        buy_first = self.client.post('/api/portfolio/buy', json={
            'code': 'sh600000',
            'price': 12.0,
            'qty': 5.0,
            'request_id': request_id,
        })
        self.assertEqual(buy_first.status_code, 200)
        self.assertEqual(buy_first.get_json().get('status'), 'ok')

        buy_second = self.client.post('/api/portfolio/buy', json={
            'code': 'sh600000',
            'price': 12.0,
            'qty': 5.0,
            'request_id': request_id,
        })
        self.assertEqual(buy_second.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600000'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target['qty']), 15.0)

    def test_portfolio_add_us_code_forces_usd_currency(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'goog',
            'name': 'Google',
            'price': 100.0,
            'qty': 1.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_resp.status_code, 200)
        self.assertEqual(add_resp.get_json().get('status'), 'ok')

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'gb_goog'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('curr'), 'USD')

    def test_delete_corrective_removes_transactions_and_future_snapshots(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600001',
            'name': '测试纠错',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        buy_resp = self.client.post('/api/portfolio/buy', json={
            'code': 'sh600001',
            'price': 11.0,
            'qty': 2.0,
        })
        self.assertEqual(buy_resp.status_code, 200)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        d1 = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        d2 = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1, 1, 0, 0, 0, 0, '')
            """,
            (d1,),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1, 1, 0, 0, 0, 0, '')
            """,
            (d2,),
        )
        conn.commit()
        conn.close()

        delete_resp = self.client.post('/api/portfolio/delete_corrective', json={
            'code': 'sh600001',
            'request_id': 'req-corrective-1',
        })
        self.assertEqual(delete_resp.status_code, 200)
        payload = delete_resp.get_json()
        self.assertEqual(payload.get('status'), 'ok')
        self.assertEqual(payload.get('code'), 'CORRECTIVE_DELETE_DONE')
        self.assertIn('deleted', payload)

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600001' for item in portfolio_items))

        tx_resp = self.client.get('/api/transactions')
        self.assertEqual(tx_resp.status_code, 200)
        tx_items = tx_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600001' for item in tx_items))

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(1) AS cnt FROM daily_snapshots WHERE date IN (?, ?) AND (user_id IS NULL OR user_id = '')",
            (d1, d2),
        )
        remaining = int(cursor.fetchone()['cnt'])
        conn.close()
        self.assertEqual(remaining, 0)


if __name__ == '__main__':
    unittest.main()

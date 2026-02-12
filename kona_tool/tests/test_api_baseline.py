import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

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


if __name__ == '__main__':
    unittest.main()

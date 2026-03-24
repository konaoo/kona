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


class QuoteApiTests(unittest.TestCase):
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
            self.assertGreater(int(resp.headers.get('X-Trace-Stage-Count', '0')), 0)

    def test_price_mocked(self):
        with patch.object(app_module, 'get_price', return_value=(10, 9, 0, 0)):
            resp = self.client.get('/api/price?code=sh600000')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual(data.get('price'), 10)

    def test_search_mocked(self):
        with patch.object(app_module, 'search_stocks', return_value=[{'code': 'sh600000'}]):
            resp = self.client.get('/api/search?q=浦发')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json() or []
            self.assertEqual(data[0].get('code'), 'sh600000')

    def test_prices_batch_mocked(self):
        with patch.object(app_module, 'batch_get_prices_fast', return_value={'sh600000': (10, 9, 0, 0)}):
            resp = self.client.post('/api/prices/batch', json={'codes': ['sh600000']})
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn('sh600000', data)
            self.assertEqual(data['sh600000']['price'], 10)
            self.assertGreater(int(resp.headers.get('X-Trace-Stage-Count', '0')), 0)

    def test_prices_batch_merges_us_extended_quote(self):
        with patch.object(app_module, 'batch_get_prices', return_value={'AAPL': (10, 9, 1, 11.1)}):
            with patch.object(
                app_module,
                'get_us_extended_quotes',
                return_value={
                    'AAPL': {
                        'price': 10.5,
                        'yclose': 9.0,
                        'amt': 1.5,
                        'chg': 16.6,
                        'regular_price': 10.0,
                        'premarket_price': 10.5,
                        'after_hours_price': 0.0,
                        'session': 'pre',
                        'effective_session': 'pre',
                        'extended_active': True,
                    }
                },
            ):
                resp = self.client.post('/api/prices/batch', json={'codes': ['AAPL']})
                self.assertEqual(resp.status_code, 200)
                body = resp.get_json() or {}
                self.assertIn('AAPL', body)
                quote = body['AAPL']
                self.assertEqual(float(quote.get('price', 0)), 10.5)
                self.assertEqual(float(quote.get('amt', 0)), 1.5)
                self.assertEqual(str(quote.get('session')), 'pre')
                self.assertEqual(bool(quote.get('extended_active')), True)


if __name__ == '__main__':
    unittest.main()

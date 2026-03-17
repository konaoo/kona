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


class PortfolioApiTests(unittest.TestCase):
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
        self.assertGreater(int(buy_first.headers.get('X-Trace-Stage-Count') or 0), 0)

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

    def test_portfolio_modify_allows_negative_cost_price(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600002',
            'name': '测试负成本',
            'price': 10.0,
            'qty': 5.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        modify_resp = self.client.post('/api/portfolio/modify', json={
            'code': 'sh600002',
            'qty': 5.0,
            'price': -1.23,
            'adjustment': 3.0,
        })
        self.assertEqual(modify_resp.status_code, 200)
        self.assertEqual((modify_resp.get_json() or {}).get('status'), 'ok')
        self.assertGreater(int(modify_resp.headers.get('X-Trace-Stage-Count') or 0), 0)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600002'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('price') or 0.0), -1.23, places=6)

    def test_add_buy_sell_reject_non_positive_price(self):
        bad_add = self.client.post('/api/portfolio/add', json={
            'code': 'sh600003',
            'name': '非法新增',
            'price': 0.0,
            'qty': 1.0,
        })
        self.assertEqual(bad_add.status_code, 400)
        self.assertEqual((bad_add.get_json() or {}).get('code'), 'INVALID_VALUE')

        add_ok = self.client.post('/api/portfolio/add', json={
            'code': 'sh600003',
            'name': '合法新增',
            'price': 10.0,
            'qty': 2.0,
        })
        self.assertEqual(add_ok.status_code, 200)

        bad_buy = self.client.post('/api/portfolio/buy', json={
            'code': 'sh600003',
            'price': -1.0,
            'qty': 1.0,
        })
        self.assertEqual(bad_buy.status_code, 400)
        self.assertEqual((bad_buy.get_json() or {}).get('code'), 'INVALID_VALUE')

        bad_sell = self.client.post('/api/portfolio/sell', json={
            'code': 'sh600003',
            'price': 0.0,
            'qty': 1.0,
        })
        self.assertEqual(bad_sell.status_code, 400)
        self.assertEqual((bad_sell.get_json() or {}).get('code'), 'INVALID_VALUE')

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

    def test_sell_all_keeps_realized_pnl_in_cumulative_total(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600010',
            'name': '测试清仓',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        sell_resp = self.client.post('/api/portfolio/sell', json={
            'code': 'sh600010',
            'price': 12.0,
            'qty': 10.0,
            'request_id': 'req-sellall-1',
        })
        self.assertEqual(sell_resp.status_code, 200)
        self.assertEqual(sell_resp.get_json().get('status'), 'ok')

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600010' for item in items))

        with patch('core.snapshot.batch_get_prices', return_value={'sh600010': (12.0, 12.0, 0, 0)}):
            with patch('core.snapshot.get_forex_rates', return_value={'CNY': 1.0}):
                stats = app_module.calculate_portfolio_stats(None)
        self.assertAlmostEqual(float(stats.get('total_pnl') or 0.0), 20.0, places=2)

    def test_buy_with_cash_and_undo_restores_cash_and_portfolio(self):
        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '银行卡',
            'amount': 20000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        self.assertTrue(len(cash_assets) > 0)
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': 'sh600000',
            'name': '浦发银行',
            'price': 10.0,
            'qty': 100.0,
            'cash_asset_id': cash_id,
            'request_id': 'req-buy-with-cash-1',
        })
        self.assertEqual(buy_resp.status_code, 200)
        buy_payload = buy_resp.get_json()
        self.assertEqual(buy_payload.get('status'), 'ok')
        self.assertGreater(int(buy_resp.headers.get('X-Trace-Stage-Count') or 0), 0)
        undo_token = buy_payload.get('undo_token')
        self.assertTrue(isinstance(undo_token, str) and len(undo_token) > 0)

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        target = next((item for item in portfolio_items if item.get('code') == 'sh600000'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('qty', 0)), 100.0)

        cash_list_resp_after_buy = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp_after_buy.status_code, 200)
        cash_after_buy = cash_list_resp_after_buy.get_json() or []
        buy_cash_item = next((item for item in cash_after_buy if item.get('id') == cash_id), None)
        self.assertIsNotNone(buy_cash_item)
        self.assertAlmostEqual(float(buy_cash_item.get('amount', 0)), 19000.0)

        undo_resp = self.client.post('/api/portfolio/undo', json={
            'undo_token': undo_token,
        })
        self.assertEqual(undo_resp.status_code, 200)
        undo_payload = undo_resp.get_json()
        self.assertEqual(undo_payload.get('status'), 'ok')
        self.assertEqual(undo_payload.get('code'), 'UNDO_DONE')
        self.assertGreater(int(undo_resp.headers.get('X-Trace-Stage-Count') or 0), 0)

        portfolio_resp_after_undo = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp_after_undo.status_code, 200)
        portfolio_after_undo = portfolio_resp_after_undo.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600000' for item in portfolio_after_undo))

        cash_list_resp_after_undo = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp_after_undo.status_code, 200)
        cash_after_undo = cash_list_resp_after_undo.get_json() or []
        undo_cash_item = next((item for item in cash_after_undo if item.get('id') == cash_id), None)
        self.assertIsNotNone(undo_cash_item)
        self.assertAlmostEqual(float(undo_cash_item.get('amount', 0)), 20000.0)

    def test_sell_to_cash_and_undo_restores_cash_and_portfolio(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600519',
            'name': '贵州茅台',
            'price': 1000.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '银行卡',
            'amount': 2000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        sell_resp = self.client.post('/api/portfolio/sell_to_cash', json={
            'code': 'sh600519',
            'price': 1200.0,
            'qty': 2.0,
            'cash_asset_id': cash_id,
            'request_id': 'req-sell-to-cash-1',
        })
        self.assertEqual(sell_resp.status_code, 200)
        sell_payload = sell_resp.get_json() or {}
        self.assertEqual(sell_payload.get('status'), 'ok')
        self.assertGreater(int(sell_resp.headers.get('X-Trace-Stage-Count') or 0), 0)
        self.assertAlmostEqual(float(sell_payload.get('cash_added') or 0.0), 2400.0)
        undo_token = sell_payload.get('undo_token')
        self.assertTrue(isinstance(undo_token, str) and len(undo_token) > 0)

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        target = next((item for item in portfolio_items if item.get('code') == 'sh600519'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('qty', 0)), 8.0)

        cash_after_sell_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_after_sell_resp.status_code, 200)
        cash_after_sell = cash_after_sell_resp.get_json() or []
        sell_cash_item = next((item for item in cash_after_sell if item.get('id') == cash_id), None)
        self.assertIsNotNone(sell_cash_item)
        self.assertAlmostEqual(float(sell_cash_item.get('amount', 0)), 4400.0)

        undo_resp = self.client.post('/api/portfolio/undo', json={'undo_token': undo_token})
        self.assertEqual(undo_resp.status_code, 200)
        self.assertEqual((undo_resp.get_json() or {}).get('code'), 'UNDO_DONE')

        portfolio_after_undo_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_after_undo_resp.status_code, 200)
        portfolio_after_undo = portfolio_after_undo_resp.get_json() or []
        undo_target = next((item for item in portfolio_after_undo if item.get('code') == 'sh600519'), None)
        self.assertIsNotNone(undo_target)
        self.assertAlmostEqual(float(undo_target.get('qty', 0)), 10.0)

        cash_after_undo_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_after_undo_resp.status_code, 200)
        cash_after_undo = cash_after_undo_resp.get_json() or []
        undo_cash_item = next((item for item in cash_after_undo if item.get('id') == cash_id), None)
        self.assertIsNotNone(undo_cash_item)
        self.assertAlmostEqual(float(undo_cash_item.get('amount', 0)), 2000.0)

    def test_buy_with_cash_insufficient_balance_returns_400(self):
        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '微信',
            'amount': 100.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': 'sh600000',
            'name': '浦发银行',
            'price': 20.0,
            'qty': 10.0,
            'cash_asset_id': cash_id,
        })
        self.assertEqual(buy_resp.status_code, 400)
        payload = buy_resp.get_json()
        self.assertEqual(payload.get('code'), 'INSUFFICIENT_CASH')

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600000' for item in portfolio_items))

    def test_buy_with_cash_supports_fund_decimal_qty(self):
        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '支付宝',
            'amount': 1000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': 'f_110017',
            'name': '易方达增强回报债券A',
            'price': 1.2345,
            'qty': 81.0044,
            'cash_asset_id': cash_id,
            'request_id': 'req-buy-fund-decimal-qty',
        })
        self.assertEqual(buy_resp.status_code, 200)
        self.assertEqual((buy_resp.get_json() or {}).get('status'), 'ok')

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        target = next((item for item in portfolio_items if item.get('code') == 'f_110017'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('qty') or 0.0), 81.0044, places=4)

    def test_buy_with_cash_merges_legacy_numeric_exchange_fund_position(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ('159655', '标普ETF', 8400.0, 1.783, 'CNY', 0.0, 'fund', ''),
        )
        conn.commit()
        conn.close()

        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '浦发银行',
            'amount': 50000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': '159655',
            'name': '标普ETF',
            'price': 1.72,
            'qty': 1600.0,
            'curr': 'CNY',
            'asset_type': 'fund',
            'cash_asset_id': cash_id,
            'request_id': 'req-buy-legacy-exchange-fund',
        })
        self.assertEqual(buy_resp.status_code, 200)
        self.assertEqual((buy_resp.get_json() or {}).get('status'), 'ok')

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        legacy_target = next((item for item in portfolio_items if item.get('code') == '159655'), None)
        self.assertIsNotNone(legacy_target)
        self.assertAlmostEqual(float(legacy_target.get('qty') or 0.0), 10000.0, places=4)
        self.assertFalse(any(item.get('code') == 'sz159655' for item in portfolio_items))

        tx_resp = self.client.get('/api/transactions?limit=20')
        self.assertEqual(tx_resp.status_code, 200)
        tx_items = tx_resp.get_json() or []
        target_tx = next((item for item in tx_items if item.get('name') == '标普ETF'), None)
        self.assertIsNotNone(target_tx)
        self.assertEqual(target_tx.get('code'), '159655')

    def test_snapshot_trigger_returns_ok_when_take_snapshot_succeeds(self):
        with patch.object(app_module, 'take_snapshot', return_value=True) as mocked:
            resp = self.client.post('/api/snapshot/trigger', json={})
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertEqual(payload.get('status'), 'ok')
        mocked.assert_called_once_with(None)

    def test_snapshot_fix_requires_dates_list(self):
        missing_resp = self.client.post('/api/snapshot/fix', json={})
        self.assertEqual(missing_resp.status_code, 400)
        self.assertEqual((missing_resp.get_json() or {}).get('error'), 'Missing dates')

        invalid_resp = self.client.post('/api/snapshot/fix', json={'dates': '2026-01-17'})
        self.assertEqual(invalid_resp.status_code, 400)
        self.assertEqual((invalid_resp.get_json() or {}).get('error'), 'dates must be a list')

        with patch.object(app_module.db, 'fix_snapshot_day_pnl', return_value=True) as mocked:
            ok_resp = self.client.post('/api/snapshot/fix', json={'dates': ['2026-01-17', '2026-01-18']})
        self.assertEqual(ok_resp.status_code, 200)
        self.assertEqual((ok_resp.get_json() or {}).get('status'), 'ok')
        mocked.assert_called_once_with(['2026-01-17', '2026-01-18'], None)


if __name__ == '__main__':
    unittest.main()

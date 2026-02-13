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

    def test_analysis_calendar_supports_year_month_query(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-02-03', 1, 1000, 1, 0, 0, 100, 10, '')
            """
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-02-04', 1, 1000, 1, 0, 0, 120, 20, '')
            """
        )
        conn.commit()
        conn.close()

        resp = self.client.get('/api/analysis/calendar?type=day&year=2026&month=2')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertEqual(payload.get('title'), '2026年2月累计')
        self.assertEqual(payload.get('period', {}).get('year'), 2026)
        self.assertEqual(payload.get('period', {}).get('month'), 2)
        self.assertIn('selectable', payload)

    def test_analysis_calendar_month_supports_year_query(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2024-12-31', 1, 1000, 1, 0, 0, 100, 0, '')
            """
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2025-01-15', 1, 1000, 1, 0, 0, 130, 0, '')
            """
        )
        conn.commit()
        conn.close()

        resp = self.client.get('/api/analysis/calendar?type=month&year=2025')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertEqual(payload.get('period', {}).get('year'), 2025)
        self.assertEqual(payload.get('title'), '2025年累计')

    def test_analysis_calendar_invalid_month_returns_400(self):
        resp = self.client.get('/api/analysis/calendar?type=day&year=2026&month=13')
        self.assertEqual(resp.status_code, 400)
        payload = resp.get_json()
        self.assertEqual(payload.get('code'), 'INVALID_CALENDAR_PERIOD')

    def test_analysis_overview_month_year_all_calculation(self):
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        month_start = today.replace(day=1)
        year_start = datetime(today.year, 1, 1).date()
        prev_month = month_start - timedelta(days=1)
        prev_year = year_start - timedelta(days=1)

        prev_month_pnl = 120.0
        prev_year_pnl = 90.0
        if prev_month == prev_year:
            prev_year_pnl = prev_month_pnl

        today_pnl = 260.0
        today_invest = 1200.0

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, ?, 0, '')
            """,
            (prev_year.strftime('%Y-%m-%d'), prev_year_pnl),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, ?, 0, '')
            """,
            (prev_month.strftime('%Y-%m-%d'), prev_month_pnl),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, ?, 1, 0, 0, ?, 0, '')
            """,
            (today_str, today_invest, today_pnl),
        )
        conn.commit()
        conn.close()

        resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        month_expected = today_pnl - prev_month_pnl
        year_expected = today_pnl - prev_year_pnl
        all_expected = today_pnl
        self.assertAlmostEqual(float((payload.get('month') or {}).get('pnl', 0)), month_expected)
        self.assertAlmostEqual(float((payload.get('year') or {}).get('pnl', 0)), year_expected)
        self.assertAlmostEqual(float((payload.get('all') or {}).get('pnl', 0)), all_expected)

    def test_analysis_overview_year_matches_calendar_month_total_with_future_row(self):
        today = datetime.now().date()
        future_same_month = today + timedelta(days=1)
        if future_same_month.month != today.month or future_same_month.year != today.year:
            self.skipTest("month boundary; no safe future date in current month")

        prev_year = datetime(today.year, 1, 1).date() - timedelta(days=1)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 0, 0, '')
            """,
            (prev_year.strftime('%Y-%m-%d'),),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 21000, 0, '')
            """,
            (today.strftime('%Y-%m-%d'),),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, -745, 0, '')
            """,
            (future_same_month.strftime('%Y-%m-%d'),),
        )
        conn.commit()
        conn.close()

        overview_resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(overview_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        year_pnl = float((overview.get('year') or {}).get('pnl', 0))
        self.assertAlmostEqual(year_pnl, 21000.0)

        calendar_resp = self.client.get(f"/api/analysis/calendar?type=month&year={today.year}")
        self.assertEqual(calendar_resp.status_code, 200)
        calendar_payload = calendar_resp.get_json() or {}
        calendar_total = float(calendar_payload.get('total_pnl', 0))
        self.assertAlmostEqual(calendar_total, year_pnl)

    def test_analysis_overview_year_matches_calendar_when_no_prev_year_snapshot(self):
        today = datetime.now().date()
        month_start = today.replace(day=1)
        first_in_period = month_start + timedelta(days=2)
        if first_in_period > today:
            first_in_period = today

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 0, '')
            """,
            (first_in_period.strftime('%Y-%m-%d'),),
        )
        conn.commit()
        conn.close()

        overview_resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(overview_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        year_pnl = float((overview.get('year') or {}).get('pnl', 0))

        calendar_resp = self.client.get(f"/api/analysis/calendar?type=month&year={today.year}")
        self.assertEqual(calendar_resp.status_code, 200)
        calendar_payload = calendar_resp.get_json() or {}
        calendar_total = float(calendar_payload.get('total_pnl', 0))

        self.assertAlmostEqual(year_pnl, calendar_total)

    def test_analysis_overview_all_ignores_future_snapshots(self):
        today = datetime.now().date()
        future_date = today + timedelta(days=1)
        prev_year = datetime(today.year, 1, 1).date() - timedelta(days=1)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 0, 0, '')
            """,
            (prev_year.strftime('%Y-%m-%d'),),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 21000, 0, '')
            """,
            (today.strftime('%Y-%m-%d'),),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, -745, 0, '')
            """,
            (future_date.strftime('%Y-%m-%d'),),
        )
        conn.commit()
        conn.close()

        resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        all_pnl = float((payload.get('all') or {}).get('pnl', 0))
        self.assertAlmostEqual(all_pnl, 21000.0)

    def test_analysis_overview_all_matches_calendar_when_first_snapshot_nonzero(self):
        today = datetime.now().date()
        first_in_period = today.replace(day=1) + timedelta(days=1)
        if first_in_period > today:
            first_in_period = today

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 0, '')
            """,
            (first_in_period.strftime('%Y-%m-%d'),),
        )
        conn.commit()
        conn.close()

        overview_resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(overview_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        all_pnl = float((overview.get('all') or {}).get('pnl', 0))

        calendar_resp = self.client.get(f"/api/analysis/calendar?type=year")
        self.assertEqual(calendar_resp.status_code, 200)
        calendar_payload = calendar_resp.get_json() or {}
        calendar_total = float(calendar_payload.get('total_pnl', 0))

        self.assertAlmostEqual(all_pnl, 21361.58)
        self.assertAlmostEqual(all_pnl, calendar_total)

    def test_analysis_overview_all_returns_latest_total_pnl_not_delta(self):
        today = datetime.now().date()
        prev_year = datetime(today.year, 1, 1).date() - timedelta(days=1)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 22106.51, 0, '')
            """,
            (prev_year.strftime('%Y-%m-%d'),),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 0, '')
            """,
            (today.strftime('%Y-%m-%d'),),
        )
        conn.commit()
        conn.close()

        overview_resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(overview_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        all_pnl = float((overview.get('all') or {}).get('pnl', 0))

        self.assertAlmostEqual(all_pnl, 21361.58)

    def test_analysis_baseline_route_removed_returns_404(self):
        resp = self.client.get('/api/analysis/baseline')
        self.assertEqual(resp.status_code, 404)

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


if __name__ == '__main__':
    unittest.main()

import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class AnalysisApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio_adjustment_ledger")
        cursor.execute("DELETE FROM cash_assets")
        cursor.execute("DELETE FROM other_assets")
        cursor.execute("DELETE FROM liabilities")
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM ledger_daily_snapshots")
        cursor.execute("DELETE FROM investment_ledgers")
        cursor.execute("DELETE FROM daily_snapshots")
        cursor.execute("DELETE FROM runtime_configs")
        conn.commit()
        conn.close()

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

    def test_analysis_overview_month_year_all_uses_snapshot_day_pnl_sum(self):
        fixed_now = datetime(2026, 2, 13, 14, 0, 0)
        today = fixed_now.date()
        today_str = today.strftime('%Y-%m-%d')
        anchor = today - timedelta(days=1)
        anchor_str = anchor.strftime('%Y-%m-%d')
        month_start = today.replace(day=1)
        year_start = datetime(today.year, 1, 1).date()
        prev_month = month_start - timedelta(days=1)
        prev_year = year_start - timedelta(days=1)

        prev_month_pnl = 120.0
        prev_year_pnl = 90.0
        if prev_month == prev_year:
            prev_year_pnl = prev_month_pnl

        anchor_day_pnl = 55.0
        today_day_pnl = 70.0
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
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, ?, 1, 0, 0, ?, ?, '', ?)
            """,
            (anchor_str, today_invest, 9999.0, anchor_day_pnl, f"{anchor_str} 14:00:00"),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, ?, 1, 0, 0, ?, ?, '', ?)
            """,
            (today_str, today_invest, -999.0, today_day_pnl, f"{today_str} 14:00:00"),
        )
        conn.commit()
        conn.close()

        # 直接 patch 分析层的“当前时间”入口，避免被其他测试对 sys.modules/core.db 的覆盖污染。
        with patch('core.db_analysis._get_datetime_now', return_value=fixed_now):
            resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        expected = anchor_day_pnl + today_day_pnl
        self.assertAlmostEqual(float((payload.get('month') or {}).get('pnl', 0)), expected)
        self.assertAlmostEqual(float((payload.get('year') or {}).get('pnl', 0)), expected)
        self.assertAlmostEqual(float((payload.get('all') or {}).get('pnl', 0)), expected)
        self.assertAlmostEqual(float((payload.get('month') or {}).get('base_value', 0)), 1000.0)
        self.assertAlmostEqual(float((payload.get('year') or {}).get('base_value', 0)), 1000.0)
        self.assertAlmostEqual(float((payload.get('all') or {}).get('base_value', 0)), 1000.0)
        self.assertAlmostEqual(float((payload.get('month') or {}).get('pnl_rate', 0)), 12.5)
        self.assertAlmostEqual(float((payload.get('year') or {}).get('pnl_rate', 0)), 12.5)
        self.assertAlmostEqual(float((payload.get('all') or {}).get('pnl_rate', 0)), 12.5)

    def test_analysis_calendar_today_item_keeps_snapshot_value(self):
        fixed_now = datetime(2026, 2, 12, 14, 0, 0)
        today = fixed_now.date()
        today_str = today.strftime('%Y-%m-%d')
        previous_day = today - timedelta(days=1)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 100, 10, '')
            """,
            (previous_day.strftime('%Y-%m-%d'),),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 141, 41, '')
            """,
            (today_str,),
        )
        conn.commit()
        conn.close()

        with patch('core.db_analysis._get_datetime_now', return_value=fixed_now):
            resp = self.client.get(
                f'/api/analysis/calendar?type=day&year={today.year}&month={today.month}'
            )
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        items = payload.get('items') or []
        today_item = next(
            (item for item in items if str(item.get('label')) == f'{today.month}-{today.day}'),
            None,
        )
        self.assertIsNotNone(today_item)
        self.assertAlmostEqual(float(today_item.get('pnl', 0)), 41.0)

    def test_analysis_overview_month_uses_snapshot_day_pnl_not_breakdown_sum(self):
        fixed_now = datetime(2026, 3, 22, 12, 0, 0)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES ('2026-03-19', 1, 1000, 1, 0, 0, 100, -1250.87, '', '2026-03-19 23:00:00')
            """
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES ('2026-03-20', 1, 1000, 1, 0, 0, 100, -1611.46, '', '2026-03-20 23:00:00')
            """
        )
        for market, pnl in {
            "a": 0.0,
            "hk": 0.0,
            "us": 0.0,
            "fund": -34.64,
            "unallocated": 0.0,
        }.items():
            cursor.execute(
                """
                INSERT OR REPLACE INTO daily_snapshot_market_breakdowns
                (date, user_id, market, day_pnl, source, confidence, updated_at)
                VALUES ('2026-03-19', '', ?, ?, 'exact', 1.0, '2026-03-21 00:00:00')
                """,
                (market, pnl),
            )
        conn.commit()
        conn.close()

        with patch('core.db_analysis._get_datetime_now', return_value=fixed_now):
            resp = self.client.get('/api/analysis/overview?period=month')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertAlmostEqual(float((payload.get('month') or {}).get('pnl', 0)), -2862.33, places=2)

    def test_analysis_overview_year_matches_calendar_month_total_with_future_row(self):
        fixed_now = datetime(2026, 2, 13, 14, 0, 0)
        today = fixed_now.date()
        anchor = today - timedelta(days=1)
        future_same_month = today + timedelta(days=1)
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
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, 1000, 1, 0, 0, 21000, 210, '', ?)
            """,
            (anchor.strftime('%Y-%m-%d'), f"{anchor.strftime('%Y-%m-%d')} 14:00:00"),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, 1000, 1, 0, 0, -745, -745, '', ?)
            """,
            (future_same_month.strftime('%Y-%m-%d'), f"{future_same_month.strftime('%Y-%m-%d')} 14:00:00"),
        )
        conn.commit()
        conn.close()

        with patch('core.db_analysis._get_datetime_now', return_value=fixed_now):
            overview_resp = self.client.get('/api/analysis/overview?period=all')
            calendar_resp = self.client.get(f"/api/analysis/calendar?type=month&year={today.year}")
        self.assertEqual(overview_resp.status_code, 200)
        self.assertEqual(calendar_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        calendar_payload = calendar_resp.get_json() or {}
        year_pnl = float((overview.get('year') or {}).get('pnl', 0))
        calendar_total = float(calendar_payload.get('total_pnl', 0))
        self.assertAlmostEqual(year_pnl, 210.0)
        self.assertAlmostEqual(calendar_total, year_pnl)

    def test_analysis_overview_year_matches_calendar_when_no_prev_year_snapshot(self):
        fixed_now = datetime(2026, 2, 13, 14, 0, 0)
        today = fixed_now.date()
        first_in_period = datetime(today.year, today.month, 3).date()

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 123.45, '', ?)
            """,
            (first_in_period.strftime('%Y-%m-%d'), f"{first_in_period.strftime('%Y-%m-%d')} 14:00:00"),
        )
        conn.commit()
        conn.close()

        with patch('core.db_analysis._get_datetime_now', return_value=fixed_now):
            overview_resp = self.client.get('/api/analysis/overview?period=all')
            calendar_resp = self.client.get(f"/api/analysis/calendar?type=month&year={today.year}")
        self.assertEqual(overview_resp.status_code, 200)
        self.assertEqual(calendar_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        calendar_payload = calendar_resp.get_json() or {}
        year_pnl = float((overview.get('year') or {}).get('pnl', 0))
        calendar_total = float(calendar_payload.get('total_pnl', 0))
        self.assertAlmostEqual(year_pnl, calendar_total)

    def test_analysis_overview_all_ignores_future_snapshots(self):
        fixed_now = datetime(2026, 2, 13, 14, 0, 0)
        today = fixed_now.date()
        future_date = today + timedelta(days=1)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, 21000, 21000, '')
            """,
            (today.strftime('%Y-%m-%d'),),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1000, 1, 0, 0, -745, -745, '')
            """,
            (future_date.strftime('%Y-%m-%d'),),
        )
        conn.commit()
        conn.close()

        with patch('core.db_analysis._get_datetime_now', return_value=fixed_now):
            resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        all_pnl = float((payload.get('all') or {}).get('pnl', 0))
        self.assertAlmostEqual(all_pnl, 21000.0)

    def test_analysis_overview_all_matches_calendar_when_first_snapshot_nonzero(self):
        fixed_now = datetime(2026, 2, 13, 14, 0, 0)
        today = fixed_now.date()
        first_in_period = datetime(today.year, today.month, 2).date()

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 123.45, '', ?)
            """,
            (first_in_period.strftime('%Y-%m-%d'), f"{first_in_period.strftime('%Y-%m-%d')} 14:00:00"),
        )
        conn.commit()
        conn.close()

        with patch('core.db_analysis._get_datetime_now', return_value=fixed_now):
            overview_resp = self.client.get('/api/analysis/overview?period=all')
            calendar_resp = self.client.get("/api/analysis/calendar?type=year")
        self.assertEqual(overview_resp.status_code, 200)
        self.assertEqual(calendar_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        calendar_payload = calendar_resp.get_json() or {}
        all_pnl = float((overview.get('all') or {}).get('pnl', 0))
        calendar_total = float(calendar_payload.get('total_pnl', 0))
        self.assertAlmostEqual(all_pnl, 123.45)
        self.assertAlmostEqual(all_pnl, calendar_total)

    def test_analysis_overview_all_returns_snapshot_day_pnl_sum_not_latest_total(self):
        fixed_now = datetime(2026, 2, 13, 14, 0, 0)
        today = fixed_now.date()
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
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 55.0, '', ?)
            """,
            (today.strftime('%Y-%m-%d'), f"{today.strftime('%Y-%m-%d')} 14:00:00"),
        )
        conn.commit()
        conn.close()

        with patch('core.db_analysis._get_datetime_now', return_value=fixed_now):
            overview_resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(overview_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        all_pnl = float((overview.get('all') or {}).get('pnl', 0))
        self.assertAlmostEqual(all_pnl, 55.0)

    def test_analysis_baseline_route_removed_returns_404(self):
        resp = self.client.get('/api/analysis/baseline')
        self.assertEqual(resp.status_code, 404)

    def test_analysis_rank_uses_absolute_cost_for_pnl_rate(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600004',
            'name': '排行负成本',
            'price': 5.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        modify_resp = self.client.post('/api/portfolio/modify', json={
            'code': 'sh600004',
            'qty': 10.0,
            'price': -2.0,
            'adjustment': 0.0,
        })
        self.assertEqual(modify_resp.status_code, 200)

        with patch.object(app_module, 'batch_get_prices', return_value={'sh600004': (0.0, 0.0, 0.0, 0.0)}):
            rank_resp = self.client.get('/api/analysis/rank?type=all')
        self.assertEqual(rank_resp.status_code, 200)
        payload = rank_resp.get_json() or {}
        items = (payload.get('gain') or []) + (payload.get('loss') or [])
        target = next((item for item in items if item.get('code') == 'sh600004'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('pnl') or 0.0), 20.0, places=2)
        self.assertAlmostEqual(float(target.get('pnl_rate') or 0.0), 100.0, places=2)

    def test_analysis_rank_includes_ledger_adjustment(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600013',
            'name': '排行流水补差',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio_adjustment_ledger (user_id, code, event_type, amount, curr, note, source)
            VALUES ('', 'sh600013', 'dividend', 15.0, 'CNY', '', 'test')
            """
        )
        conn.commit()
        conn.close()

        with patch.object(app_module, 'batch_get_prices', return_value={'sh600013': (0.0, 10.0, 0.0, 0.0)}):
            rank_resp = self.client.get('/api/analysis/rank?type=all')
        self.assertEqual(rank_resp.status_code, 200)
        payload = rank_resp.get_json() or {}
        items = (payload.get('gain') or []) + (payload.get('loss') or [])
        target = next((item for item in items if item.get('code') == 'sh600013'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('pnl') or 0.0), 15.0, places=2)

    def test_analysis_rank_ignores_legacy_adjustment_after_migration_switch(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600014',
            'name': '排行新口径',
            'price': 10.0,
            'qty': 10.0,
            'adjustment': 5.0,
        })
        self.assertEqual(add_resp.status_code, 200)
        app_module.db.set_portfolio_legacy_adjustment_ignored(True, note='切到新口径')

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio_adjustment_ledger (user_id, code, event_type, amount, curr, note, source)
            VALUES ('', 'sh600014', 'dividend', 15.0, 'CNY', '', 'test')
            """
        )
        conn.commit()
        conn.close()

        with patch.object(app_module, 'batch_get_prices', return_value={'sh600014': (0.0, 10.0, 0.0, 0.0)}):
            rank_resp = self.client.get('/api/analysis/rank?type=all')
        self.assertEqual(rank_resp.status_code, 200)
        payload = rank_resp.get_json() or {}
        items = (payload.get('gain') or []) + (payload.get('loss') or [])
        target = next((item for item in items if item.get('code') == 'sh600014'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('pnl') or 0.0), 15.0, places=2)

    def test_analysis_rank_keeps_same_code_isolated_by_ledger(self):
        default_ledger_id = app_module.db.get_default_ledger_id('')
        second_ledger = app_module.db.create_ledger('', '分析第二账本')
        second_ledger_id = int(second_ledger['ledger_id'])

        asset_payload = {
            'code': 'sh600015',
            'name': '分析账本隔离',
            'qty': 10.0,
            'price': 10.0,
            'curr': 'CNY',
            'asset_type': 'a',
            'adjustment': 0.0,
        }
        self.assertTrue(app_module.db.add_asset(dict(asset_payload), user_id='', ledger_id=default_ledger_id))
        self.assertTrue(
            app_module.db.add_asset(
                {
                    **asset_payload,
                    'qty': 8.0,
                    'price': 12.0,
                },
                user_id='',
                ledger_id=second_ledger_id,
            )
        )
        self.assertTrue(
            app_module.db.add_portfolio_adjustment_event(
                code='sh600015',
                event_type='dividend',
                amount=15.0,
                user_id='',
                ledger_id=default_ledger_id,
            )
        )
        self.assertTrue(
            app_module.db.sell_asset(
                code='sh600015',
                price=14.0,
                qty=2.0,
                user_id='',
                ledger_id=second_ledger_id,
            )
        )

        with patch.object(app_module, 'batch_get_prices', return_value={'sh600015': (10.0, 10.0, 0.0, 0.0)}):
            default_resp = self.client.get(f'/api/analysis/rank?type=all&ledger_id={default_ledger_id}')
            second_resp = self.client.get(f'/api/analysis/rank?type=all&ledger_id={second_ledger_id}')

        self.assertEqual(default_resp.status_code, 200)
        self.assertEqual(second_resp.status_code, 200)

        default_items = ((default_resp.get_json() or {}).get('gain') or []) + ((default_resp.get_json() or {}).get('loss') or [])
        second_items = ((second_resp.get_json() or {}).get('gain') or []) + ((second_resp.get_json() or {}).get('loss') or [])
        default_target = next((item for item in default_items if item.get('code') == 'sh600015'), None)
        second_target = next((item for item in second_items if item.get('code') == 'sh600015'), None)
        self.assertIsNotNone(default_target)
        self.assertIsNotNone(second_target)
        self.assertAlmostEqual(float(default_target.get('pnl') or 0.0), 15.0, places=2)
        self.assertAlmostEqual(float(second_target.get('pnl') or 0.0), -8.0, places=2)

    def test_analysis_calendar_backfills_single_ledger_history_from_global_snapshots(self):
        ledger_id = app_module.db.get_default_ledger_id('')

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-03-01', 1000, 800, 200, 0, 0, 80, 10, '')
            """
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-03-02', 1020, 820, 200, 0, 0, 95, 15, '')
            """
        )
        conn.commit()
        conn.close()

        app_module.db.init_database()

        resp = self.client.get(f'/api/analysis/calendar?type=day&year=2026&month=3&ledger_id={ledger_id}')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        items = payload.get('items') or []
        item_map = {str(item.get('label')): float(item.get('pnl') or 0.0) for item in items}
        self.assertEqual(10.0, item_map.get('3-1'))
        self.assertEqual(15.0, item_map.get('3-2'))

    def test_analysis_calendar_backfills_default_ledger_history_when_other_ledgers_are_new(self):
        default_ledger_id = app_module.db.get_default_ledger_id('')

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO investment_ledgers (user_id, name, is_default, sort_order, created_at)
            VALUES ('', '新账本', 0, 1, '2026-03-10 09:00:00')
            """
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-03-01', 1000, 800, 200, 0, 0, 80, 10, '')
            """
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES ('2026-03-02', 1020, 820, 200, 0, 0, 95, 15, '')
            """
        )
        conn.commit()
        conn.close()

        app_module.db.init_database()

        resp = self.client.get(f'/api/analysis/calendar?type=day&year=2026&month=3&ledger_id={default_ledger_id}')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        items = payload.get('items') or []
        item_map = {str(item.get('label')): float(item.get('pnl') or 0.0) for item in items}
        self.assertEqual(10.0, item_map.get('3-1'))
        self.assertEqual(15.0, item_map.get('3-2'))

    def test_analysis_rejects_invalid_ledger_id(self):
        resp = self.client.get('/api/analysis/rank?type=all&ledger_id=bad-ledger')
        self.assertEqual(resp.status_code, 400)
        payload = resp.get_json() or {}
        self.assertEqual(payload.get('code'), 'INVALID_LEDGER_ID')


if __name__ == '__main__':
    unittest.main()

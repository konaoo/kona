import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

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
from core import snapshot as snapshot_module  # noqa: E402


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
        cursor.execute("DELETE FROM daily_snapshot_market_breakdowns")
        cursor.execute("DELETE FROM runtime_configs")
        conn.commit()
        conn.close()

    def test_web_config_endpoint(self):
        resp = self.client.get('/api/web/config')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertIn('portal_title', data)
        self.assertEqual(data.get('apk_download_url'), '/download/apk')
        self.assertIn('invite_acquire_text', data)
        self.assertIn('invite_acquire_image_url', data)
        self.assertIn('user_group_text', data)
        self.assertIn('user_group_image_url', data)

    def test_web_config_fallbacks_to_local_apk_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            apk_path = Path(tmp) / "kaka-latest-release.apk"
            apk_path.write_bytes(b"apk")
            with patch.object(app_module.config, "WEB_APK_DOWNLOAD_URL", ""), patch.object(
                app_module.config,
                "CLIENT_APP_DOWNLOAD_URL",
                "",
            ), patch.object(
                app_module.config,
                "WEB_APK_LOCAL_PATH",
                apk_path,
            ):
                resp = self.client.get('/api/web/config')
                self.assertEqual(resp.status_code, 200)
                data = resp.get_json() or {}
                self.assertEqual(data.get("apk_download_url"), "/download/apk")

    def test_web_config_prefers_runtime_invite_acquire_config(self):
        app_module.db.set_runtime_config("ops.invite_acquire.text", "进微信群领取邀请码", updated_by="test")
        app_module.db.set_runtime_config(
            "ops.invite_acquire.image_url",
            "https://example.com/invite.png",
            updated_by="test",
        )
        resp = self.client.get('/api/web/config')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertEqual(data.get("invite_acquire_text"), "进微信群领取邀请码")
        self.assertEqual(data.get("invite_acquire_image_url"), "https://example.com/invite.png")

    def test_web_config_prefers_runtime_user_group_config(self):
        app_module.db.set_runtime_config("ops.user_group.text", "加入咔咔用户群", updated_by="test")
        app_module.db.set_runtime_config(
            "ops.user_group.image_url",
            "https://example.com/user_group.webp",
            updated_by="test",
        )
        resp = self.client.get('/api/web/config')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertEqual(data.get("user_group_text"), "加入咔咔用户群")
        self.assertEqual(data.get("user_group_image_url"), "https://example.com/user_group.webp")

    def test_app_version_prefers_runtime_update_config(self):
        app_module.db.set_runtime_config(
            "ops.app_update.text",
            "1. 修复问题\n2. 优化体验",
            updated_by="test",
        )
        app_module.db.set_runtime_config(
            "ops.app_update.download_url",
            "https://example.com/new.apk",
            updated_by="test",
        )
        resp = self.client.get('/api/app/version')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertEqual(data.get("releaseNotes"), "1. 修复问题\n2. 优化体验")
        self.assertEqual(data.get("downloadUrl"), "https://example.com/new.apk")
        self.assertIn("version", data)
        self.assertIn("buildNumber", data)
        self.assertIn("forceUpdate", data)

    def test_app_version_defaults_to_domain_apk_download_url(self):
        resp = self.client.get('/api/app/version')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertEqual(data.get("downloadUrl"), "https://kakalog.fun/download/apk")

    def test_download_apk_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "not_exists.apk"
            with patch.object(app_module.config, "WEB_APK_LOCAL_PATH", missing_path):
                resp = self.client.get('/download/apk')
                self.assertEqual(resp.status_code, 404)
                data = resp.get_json() or {}
                self.assertEqual(data.get("error"), "APK not found")

    def test_download_apk_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            apk_path = Path(tmp) / "kaka-latest-release.apk"
            apk_path.write_bytes(b"apk-binary")
            with patch.object(app_module.config, "WEB_APK_LOCAL_PATH", apk_path):
                resp = self.client.get('/download/apk')
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(
                    resp.headers.get("Content-Type"),
                    "application/vnd.android.package-archive",
                )
                self.assertIn(
                    "attachment; filename=kaka-latest-release.apk",
                    resp.headers.get("Content-Disposition", ""),
                )
                self.assertEqual(resp.data, b"apk-binary")
                resp.close()

    def test_optional_auth_rejects_invalid_bearer_token(self):
        resp = self.client.get(
            '/api/portfolio?type=all',
            headers={'Authorization': 'Bearer invalid.token.payload'},
        )
        self.assertEqual(resp.status_code, 401)
        body = resp.get_json() or {}
        self.assertEqual(body.get('error'), '登录状态已过期，请重新登录')

    def test_optional_auth_rejects_invalid_bearer_token_on_bootstrap(self):
        resp = self.client.post(
            '/api/sync/bootstrap',
            json={'include': ['portfolio']},
            headers={'Authorization': 'Bearer invalid.token.payload'},
        )
        self.assertEqual(resp.status_code, 401)
        body = resp.get_json() or {}
        self.assertEqual(body.get('error'), '登录状态已过期，请重新登录')

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

    def test_portfolio_add_qdii_exchange_fund_code_normalizes_to_exchange_code(self):
        with patch.object(app_module, 'batch_get_prices', return_value={'sz159687': (1.7, 1.6, 0.1, 6.2)}):
            add_resp = self.client.post('/api/portfolio/add', json={
                'code': 'f_159687',
                'name': '南方东英富时亚太低碳精选ETF(QDII)',
                'price': 1.70,
                'qty': 10.0,
                'curr': 'CNY',
            })
        self.assertEqual(add_resp.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sz159687'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('curr'), 'CNY')
        self.assertEqual(target.get('asset_type'), 'a')
        self.assertEqual(target.get('category_type'), 'fund')

    def test_portfolio_add_shanghai_exchange_etf_code_normalizes_to_exchange_code(self):
        with patch.object(app_module, 'batch_get_prices', return_value={'sh511360': (113.133, 113.133, 0.0, 0.0)}):
            add_resp = self.client.post('/api/portfolio/add', json={
                'code': 'f_511360',
                'name': '短融ETF',
                'price': 113.13,
                'qty': 10.0,
                'curr': 'CNY',
            })
        self.assertEqual(add_resp.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh511360'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('curr'), 'CNY')
        self.assertEqual(target.get('asset_type'), 'a')
        self.assertEqual(target.get('category_type'), 'fund')

    def test_portfolio_add_otc_fund_code_keeps_f_prefix(self):
        with patch.object(app_module, 'batch_get_prices', return_value={}):
            add_resp = self.client.post('/api/portfolio/add', json={
                'code': 'f_110017',
                'name': '易方达增强回报债券A',
                'price': 1.23,
                'qty': 20.0,
                'curr': 'CNY',
            })
        self.assertEqual(add_resp.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'f_110017'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('asset_type'), 'fund')

    def test_portfolio_add_16_prefix_fund_keeps_fund_code(self):
        with patch.object(app_module, 'batch_get_prices', return_value={}):
            add_resp = self.client.post('/api/portfolio/add', json={
                'code': '161907',
                'name': '万家中证红利ETF联接A',
                'price': 1.60,
                'qty': 10.0,
                'curr': 'CNY',
            })
        self.assertEqual(add_resp.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'f_161907'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('asset_type'), 'fund')

    def test_portfolio_add_sh_b_share_forces_usd_currency(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh900901',
            'name': '沪B样本',
            'price': 1.0,
            'qty': 2.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_resp.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh900901'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('curr'), 'USD')

    def test_take_snapshot_only_writes_snapshot_date_breakdown(self):
        fake_stats = {
            "snapshot_date": "2026-03-21",
            "now_utc": datetime(2026, 3, 21, 2, 0, tzinfo=timezone.utc),
            "total_asset": 100.0,
            "total_invest": 80.0,
            "total_cash": 20.0,
            "total_other": 0.0,
            "total_liability": 0.0,
            "total_pnl": 5.0,
            "day_pnl": -10.0,
            "snapshot_day_pnl": 1.0,
            "snapshot_day_pnl_by_market": {
                "a": 1.0,
                "hk": 0.0,
                "us": 0.0,
                "fund": 0.0,
                "unallocated": 0.0,
            },
            "day_pnl_breakdowns_by_date": {
                "2026-03-20": {
                    "a": -10.0,
                    "hk": 0.0,
                    "us": 0.0,
                    "fund": 0.0,
                    "unallocated": 0.0,
                },
                "2026-03-21": {
                    "a": 1.0,
                    "hk": 0.0,
                    "us": 0.0,
                    "fund": 0.0,
                    "unallocated": 0.0,
                },
            },
        }

        with patch.object(snapshot_module, "calculate_portfolio_stats", return_value=fake_stats):
            with patch.object(
                snapshot_module,
                "get_market_statuses",
                return_value={
                    "a": {"open": True, "trading_day": True, "reason": "open_session"},
                    "hk": {"open": False, "trading_day": False, "reason": "holiday_or_weekend"},
                    "us": {"open": False, "trading_day": False, "reason": "holiday_or_weekend"},
                    "fund": {"open": False, "trading_day": False, "reason": "holiday_or_weekend"},
                },
            ):
                ok = snapshot_module.take_snapshot(user_id="u_test")
        self.assertTrue(ok)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT date, market, day_pnl
            FROM daily_snapshot_market_breakdowns
            WHERE user_id = ?
            ORDER BY date ASC, market ASC
            """,
            ("u_test",),
        )
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["date"], "2026-03-21")
        self.assertTrue(all(row["date"] == "2026-03-21" for row in rows))
        total = sum(float(row["day_pnl"] or 0.0) for row in rows)
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_portfolio_add_sz_b_share_forces_hkd_currency(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sz200002',
            'name': '深B样本',
            'price': 1.0,
            'qty': 2.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_resp.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sz200002'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('curr'), 'HKD')

    def test_b_share_currency_backfill_on_db_init(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ('sh900901', '沪B历史', 1.0, 1.0, 'CNY', 0.0, 'a', ''),
        )
        cursor.execute(
            """
            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ('sz200002', '深B历史', 1.0, 1.0, 'CNY', 0.0, 'a', ''),
        )
        conn.commit()
        conn.close()

        # 启动流程会调用 init_database；这里显式触发以验证幂等回填。
        app_module.db.init_database()

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        sh_target = next((item for item in items if item.get('code') == 'sh900901'), None)
        sz_target = next((item for item in items if item.get('code') == 'sz200002'), None)
        self.assertIsNotNone(sh_target)
        self.assertIsNotNone(sz_target)
        self.assertEqual(sh_target.get('curr'), 'USD')
        self.assertEqual(sz_target.get('curr'), 'HKD')

    def test_portfolio_add_invalid_f_prefix_letters_normalizes_to_us(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'f_NUGT',
            'name': '二倍做多金矿指数ETF-Direxion',
            'price': 303.938,
            'qty': 1.0,
            'curr': 'CNY',
            'asset_type': 'fund',
        })
        self.assertEqual(add_resp.status_code, 200)
        self.assertEqual(add_resp.get_json().get('status'), 'ok')

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'gb_nugt'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('asset_type'), 'us')
        self.assertEqual(target.get('curr'), 'USD')

    def test_portfolio_add_existing_name_not_overwritten_by_short_name(self):
        first = self.client.post('/api/portfolio/add', json={
            'code': 'gb_nugt',
            'name': '二倍做多金矿指数ETF-Direxion',
            'price': 303.938,
            'qty': 1.0,
            'curr': 'USD',
            'asset_type': 'us',
        })
        self.assertEqual(first.status_code, 200)

        second = self.client.post('/api/portfolio/add', json={
            'code': 'gb_nugt',
            'name': '3X多金矿',
            'price': 313.53,
            'qty': 2.0,
            'curr': 'USD',
            'asset_type': 'us',
        })
        self.assertEqual(second.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'gb_nugt'), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get('name'), '二倍做多金矿指数ETF-Direxion')
        self.assertAlmostEqual(float(target.get('qty') or 0.0), 2.0, places=6)

    def test_calculate_stats_converts_non_invest_assets_to_cny(self):
        add_cash = self.client.post('/api/cash_assets/add', json={
            'name': '港币账户',
            'amount': 100.0,
            'curr': 'HKD',
        })
        self.assertEqual(add_cash.status_code, 200)
        add_other = self.client.post('/api/other_assets/add', json={
            'name': '美元资产',
            'amount': 10.0,
            'curr': 'USD',
        })
        self.assertEqual(add_other.status_code, 200)
        add_liability = self.client.post('/api/liabilities/add', json={
            'name': '美元负债',
            'amount': 5.0,
            'curr': 'USD',
        })
        self.assertEqual(add_liability.status_code, 200)

        with patch('core.snapshot.batch_get_prices', return_value={}):
            with patch('core.snapshot.get_forex_rates', return_value={
                'CNY': 1.0,
                'HKD': 0.88,
                'USD': 7.0,
            }):
                stats = app_module.calculate_portfolio_stats(None)

        self.assertAlmostEqual(float(stats.get('total_cash') or 0.0), 88.0, places=2)
        self.assertAlmostEqual(float(stats.get('total_other') or 0.0), 70.0, places=2)
        self.assertAlmostEqual(float(stats.get('total_liability') or 0.0), 35.0, places=2)
        self.assertAlmostEqual(float(stats.get('total_asset') or 0.0), 123.0, places=2)

    def test_calculate_stats_returns_zero_day_pnl_before_market_open(self):
        fixed_now = datetime(2026, 3, 26, 1, 0, tzinfo=timezone.utc)
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600000',
            'name': '浦发银行',
            'price': 10.0,
            'qty': 2.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        with patch('core.snapshot.batch_get_prices', return_value={'sh600000': (11.0, 10.0, 0, 0)}):
            with patch('core.snapshot.get_forex_rates', return_value={'CNY': 1.0}):
                with patch(
                    'core.snapshot.get_market_statuses',
                    return_value={'a': {'open': False, 'trading_day': True, 'reason': 'off_hours'}},
                ):
                    with patch('core.snapshot.is_trading_day', create=True, return_value=True):
                        with patch('core.snapshot.is_markets_closed_on_date', create=True, return_value=False):
                            with patch.object(app_module.db, 'get_today_realized_pnl', return_value=0.0):
                                stats = app_module.calculate_portfolio_stats(None, now_utc=fixed_now)

        self.assertAlmostEqual(float(stats.get('day_pnl') or 0.0), 0.0, places=2)
        self.assertEqual(stats.get('day_pnl_effective_date'), '2026-03-26')

    def test_calculate_stats_counts_same_day_closed_sell_when_price_is_flat(self):
        fixed_now = datetime(2026, 3, 26, 3, 0, tzinfo=timezone.utc)
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
            VALUES ('sh600010', '包钢股份', 0, 10, 'CNY', 0, 'a', '')
            """
        )
        cursor.execute(
            """
            INSERT INTO transactions
                (time, code, name, type, price, qty, amount, pnl, curr, market, effective_date, user_id)
            VALUES
                ('2026-03-26 10:00:00', 'sh600010', '包钢股份', '减仓', 15, 100, 1500, 500, 'CNY', 'a', '2026-03-26', '')
            """
        )
        conn.commit()
        conn.close()

        with patch('core.snapshot.batch_get_prices', return_value={'sh600010': (10.0, 10.0, 0, 0)}):
            with patch('core.snapshot.get_forex_rates', return_value={'CNY': 1.0}):
                with patch(
                    'core.snapshot.get_market_statuses',
                    return_value={'a': {'open': True, 'trading_day': True, 'reason': 'open_session'}},
                ):
                    stats = app_module.calculate_portfolio_stats(None, now_utc=fixed_now)

        self.assertAlmostEqual(float(stats.get('day_pnl') or 0.0), 500.0, places=2)
        self.assertAlmostEqual(
            float((stats.get('day_pnl_breakdowns_by_date') or {}).get('2026-03-26', {}).get('a') or 0.0),
            500.0,
            places=2,
        )

    def test_calculate_stats_zero_day_pnl_on_non_trading_day(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600001',
            'name': '测试非交易日',
            'price': 10.0,
            'qty': 2.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        with patch('core.snapshot.batch_get_prices', return_value={'sh600001': (11.0, 10.0, 0, 0)}):
            with patch('core.snapshot.get_forex_rates', return_value={'CNY': 1.0}):
                with patch(
                    'core.snapshot.get_market_statuses',
                    return_value={'a': {'open': True, 'reason': 'open_session'}},
                ):
                    with patch('core.snapshot.is_trading_day', create=True, return_value=False):
                        with patch('core.snapshot.is_markets_closed_on_date', create=True, return_value=True):
                            with patch('core.snapshot.all_markets_closed', return_value=False):
                                with patch.object(app_module.db, 'get_today_realized_pnl', return_value=5.0):
                                    stats = app_module.calculate_portfolio_stats(None)

        self.assertAlmostEqual(float(stats.get('day_pnl') or 0.0), 0.0, places=2)

    def test_calculate_stats_attributes_us_overnight_to_previous_trading_day(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'gb_goog',
            'name': '谷歌',
            'price': 10.0,
            'qty': 1.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        with patch('core.snapshot.batch_get_prices', return_value={'gb_goog': (12.0, 10.0, 0, 0)}):
            with patch('core.snapshot.get_forex_rates', return_value={'USD': 7.0}):
                with patch(
                    'core.snapshot.get_market_statuses',
                    return_value={
                        'a': {'open': False, 'trading_day': False, 'reason': 'holiday_or_weekend'},
                        'hk': {'open': False, 'trading_day': False, 'reason': 'holiday_or_weekend'},
                        'us': {'open': True, 'trading_day': True, 'reason': 'open_session'},
                        'fund': {'open': False, 'trading_day': False, 'reason': 'holiday_or_weekend'},
                    },
                ):
                    with patch('core.snapshot.is_trading_day', create=True, side_effect=lambda market, date: market == 'us'):
                        stats = app_module.calculate_portfolio_stats(
                            None,
                            now_utc=datetime(2026, 3, 21, 2, 0, tzinfo=timezone.utc),
                        )

        # today 展示应认当前自然日，没有当日有效收益时不能把上一交易日顶上来
        self.assertEqual(stats.get('day_pnl_effective_date'), '2026-03-21')
        self.assertAlmostEqual(float(stats.get('day_pnl') or 0.0), 0.0, places=2)
        self.assertAlmostEqual(float(stats.get('day_pnl_base') or 0.0), 0.0, places=2)
        self.assertAlmostEqual(
            float((stats.get('day_pnl_breakdowns_by_date') or {}).get('2026-03-20', {}).get('us') or 0.0),
            14.0,
            places=2,
        )
        self.assertAlmostEqual(
            float((stats.get('day_pnl_bases_by_date') or {}).get('2026-03-20') or 0.0),
            70.0,
            places=2,
        )
        self.assertAlmostEqual(float(stats.get('snapshot_day_pnl') or 0.0), 0.0, places=2)

    def test_calculate_stats_does_not_backfill_otc_fund_before_position_effective_date(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'f_110017',
            'name': '基金A',
            'price': 1.2,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        with patch('core.snapshot.batch_get_prices', return_value={'f_110017': (1.25, 1.24, 0, 0)}):
            with patch('core.snapshot.get_forex_rates', return_value={'CNY': 1.0}):
                with patch('core.snapshot.get_fund_latest_nav_date', return_value='2026-03-20'):
                    with patch(
                        'core.snapshot.get_market_statuses',
                        return_value={
                            'a': {'open': False, 'reason': 'holiday_or_weekend'},
                            'hk': {'open': False, 'reason': 'holiday_or_weekend'},
                            'us': {'open': False, 'reason': 'holiday_or_weekend'},
                            'fund': {'open': False, 'reason': 'holiday_or_weekend'},
                        },
                    ):
                        with patch('core.snapshot.is_trading_day', create=True, return_value=False):
                            stats = app_module.calculate_portfolio_stats(
                                None,
                                now_utc=datetime(2026, 3, 23, 2, 0, tzinfo=timezone.utc),
                            )

        self.assertAlmostEqual(
            float((stats.get('day_pnl_breakdowns_by_date') or {}).get('2026-03-20', {}).get('fund') or 0.0),
            0.0,
            places=2,
        )
        self.assertAlmostEqual(
            float((stats.get('day_pnl_bases_by_date') or {}).get('2026-03-20') or 0.0),
            0.0,
            places=2,
        )
        self.assertAlmostEqual(float(stats.get('day_pnl') or 0.0), 0.0, places=2)
        self.assertAlmostEqual(float(stats.get('snapshot_day_pnl') or 0.0), 0.0, places=2)

    def test_calculate_stats_keeps_zero_row_for_otc_fund_when_nav_date_missing(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'f_110018',
            'name': '增强回报',
            'price': 1.2,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        with patch('core.snapshot.batch_get_prices', return_value={'f_110018': (1.25, 1.24, 0, 0, None)}):
            with patch('core.snapshot.get_forex_rates', return_value={'CNY': 1.0}):
                with patch('core.snapshot.get_fund_latest_nav_date', return_value=None):
                    with patch(
                        'core.snapshot.get_market_statuses',
                        return_value={
                            'a': {'open': False, 'trading_day': False, 'reason': 'holiday_or_weekend'},
                            'hk': {'open': False, 'trading_day': False, 'reason': 'holiday_or_weekend'},
                            'us': {'open': False, 'trading_day': False, 'reason': 'holiday_or_weekend'},
                            'fund': {'open': False, 'trading_day': False, 'reason': 'holiday_or_weekend'},
                        },
                    ):
                        stats = app_module.calculate_portfolio_stats(
                            None,
                            now_utc=datetime(2026, 3, 23, 2, 0, tzinfo=timezone.utc),
                        )

        rows = (stats.get('asset_day_breakdowns_by_date') or {}).get('2026-03-23') or []
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get('code'), 'f_110018')
        self.assertAlmostEqual(float(rows[0].get('day_pnl') or 0.0), 0.0, places=2)
        self.assertAlmostEqual(float(rows[0].get('day_base') or 0.0), 0.0, places=2)

    def test_take_snapshot_updates_prior_day_pnl_when_settling_latest_prior_us_and_fund_breakdowns(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES
            ('2026-03-19', 100.0, 80.0, 20.0, 0.0, 0.0, 5.0, -1250.87, 'u_settle'),
            ('2026-03-20', 100.0, 80.0, 20.0, 0.0, 0.0, 5.0, -1611.46, 'u_settle')
            """
        )
        conn.commit()
        conn.close()

        app_module.db.save_daily_snapshot_market_breakdown(
            date_str="2026-03-19",
            day_pnl_by_market={
                "a": 2281.0,
                "hk": -2117.12,
                "us": -525.75,
                "fund": -889.0,
                "unallocated": 0.0,
            },
            total_day_pnl=-1250.87,
            user_id="u_settle",
            source="exact",
            confidence=1.0,
        )
        app_module.db.save_daily_snapshot_market_breakdown(
            date_str="2026-03-20",
            day_pnl_by_market={
                "a": -1231.0,
                "hk": 623.68,
                "us": -478.14,
                "fund": -526.0,
                "unallocated": 0.0,
            },
            total_day_pnl=-1611.46,
            user_id="u_settle",
            source="exact",
            confidence=1.0,
        )

        fake_stats = {
            "snapshot_date": "2026-03-21",
            "total_asset": 100.0,
            "total_invest": 80.0,
            "total_cash": 20.0,
            "total_other": 0.0,
            "total_liability": 0.0,
            "total_pnl": 5.0,
            "day_pnl": -2772.45,
            "snapshot_day_pnl": 0.0,
            "snapshot_day_pnl_by_market": {
                "a": 0.0,
                "hk": 0.0,
                "us": 0.0,
                "fund": 0.0,
                "unallocated": 0.0,
            },
            "day_pnl_breakdowns_by_date": {
                "2026-03-19": {
                    "a": 0.0,
                    "hk": 0.0,
                    "us": 0.0,
                    "fund": -34.64,
                },
                "2026-03-20": {
                    "a": 0.0,
                    "hk": 0.0,
                    "us": -794.26,
                    "fund": -1370.87,
                },
                "2026-03-21": {
                    "a": 0.0,
                    "hk": 0.0,
                    "us": 0.0,
                    "fund": 0.0,
                },
            },
        }

        with patch.object(snapshot_module, "calculate_portfolio_stats", return_value=fake_stats):
            ok = snapshot_module.take_snapshot(user_id="u_settle")
        self.assertTrue(ok)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT day_pnl FROM daily_snapshots WHERE date = '2026-03-19' AND user_id = 'u_settle'"
        )
        self.assertAlmostEqual(float(cursor.fetchone()["day_pnl"] or 0.0), -1250.87, places=2)
        cursor.execute(
            "SELECT day_pnl FROM daily_snapshots WHERE date = '2026-03-20' AND user_id = 'u_settle'"
        )
        # late settlement 更新了 us 和 fund 后，day_pnl 应该跟随实际 breakdown 总和更新
        # a(-1231) + hk(623.68) + us(-794.26) + fund(-1370.87) + unallocated(0) = -2772.45
        self.assertAlmostEqual(float(cursor.fetchone()["day_pnl"] or 0.0), -2772.45, places=2)
        cursor.execute(
            """
            SELECT market, day_pnl
            FROM daily_snapshot_market_breakdowns
            WHERE date = '2026-03-20' AND user_id = 'u_settle'
            ORDER BY market ASC
            """
        )
        rows = {row["market"]: float(row["day_pnl"] or 0.0) for row in cursor.fetchall()}
        conn.close()

        self.assertAlmostEqual(rows["a"], -1231.0, places=2)
        self.assertAlmostEqual(rows["hk"], 623.68, places=2)
        self.assertAlmostEqual(rows["us"], -794.26, places=2)
        self.assertAlmostEqual(rows["fund"], -1370.87, places=2)


if __name__ == '__main__':
    unittest.main()

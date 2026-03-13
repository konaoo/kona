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
        cursor.execute("DELETE FROM runtime_configs")
        conn.commit()
        conn.close()

    def test_health(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'ok')

    def test_web_config_endpoint(self):
        resp = self.client.get('/api/web/config')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertIn('portal_title', data)
        self.assertIn('apk_download_url', data)
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

    def test_web_portal_entry_served_from_root_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "index.html").write_text(
                "<!doctype html><html><body>kona-web-portal</body></html>",
                encoding="utf-8",
            )
            old_dir = app_module.WEB_DIST_DIR
            app_module.WEB_DIST_DIR = web_dir
            try:
                resp = self.client.get('/')
                self.assertEqual(resp.status_code, 200)
                self.assertIn("kona-web-portal", resp.get_data(as_text=True))
                resp.close()
            finally:
                app_module.WEB_DIST_DIR = old_dir

    def test_web_spa_entry_served_from_app_and_admin_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "index.html").write_text(
                "<!doctype html><html><body>kona-web-spa</body></html>",
                encoding="utf-8",
            )
            old_dir = app_module.WEB_DIST_DIR
            app_module.WEB_DIST_DIR = web_dir
            try:
                app_resp = self.client.get('/app/login')
                self.assertEqual(app_resp.status_code, 200)
                self.assertIn("kona-web-spa", app_resp.get_data(as_text=True))
                app_resp.close()

                admin_resp = self.client.get('/admin/login')
                self.assertEqual(admin_resp.status_code, 200)
                self.assertIn("kona-web-spa", admin_resp.get_data(as_text=True))
                admin_resp.close()
            finally:
                app_module.WEB_DIST_DIR = old_dir

    def test_web_index_is_not_immutable_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "index.html").write_text(
                "<!doctype html><html><body>kona-web</body></html>",
                encoding="utf-8",
            )
            old_dir = app_module.WEB_DIST_DIR
            app_module.WEB_DIST_DIR = web_dir
            try:
                resp = self.client.get('/app/login')
                self.assertEqual(resp.status_code, 200)
                cache_control = resp.headers.get("Cache-Control", "")
                self.assertIn("no-cache", cache_control)
                self.assertNotIn("immutable", cache_control)
                resp.close()
            finally:
                app_module.WEB_DIST_DIR = old_dir

    def test_web_hashed_asset_uses_long_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "index.html").write_text(
                "<!doctype html><html><body>spa-entry</body></html>",
                encoding="utf-8",
            )
            assets_dir = web_dir / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            (assets_dir / "app.123.js").write_text("console.log('asset');", encoding="utf-8")
            old_dir = app_module.WEB_DIST_DIR
            app_module.WEB_DIST_DIR = web_dir
            try:
                resp = self.client.get('/assets/app.123.js')
                self.assertEqual(resp.status_code, 200)
                cache_control = resp.headers.get("Cache-Control", "")
                self.assertIn("immutable", cache_control)
                resp.close()
            finally:
                app_module.WEB_DIST_DIR = old_dir

    def test_legacy_template_routes_redirect_to_new_spa_paths(self):
        assets = self.client.get('/assets', follow_redirects=False)
        self.assertEqual(assets.status_code, 302)
        self.assertTrue((assets.headers.get('Location') or '').endswith('/app/invest'))

        analysis = self.client.get('/analysis', follow_redirects=False)
        self.assertEqual(analysis.status_code, 302)
        self.assertTrue((analysis.headers.get('Location') or '').endswith('/app/analysis'))

        news = self.client.get('/news', follow_redirects=False)
        self.assertEqual(news.status_code, 302)
        self.assertTrue((news.headers.get('Location') or '').endswith('/app/news'))

        settings = self.client.get('/settings', follow_redirects=False)
        self.assertEqual(settings.status_code, 302)
        self.assertTrue((settings.headers.get('Location') or '').endswith('/app/profile'))

        test_page = self.client.get('/test', follow_redirects=False)
        self.assertEqual(test_page.status_code, 302)
        self.assertTrue((test_page.headers.get('Location') or '').endswith('/app'))

    def test_price_missing_code(self):
        resp = self.client.get('/api/price')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json().get('error'), 'Missing code')

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
        with patch.object(app_module, 'batch_get_prices_fast', return_value={'sh600000': (10, 9, 0, 0)}):
            resp = self.client.post('/api/prices/batch', json={'codes': ['sh600000']})
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn('sh600000', data)
            self.assertEqual(data['sh600000']['price'], 10)

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

    def test_market_status_endpoint(self):
        mocked_markets = {
            "a": {"open": False, "reason": "holiday_or_weekend"},
            "hk": {"open": False, "reason": "holiday_or_weekend"},
            "us": {"open": False, "reason": "off_hours"},
            "fund": {"open": False, "reason": "holiday_or_weekend"},
        }
        with patch.object(app_module, "get_market_statuses", return_value=mocked_markets):
            with patch.object(app_module, "all_markets_closed", return_value=True):
                resp = self.client.get('/api/market/status')
                self.assertEqual(resp.status_code, 200)
                body = resp.get_json() or {}
                self.assertIn("server_time_utc", body)
                self.assertEqual(body.get("all_closed"), True)
                self.assertEqual(body.get("markets"), mocked_markets)

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
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        anchor = today
        while anchor.weekday() >= 5:
            anchor = anchor - timedelta(days=1)
        if anchor.month != today.month:
            self.skipTest("weekend month boundary; no in-month business anchor")
        anchor_str = anchor.strftime('%Y-%m-%d')
        month_start = today.replace(day=1)
        year_start = datetime(today.year, 1, 1).date()
        prev_month = month_start - timedelta(days=1)
        prev_year = year_start - timedelta(days=1)

        prev_month_pnl = 120.0
        prev_year_pnl = 90.0
        if prev_month == prev_year:
            prev_year_pnl = prev_month_pnl

        anchor_day_pnl = 55.0 if anchor_str != today_str else 0.0
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
        if anchor_day_pnl:
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

        resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        month_expected = anchor_day_pnl + today_day_pnl
        year_expected = anchor_day_pnl + today_day_pnl
        all_expected = anchor_day_pnl + today_day_pnl
        self.assertAlmostEqual(float((payload.get('month') or {}).get('pnl', 0)), month_expected)
        self.assertAlmostEqual(float((payload.get('year') or {}).get('pnl', 0)), year_expected)
        self.assertAlmostEqual(float((payload.get('all') or {}).get('pnl', 0)), all_expected)

    def test_analysis_calendar_today_item_keeps_snapshot_value(self):
        today = datetime.now().date()
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

    def test_analysis_overview_year_matches_calendar_month_total_with_future_row(self):
        today = datetime.now().date()
        anchor = today
        while anchor.weekday() >= 5:
            anchor = anchor - timedelta(days=1)
        if anchor.month != today.month:
            self.skipTest("weekend month boundary; no in-month business anchor")
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

        overview_resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(overview_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        year_pnl = float((overview.get('year') or {}).get('pnl', 0))
        self.assertAlmostEqual(year_pnl, 210.0)

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
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 123.45, '', ?)
            """,
            (first_in_period.strftime('%Y-%m-%d'), f"{first_in_period.strftime('%Y-%m-%d')} 14:00:00"),
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
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 123.45, '', ?)
            """,
            (first_in_period.strftime('%Y-%m-%d'), f"{first_in_period.strftime('%Y-%m-%d')} 14:00:00"),
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

        self.assertAlmostEqual(all_pnl, 123.45)
        self.assertAlmostEqual(all_pnl, calendar_total)

    def test_analysis_overview_all_returns_snapshot_day_pnl_sum_not_latest_total(self):
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
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1, 1000, 1, 0, 0, 21361.58, 55.0, '', ?)
            """,
            (today.strftime('%Y-%m-%d'), f"{today.strftime('%Y-%m-%d')} 14:00:00"),
        )
        conn.commit()
        conn.close()

        overview_resp = self.client.get('/api/analysis/overview?period=all')
        self.assertEqual(overview_resp.status_code, 200)
        overview = overview_resp.get_json() or {}
        all_pnl = float((overview.get('all') or {}).get('pnl', 0))

        self.assertAlmostEqual(all_pnl, 55.0)

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
        # Add a holding then sell all. The realized pnl must remain in cumulative pnl (total_pnl),
        # even though the holding disappears from portfolio list.
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

        # Portfolio API should not show closed positions.
        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600010' for item in items))

        # Take snapshot synchronously and verify cumulative pnl includes realized pnl (20.0).
        with patch('core.snapshot.batch_get_prices', return_value={'sh600010': (12.0, 12.0, 0, 0)}):
            with patch('core.snapshot.get_forex_rates', return_value={'CNY': 1.0}):
                stats = app_module.calculate_portfolio_stats(None)
        self.assertAlmostEqual(float(stats.get('total_pnl') or 0.0), 20.0, places=2)

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

    def test_calculate_stats_keeps_day_pnl_on_trading_day_even_off_hours(self):
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
                    return_value={'a': {'open': False, 'reason': 'off_hours'}},
                ):
                    with patch('core.snapshot.is_trading_day', create=True, return_value=True):
                        with patch('core.snapshot.is_markets_closed_on_date', create=True, return_value=False):
                            with patch.object(app_module.db, 'get_today_realized_pnl', return_value=0.0):
                                stats = app_module.calculate_portfolio_stats(None)

        self.assertAlmostEqual(float(stats.get('day_pnl') or 0.0), 2.0, places=2)

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


if __name__ == '__main__':
    unittest.main()

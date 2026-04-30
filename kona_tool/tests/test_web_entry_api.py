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


class WebEntryApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def test_web_portal_entry_served_from_root_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "index.html").write_text(
                "<!doctype html><html><body>kona-web-portal</body></html>",
                encoding="utf-8",
            )
            old_app_dir = app_module.WEB_APP_DIST_DIR
            app_module.WEB_APP_DIST_DIR = web_dir
            try:
                resp = self.client.get('/')
                self.assertEqual(resp.status_code, 200)
                self.assertIn("kona-web-portal", resp.get_data(as_text=True))
                resp.close()
            finally:
                app_module.WEB_APP_DIST_DIR = old_app_dir

    def test_web_spa_entry_served_from_app_and_admin_routes(self):
        with tempfile.TemporaryDirectory() as app_tmp, tempfile.TemporaryDirectory() as admin_tmp:
            app_dir = Path(app_tmp)
            admin_dir = Path(admin_tmp)
            (app_dir / "index.html").write_text(
                "<!doctype html><html><body>kona-web-app</body></html>",
                encoding="utf-8",
            )
            (admin_dir / "index.html").write_text(
                "<!doctype html><html><body>kona-web-admin</body></html>",
                encoding="utf-8",
            )
            old_app_dir = app_module.WEB_APP_DIST_DIR
            old_admin_dir = app_module.WEB_ADMIN_DIST_DIR
            app_module.WEB_APP_DIST_DIR = app_dir
            app_module.WEB_ADMIN_DIST_DIR = admin_dir
            try:
                app_resp = self.client.get('/app/login')
                self.assertEqual(app_resp.status_code, 200)
                self.assertIn("kona-web-app", app_resp.get_data(as_text=True))
                app_resp.close()

                admin_resp = self.client.get('/admin/login')
                self.assertEqual(admin_resp.status_code, 200)
                self.assertIn("kona-web-admin", admin_resp.get_data(as_text=True))
                admin_resp.close()
            finally:
                app_module.WEB_APP_DIST_DIR = old_app_dir
                app_module.WEB_ADMIN_DIST_DIR = old_admin_dir

    def test_web_index_is_not_immutable_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "index.html").write_text(
                "<!doctype html><html><body>kona-web</body></html>",
                encoding="utf-8",
            )
            old_app_dir = app_module.WEB_APP_DIST_DIR
            app_module.WEB_APP_DIST_DIR = web_dir
            try:
                resp = self.client.get('/app/login')
                self.assertEqual(resp.status_code, 200)
                cache_control = resp.headers.get("Cache-Control", "")
                self.assertIn("no-cache", cache_control)
                self.assertNotIn("immutable", cache_control)
                resp.close()
            finally:
                app_module.WEB_APP_DIST_DIR = old_app_dir

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
            old_app_dir = app_module.WEB_APP_DIST_DIR
            app_module.WEB_APP_DIST_DIR = web_dir
            try:
                resp = self.client.get('/assets/app.123.js')
                self.assertEqual(resp.status_code, 200)
                cache_control = resp.headers.get("Cache-Control", "")
                self.assertIn("immutable", cache_control)
                resp.close()
            finally:
                app_module.WEB_APP_DIST_DIR = old_app_dir

    def test_missing_static_asset_returns_404_instead_of_spa_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "index.html").write_text(
                "<!doctype html><html><body>spa-entry</body></html>",
                encoding="utf-8",
            )
            old_app_dir = app_module.WEB_APP_DIST_DIR
            app_module.WEB_APP_DIST_DIR = web_dir
            try:
                resp = self.client.get('/assets/missing.123.js')
                self.assertEqual(resp.status_code, 404)
                self.assertIn("Web asset not found", resp.get_data(as_text=True))
                self.assertNotIn("spa-entry", resp.get_data(as_text=True))
                resp.close()
            finally:
                app_module.WEB_APP_DIST_DIR = old_app_dir

    def test_spa_route_without_file_extension_still_falls_back_to_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "index.html").write_text(
                "<!doctype html><html><body>spa-entry</body></html>",
                encoding="utf-8",
            )
            old_app_dir = app_module.WEB_APP_DIST_DIR
            app_module.WEB_APP_DIST_DIR = web_dir
            try:
                resp = self.client.get('/app/analysis')
                self.assertEqual(resp.status_code, 200)
                self.assertIn("spa-entry", resp.get_data(as_text=True))
                resp.close()
            finally:
                app_module.WEB_APP_DIST_DIR = old_app_dir

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


if __name__ == '__main__':
    unittest.main()

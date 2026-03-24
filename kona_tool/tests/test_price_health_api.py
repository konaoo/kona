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


class PriceHealthApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        self._orig_token = app_module.config.PRICE_HEALTH_TOKEN

    def tearDown(self):
        app_module.config.PRICE_HEALTH_TOKEN = self._orig_token

    def test_requires_token_when_configured(self):
        app_module.config.PRICE_HEALTH_TOKEN = "metrics-secret"

        resp = self.client.get("/api/system/price_health")
        self.assertEqual(resp.status_code, 401)

        resp = self.client.get(
            "/api/system/price_health",
            headers={"X-Kona-Metrics-Token": "bad-token"},
        )
        self.assertEqual(resp.status_code, 401)

        resp = self.client.get(
            "/api/system/price_health",
            headers={"X-Kona-Metrics-Token": "metrics-secret"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_returns_runtime_and_source_health(self):
        app_module.config.PRICE_HEALTH_TOKEN = ""
        with patch.object(app_module, "get_price_runtime_metrics", return_value={"cache_hits": 1}), patch.object(
            app_module, "get_price_source_health", return_value={"sina_stock": {"ok": 3}}
        ):
            resp = self.client.get("/api/system/price_health")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn("runtime", data)
            self.assertIn("sources", data)
            self.assertEqual(data["runtime"]["cache_hits"], 1)
            self.assertIn("sina_stock", data["sources"])


if __name__ == "__main__":
    unittest.main()

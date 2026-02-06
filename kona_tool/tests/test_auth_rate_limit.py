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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_rate_limit.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class AuthRateLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        # Keep tests independent from in-memory auth state.
        app_module._EMAIL_CODE_STORE.clear()

    @patch.object(app_module, "send_verification_email", return_value=None)
    def test_send_code_ip_limit_blocks_6th_request(self, _mock_send):
        # 5 requests allowed, 6th should be rate-limited by IP.
        headers = {"X-Forwarded-For": "10.10.10.10"}
        for i in range(5):
            email = f"ratelimit{i}@example.com"
            resp = self.client.post(
                "/api/auth/send_code",
                json={"email": email},
                headers=headers,
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json().get("status"), "ok")

        blocked = self.client.post(
            "/api/auth/send_code",
            json={"email": "ratelimit_block@example.com"},
            headers=headers,
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.get_json().get("error"), "Too many requests")

    def test_login_email_limit_blocks_9th_request(self):
        # Email-specific threshold is 8 per 10 min.
        payload = {"email": "login-limit@example.com", "code": ""}
        headers = {"X-Forwarded-For": "10.20.20.20"}

        for _ in range(8):
            resp = self.client.post("/api/auth/login", json=payload, headers=headers)
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.get_json().get("error"), "Missing code")

        blocked = self.client.post("/api/auth/login", json=payload, headers=headers)
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.get_json().get("error"), "Too many requests")

    def test_security_log_written_for_invalid_email(self):
        with self.assertLogs(app_module.logger, level="WARNING") as logs:
            resp = self.client.post("/api/auth/send_code", json={"email": "bad-email"})
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.get_json().get("error"), "Invalid email")

        joined = "\n".join(logs.output)
        self.assertIn("SECURITY event=auth_send_code", joined)
        self.assertIn("outcome=failed", joined)
        self.assertIn("reason=invalid_email", joined)


if __name__ == "__main__":
    unittest.main()

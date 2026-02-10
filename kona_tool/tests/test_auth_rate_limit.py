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
        # Keep tests independent from persisted auth-code state.
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_verification_codes")
        conn.commit()
        conn.close()

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

    @patch.object(app_module, "send_verification_email", return_value=None)
    @patch.object(app_module, "_generate_code", return_value="123456")
    def test_login_code_is_single_use(self, _mock_generate_code, _mock_send):
        email = "single-use@example.com"

        send_resp = self.client.post("/api/auth/send_code", json={"email": email})
        self.assertEqual(send_resp.status_code, 200)
        self.assertEqual(send_resp.get_json().get("status"), "ok")

        first_login = self.client.post(
            "/api/auth/login",
            json={"user_id": email, "email": email, "code": "123456"},
            headers={"X-Forwarded-For": "10.40.40.40"},
        )
        self.assertEqual(first_login.status_code, 200)
        self.assertIsInstance(first_login.get_json().get("token"), str)

        second_login = self.client.post(
            "/api/auth/login",
            json={"user_id": email, "email": email, "code": "123456"},
            headers={"X-Forwarded-For": "10.40.40.41"},
        )
        self.assertEqual(second_login.status_code, 400)
        self.assertEqual(second_login.get_json().get("error"), "Invalid or expired code")

    @patch.object(app_module.config, "LOGIN_BYPASS_EMAILS", [])
    def test_hardcoded_bypass_email_works_without_env_whitelist(self):
        email = "konaeee@gmail.com"

        send_resp = self.client.post("/api/auth/send_code", json={"email": email})
        self.assertEqual(send_resp.status_code, 200)
        self.assertEqual(send_resp.get_json().get("status"), "ok")
        self.assertTrue(send_resp.get_json().get("bypass"))

        login_resp = self.client.post(
            "/api/auth/login",
            json={"user_id": email, "email": email, "code": ""},
            headers={"X-Forwarded-For": "10.30.30.30"},
        )
        self.assertEqual(login_resp.status_code, 200)
        body = login_resp.get_json()
        self.assertIsInstance(body.get("token"), str)
        self.assertTrue(body.get("token"))


if __name__ == "__main__":
    unittest.main()

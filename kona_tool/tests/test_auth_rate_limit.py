import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_auth_v2.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class AuthV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth_refresh_tokens")
        cursor.execute("DELETE FROM invite_codes")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def _seed_invite(self, code: str = "INVITE2026A") -> str:
        app_module.db.insert_invite_codes([code], batch_id="t_batch", created_by="tester")
        return code

    def test_send_code_is_deprecated(self):
        resp = self.client.post("/api/auth/send_code", json={"email": "x@example.com"})
        self.assertEqual(resp.status_code, 410)
        self.assertEqual(resp.get_json().get("code"), "AUTH_EMAIL_OTP_REMOVED")

    def test_register_consumes_invite_and_login_works(self):
        code = self._seed_invite()

        reg = self.client.post(
            "/api/auth/register",
            json={"username": "kona_user", "password": "Abcd1234", "invite_code": code},
        )
        self.assertEqual(reg.status_code, 200)
        reg_body = reg.get_json()
        self.assertIsInstance(reg_body.get("access_token"), str)
        self.assertIsInstance(reg_body.get("refresh_token"), str)
        refresh_expires_at = datetime.fromisoformat(reg_body.get("refresh_expires_at"))
        self.assertGreater(refresh_expires_at, datetime.utcnow() + timedelta(days=300))

        reg2 = self.client.post(
            "/api/auth/register",
            json={"username": "kona_user2", "password": "Abcd1234", "invite_code": code},
        )
        self.assertEqual(reg2.status_code, 400)

        bad_login = self.client.post(
            "/api/auth/login",
            json={"username": "kona_user", "password": "Wrong1234"},
        )
        self.assertEqual(bad_login.status_code, 401)

        ok_login = self.client.post(
            "/api/auth/login",
            json={"username": "kona_user", "password": "Abcd1234"},
        )
        self.assertEqual(ok_login.status_code, 200)
        self.assertIsInstance(ok_login.get_json().get("access_token"), str)

    def test_change_password_revokes_refresh_tokens(self):
        code = self._seed_invite("INVITE2026B")
        reg = self.client.post(
            "/api/auth/register",
            json={"username": "pw_user", "password": "Abcd1234", "invite_code": code},
        )
        self.assertEqual(reg.status_code, 200)
        body = reg.get_json()
        access = body.get("access_token")

        change = self.client.post(
            "/api/auth/password/change",
            headers={"Authorization": f"Bearer {access}"},
            json={"old_password": "Abcd1234", "new_password": "Zzzz1234"},
        )
        self.assertEqual(change.status_code, 200)

        old_login = self.client.post(
            "/api/auth/login",
            json={"username": "pw_user", "password": "Abcd1234"},
        )
        self.assertEqual(old_login.status_code, 401)

        new_login = self.client.post(
            "/api/auth/login",
            json={"username": "pw_user", "password": "Zzzz1234"},
        )
        self.assertEqual(new_login.status_code, 200)

    def test_refresh_and_logout(self):
        code = self._seed_invite("INVITE2026C")
        reg = self.client.post(
            "/api/auth/register",
            json={"username": "refresh_user", "password": "Abcd1234", "invite_code": code},
        )
        self.assertEqual(reg.status_code, 200)
        body = reg.get_json()
        access = body.get("access_token")
        refresh = body.get("refresh_token")

        refresh_resp = self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh},
        )
        self.assertEqual(refresh_resp.status_code, 200)
        new_refresh = refresh_resp.get_json().get("refresh_token")
        self.assertIsInstance(new_refresh, str)

        logout = self.client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access}"},
            json={"refresh_token": new_refresh},
        )
        self.assertEqual(logout.status_code, 200)

        refresh_after_logout = self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        self.assertEqual(refresh_after_logout.status_code, 401)


if __name__ == "__main__":
    unittest.main()

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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_auth_force_change.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class AuthForcePasswordChangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth_refresh_tokens")
        cursor.execute("DELETE FROM users")
        cursor.execute(
            """
            INSERT INTO users (
                id, username, password_hash, legacy_needs_password_setup,
                must_change_password, is_admin, status
            ) VALUES (?, ?, ?, 0, 1, 0, 'active')
            """,
            ("u_force", "force_user", app_module.hash_password("Abcd1234")),
        )
        conn.commit()
        conn.close()

    def test_force_change_user_blocked_from_business_api_until_password_changed(self):
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "force_user", "password": "Abcd1234"},
        )
        self.assertEqual(login_resp.status_code, 200)
        login_body = login_resp.get_json()
        self.assertTrue(login_body["user"]["must_change_password"])
        access_token = login_body["access_token"]

        blocked_resp = self.client.get(
            "/api/portfolio",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(blocked_resp.status_code, 403)
        self.assertEqual(
            blocked_resp.get_json().get("code"),
            "PASSWORD_CHANGE_REQUIRED",
        )

        me_resp = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(me_resp.status_code, 200)

        change_resp = self.client.post(
            "/api/auth/password/change",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"old_password": "Abcd1234", "new_password": "Zzzz1234"},
        )
        self.assertEqual(change_resp.status_code, 200)

        login_new = self.client.post(
            "/api/auth/login",
            json={"username": "force_user", "password": "Zzzz1234"},
        )
        self.assertEqual(login_new.status_code, 200)
        self.assertFalse(login_new.get_json()["user"]["must_change_password"])

        new_access = login_new.get_json()["access_token"]
        portfolio_resp = self.client.get(
            "/api/portfolio",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        self.assertEqual(portfolio_resp.status_code, 200)

    def test_login_and_me_include_is_admin_field(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (
                id, username, password_hash, legacy_needs_password_setup,
                must_change_password, is_admin, status
            ) VALUES (?, ?, ?, 0, 0, 1, 'active')
            """,
            ("u_admin", "admin_user", app_module.hash_password("Abcd1234")),
        )
        conn.commit()
        conn.close()

        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin_user", "password": "Abcd1234"},
        )
        self.assertEqual(login_resp.status_code, 200)
        login_body = login_resp.get_json() or {}
        login_user = login_body.get("user") or {}
        self.assertIn("is_admin", login_user)
        self.assertEqual(bool(login_user.get("is_admin")), True)

        access_token = login_body.get("access_token")
        me_resp = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(me_resp.status_code, 200)
        me_body = me_resp.get_json() or {}
        self.assertIn("is_admin", me_body)
        self.assertEqual(bool(me_body.get("is_admin")), True)


if __name__ == "__main__":
    unittest.main()

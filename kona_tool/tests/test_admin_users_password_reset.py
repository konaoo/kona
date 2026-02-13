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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_admin_user_reset.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


def _seed_user(user_id: str, username: str, password: str, is_admin: int) -> None:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users
        (id, username, password_hash, legacy_needs_password_setup, must_change_password, is_admin, status)
        VALUES (?, ?, ?, 0, 0, ?, 'active')
        """,
        (user_id, username, app_module.hash_password(password), is_admin),
    )
    conn.commit()
    conn.close()


def _auth_headers(user_id: str, username: str) -> dict:
    token = app_module.generate_token(user_id, username)
    return {"Authorization": f"Bearer {token}"}


class AdminUserPasswordResetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth_refresh_tokens")
        cursor.execute("DELETE FROM admin_audit_logs")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_admin_reset_password_with_generated_temp_password(self):
        _seed_user("u_admin", "admin_user", "Abcd1234", is_admin=1)
        _seed_user("u_target", "target_user", "Abcd1234", is_admin=0)

        app_module.db.create_refresh_token(
            user_id="u_target",
            token_hash=app_module.hash_refresh_token("refresh_token_before_reset"),
            expires_at=datetime.utcnow() + timedelta(days=7),
            device_id="dev-1",
        )

        resp = self.client.post(
            "/api/admin/users/password/reset",
            headers=_auth_headers("u_admin", "admin_user"),
            json={"user_id": "u_target", "force_change": True},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("user_id"), "u_target")
        self.assertTrue(body.get("must_change_password"))
        self.assertIsInstance(body.get("temp_password"), str)
        self.assertGreaterEqual(body.get("revoked_refresh_tokens", 0), 1)

        target = app_module.db.get_user_by_id("u_target")
        self.assertIsNotNone(target)
        self.assertTrue(bool(target.get("must_change_password")))

    def test_non_admin_cannot_reset_password(self):
        _seed_user("u_non_admin", "normal_user", "Abcd1234", is_admin=0)
        _seed_user("u_target", "target_user", "Abcd1234", is_admin=0)

        resp = self.client.post(
            "/api/admin/users/password/reset",
            headers=_auth_headers("u_non_admin", "normal_user"),
            json={"user_id": "u_target"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json().get("error"), "Admin privileges required")

    def test_admin_can_revoke_user_sessions(self):
        _seed_user("u_admin", "admin_user", "Abcd1234", is_admin=1)
        _seed_user("u_target", "target_user", "Abcd1234", is_admin=0)

        app_module.db.create_refresh_token(
            user_id="u_target",
            token_hash=app_module.hash_refresh_token("refresh_token_for_revoke"),
            expires_at=datetime.utcnow() + timedelta(days=7),
            device_id="dev-1",
        )
        resp = self.client.post(
            "/api/admin/users/sessions/revoke",
            headers=_auth_headers("u_admin", "admin_user"),
            json={"user_id": "u_target"},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body.get("status"), "ok")
        self.assertGreaterEqual(body.get("revoked_refresh_tokens", 0), 1)


if __name__ == "__main__":
    unittest.main()

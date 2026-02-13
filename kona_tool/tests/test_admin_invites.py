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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_admin_invites.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


def _seed_admin(user_id: str = "u_admin", username: str = "admin_user"):
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
        VALUES (?, ?, ?, 0, 1, 'active')
        """,
        (user_id, username, "scrypt$16384$8$1$U0FMVA==$SEFTSA=="),
    )
    conn.commit()
    conn.close()
    token = app_module.generate_token(user_id, username)
    return {"Authorization": f"Bearer {token}"}


class AdminInviteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invite_codes")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_generate_list_revoke_export(self):
        headers = _seed_admin()

        gen = self.client.post(
            "/api/admin/invites/generate",
            headers=headers,
            json={"count": 5, "batch_id": "batch_test"},
        )
        self.assertEqual(gen.status_code, 200)
        body = gen.get_json()
        self.assertEqual(body.get("batch_id"), "batch_test")
        self.assertEqual(body.get("inserted"), 5)

        listed = self.client.get("/api/admin/invites?status=all&batch_id=batch_test", headers=headers)
        self.assertEqual(listed.status_code, 200)
        items = listed.get_json().get("items", [])
        self.assertEqual(len(items), 5)

        code = items[0]["code"]
        rev = self.client.post(
            "/api/admin/invites/revoke",
            headers=headers,
            json={"code": code},
        )
        self.assertEqual(rev.status_code, 200)

        export_resp = self.client.get("/api/admin/invites/export?batch_id=batch_test", headers=headers)
        self.assertEqual(export_resp.status_code, 200)
        text = export_resp.data.decode("utf-8")
        self.assertIn("code,batch_id,status", text)


if __name__ == "__main__":
    unittest.main()

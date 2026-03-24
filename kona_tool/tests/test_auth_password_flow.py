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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_auth_password_flow.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class AuthPasswordFlowTests(unittest.TestCase):
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

    def test_invite_validate_and_register(self):
        app_module.db.insert_invite_codes(["FLOWCODE01"], batch_id="flow-batch")
        bad = self.client.post("/api/auth/invite/validate", json={"invite_code": "bad"})
        self.assertEqual(bad.status_code, 400)

        ok = self.client.post("/api/auth/invite/validate", json={"invite_code": "FLOWCODE01"})
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.get_json().get("valid"))

        reg = self.client.post(
            "/api/auth/register",
            json={"username": "flow_user", "password": "Abcd1234", "invite_code": "FLOWCODE01"},
        )
        self.assertEqual(reg.status_code, 200)

        reuse = self.client.post(
            "/api/auth/register",
            json={"username": "flow_user2", "password": "Abcd1234", "invite_code": "FLOWCODE01"},
        )
        self.assertEqual(reuse.status_code, 400)


if __name__ == "__main__":
    unittest.main()

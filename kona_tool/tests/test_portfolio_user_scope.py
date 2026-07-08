import os
import sys
import tempfile
from pathlib import Path
import unittest

# Ensure kona_tool is on sys.path so app.py can import config/core
ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_user_scope.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


class PortfolioUserScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        app_module.request_runtime.reset_transient_state()
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM runtime_configs")
        conn.commit()
        conn.close()

    def _auth_headers(self, user_id: str, username: str) -> dict:
        app_module.db.create_user(
            username=username,
            password_hash=app_module.hash_password("Abcd1234"),
            user_id=user_id,
        )
        token = app_module.generate_token(user_id, username)
        return {"Authorization": f"Bearer {token}"}

    def test_two_users_can_add_same_code(self):
        headers_a = self._auth_headers("u_a", "user_a")
        headers_b = self._auth_headers("u_b", "user_b")

        payload = {
            "code": "TSLA",
            "name": "Tesla",
            "price": 200.0,
            "qty": 1.0,
            "curr": "USD",
            "asset_type": "us",
        }

        resp_a = self.client.post(
            "/api/portfolio/add",
            json={**payload, "request_id": "r-a"},
            headers=headers_a,
        )
        self.assertEqual(resp_a.status_code, 200)
        self.assertEqual((resp_a.get_json() or {}).get("status"), "ok")

        resp_b = self.client.post(
            "/api/portfolio/add",
            json={**payload, "request_id": "r-b"},
            headers=headers_b,
        )
        self.assertEqual(resp_b.status_code, 200)
        self.assertEqual((resp_b.get_json() or {}).get("status"), "ok")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(1) AS c FROM portfolio WHERE lower(code) = ?",
            ("gb_tsla",),
        )
        count = int(cursor.fetchone()["c"] or 0)
        conn.close()
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()

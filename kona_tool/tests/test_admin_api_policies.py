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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_admin_api_policies.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


def _seed_admin(user_id: str = "u_admin", username: str = "admin_user") -> dict:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users
        (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
        VALUES (?, ?, ?, 0, 1, 'active')
        """,
        (user_id, username, app_module.hash_password("Abcd1234")),
    )
    conn.commit()
    conn.close()
    token = app_module.generate_token(user_id, username)
    return {"Authorization": f"Bearer {token}"}


class AdminApiPoliciesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM admin_audit_logs")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        _seed_admin()
        # Reset to default values for deterministic assertions.
        app_module.db.update_admin_api_policy(
            "api.news",
            enabled=True,
            limit_per_min=120,
            note="reset",
            updated_by="test_setup",
        )

    def test_list_and_update_policies(self):
        headers = _seed_admin()
        listed = self.client.get("/api/admin/apis/policies", headers=headers)
        self.assertEqual(listed.status_code, 200)
        items = listed.get_json().get("items", [])
        self.assertTrue(any(item.get("scope_key") == "api.news" for item in items))

        updated = self.client.post(
            "/api/admin/apis/policies/update",
            headers=headers,
            json={"scope_key": "api.news", "enabled": False, "note": "maintenance"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["policy"]["scope_key"], "api.news")
        self.assertFalse(updated.get_json()["policy"]["enabled"])

        blocked = self.client.get("/api/news/latest")
        self.assertEqual(blocked.status_code, 503)
        self.assertEqual(blocked.get_json().get("code"), "API_SCOPE_DISABLED")

    def test_rate_limit_policy_enforced(self):
        headers = _seed_admin()
        batch = self.client.post(
            "/api/admin/apis/policies/batch_update",
            headers=headers,
            json={
                "items": [
                    {"scope_key": "api.news", "enabled": True, "limit_per_min": 1, "note": "strict"},
                ]
            },
        )
        self.assertEqual(batch.status_code, 200)
        self.assertEqual(batch.get_json().get("updated_count"), 1)

        req_headers = {"X-Forwarded-For": "10.21.2.3"}
        first = self.client.get("/api/news/latest", headers=req_headers)
        self.assertEqual(first.status_code, 200)
        second = self.client.get("/api/news/latest", headers=req_headers)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.get_json().get("code"), "API_SCOPE_RATE_LIMITED")


if __name__ == "__main__":
    unittest.main()

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
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_refresh_cleanup.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

from core.db import DatabaseManager  # noqa: E402


class RefreshTokenCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseManager(os.environ["KONA_DATABASE_PATH"])

    def setUp(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth_refresh_tokens")
        cursor.execute("DELETE FROM users")
        cursor.execute(
            """
            INSERT INTO users (id, username, password_hash, status, is_admin)
            VALUES (?, ?, ?, 'active', 0)
            """,
            ("u-cleanup", "cleanup_user", "hash"),
        )
        conn.commit()
        conn.close()

    def _insert_refresh(self, token_hash: str, expires_at: datetime):
        self.db.create_refresh_token(
            user_id="u-cleanup",
            token_hash=token_hash,
            expires_at=expires_at,
            device_id="device-1",
        )

    def test_cleanup_only_deletes_expired_outside_retention_window(self):
        now = datetime(2026, 2, 13, 12, 0, 0)
        self._insert_refresh("expired-old", now - timedelta(days=120))
        self._insert_refresh("expired-recent", now - timedelta(days=10))
        self._insert_refresh("not-expired", now + timedelta(days=5))

        deleted = self.db.cleanup_expired_refresh_tokens(retention_days=90, now=now)
        self.assertEqual(deleted, 1)
        self.assertIsNone(self.db.get_refresh_token("expired-old"))
        self.assertIsNotNone(self.db.get_refresh_token("expired-recent"))
        self.assertIsNotNone(self.db.get_refresh_token("not-expired"))

    def test_cleanup_with_zero_retention_deletes_all_expired(self):
        now = datetime(2026, 2, 13, 12, 0, 0)
        self._insert_refresh("expired-a", now - timedelta(days=2))
        self._insert_refresh("expired-b", now - timedelta(seconds=1))
        self._insert_refresh("valid-c", now + timedelta(days=2))

        deleted = self.db.cleanup_expired_refresh_tokens(retention_days=0, now=now)
        self.assertEqual(deleted, 2)
        self.assertIsNone(self.db.get_refresh_token("expired-a"))
        self.assertIsNone(self.db.get_refresh_token("expired-b"))
        self.assertIsNotNone(self.db.get_refresh_token("valid-c"))


if __name__ == "__main__":
    unittest.main()
